from flask import Flask, jsonify, render_template, request, send_file
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import io
import time
import logging
from datetime import datetime
from functools import wraps

# Helper to sanitize SQL string values
def sanitize_sql(value):
    """Sanitize a string for safe use in SQL queries"""
    if value is None:
        return ''
    return str(value).replace("'", "''")

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Initialize Databricks SDK client
w = WorkspaceClient()

# Get available SQL warehouse
def get_warehouse_id():
    """Get the first available SQL warehouse"""
    try:
        warehouses = list(w.warehouses.list())
        if warehouses:
            return warehouses[0].id
        return None
    except Exception as e:
        print(f"Error getting warehouse: {e}")
        return None

WAREHOUSE_ID = get_warehouse_id()

def execute_sql(query):
    """Execute SQL query and return results"""
    try:
        if not WAREHOUSE_ID:
            return {'success': False, 'error': 'No SQL warehouse available'}
        
        statement = w.statement_execution.execute_statement(
            statement=query,
            warehouse_id=WAREHOUSE_ID
        )
        
        # Wait for completion
        while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
            time.sleep(0.1)
            statement = w.statement_execution.get_statement(statement.statement_id)
        
        if statement.status.state == StatementState.SUCCEEDED:
            if statement.result and statement.result.data_array:
                columns = [col.name for col in statement.manifest.schema.columns]
                rows = []
                for row in statement.result.data_array:
                    rows.append(dict(zip(columns, row)))
                return {'success': True, 'data': rows}
            return {'success': True, 'data': []}
        else:
            return {'success': False, 'error': statement.status.error.message if statement.status.error else 'Query failed'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Helper functions
def handle_errors(f):
    """Decorator to handle errors consistently across all routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logging.exception(f"Error in {f.__name__}")
            return jsonify({'success': False, 'error': str(e)}), 500
    return decorated_function

def get_pagination_params():
    """Extract pagination parameters from request"""
    return {
        'limit': int(request.args.get('limit', 15)),
        'offset': int(request.args.get('offset', 0))
    }

def get_search_param():
    """Extract and sanitize search parameter from request"""
    return request.args.get('search', '').replace("'", "''")

def build_search_where_clause(search, fields):
    """Build WHERE clause for search across multiple fields"""
    if not search:
        return ""
    conditions = [f"{field} LIKE '%{search}%'" for field in fields]
    return f"WHERE {' OR '.join(conditions)}"

def extract_paginated_results(result, pagination):
    """Extract data and total count from paginated query result"""
    if not result['success']:
        return None, None
    
    total = result['data'][0]['total_count'] if result['data'] else 0
    for row in result['data']:
        row.pop('total_count', None)
    
    return result['data'], total

@app.route('/')
def home():
    """Serve the React frontend"""
    return render_template('index.html')

@app.route('/api/signin', methods=['POST'])
@handle_errors
def signin():
    """Sign in: verify user exists by name + practice_name + location"""
    data = request.get_json() or {}
    name = sanitize_sql(data.get('name', ''))
    practice_name = sanitize_sql(data.get('practice_name', ''))
    location = sanitize_sql(data.get('location', ''))
    
    if not name or not practice_name or not location:
        return jsonify({'success': False, 'error': 'Name, Practice Name, and Location are required'}), 400
    
    # Check if user exists
    check_query = f"""
        SELECT user_id, name, practice_name, location, email 
        FROM workspace.default.users 
        WHERE name = '{name}' AND practice_name = '{practice_name}' AND location = '{location}'
    """
    check_result = execute_sql(check_query)
    
    if not check_result['success']:
        return jsonify({'success': False, 'error': check_result['error']}), 500
    
    if check_result['data']:
        return jsonify({'success': True, 'data': check_result['data'][0], 'message': 'Sign in successful'})
    else:
        return jsonify({'success': False, 'error': 'User not found. Please check your details or sign up.'}), 404

@app.route('/api/signup', methods=['POST'])
@handle_errors
def signup():
    """Sign up: create a new user if not already present"""
    data = request.get_json() or {}
    name = sanitize_sql(data.get('name', ''))
    practice_name = sanitize_sql(data.get('practice_name', ''))
    location = sanitize_sql(data.get('location', ''))
    email = sanitize_sql(data.get('email', ''))
    
    if not name or not practice_name or not location:
        return jsonify({'success': False, 'error': 'Name, Practice Name, and Location are required'}), 400
    
    # Check if user already exists
    check_query = f"""
        SELECT user_id, name, practice_name, location, email 
        FROM workspace.default.users 
        WHERE name = '{name}' AND practice_name = '{practice_name}' AND location = '{location}'
    """
    check_result = execute_sql(check_query)
    
    if not check_result['success']:
        return jsonify({'success': False, 'error': check_result['error']}), 500
    
    if check_result['data']:
        return jsonify({'success': False, 'error': 'User already exists with these details. Please sign in instead.'}), 409
    
    # Create new user
    email_clause = f"'{email}'" if email else "NULL"
    insert_query = f"""
        INSERT INTO workspace.default.users (name, practice_name, location, email, created_at)
        VALUES ('{name}', '{practice_name}', '{location}', {email_clause}, current_timestamp())
    """
    insert_result = execute_sql(insert_query)
    
    if not insert_result['success']:
        return jsonify({'success': False, 'error': insert_result['error']}), 500
    
    # Fetch the newly created user
    fetch_query = f"""
        SELECT user_id, name, practice_name, location, email 
        FROM workspace.default.users 
        WHERE name = '{name}' AND practice_name = '{practice_name}' AND location = '{location}'
        ORDER BY user_id DESC LIMIT 1
    """
    fetch_result = execute_sql(fetch_query)
    
    if fetch_result['success'] and fetch_result['data']:
        return jsonify({'success': True, 'data': fetch_result['data'][0], 'message': 'Account created successfully'})
    
    return jsonify({'success': False, 'error': 'Failed to retrieve created user'}), 500

@app.route('/api/scheduled-reports', methods=['GET'])
@handle_errors
def get_scheduled_reports():
    """Get scheduled reports with optional search and pagination (all users see all data)"""
    search = get_search_param()
    pagination = get_pagination_params()
    
    # Build query with search filter only (no user_id filtering)
    where_clause = build_search_where_clause(search, [
        'report_category', 'report_title', 'schedule_name', 'scheduled_by'
    ])
    
    query = f"""
        SELECT 
            report_id, report_category, report_title, schedule_name, scheduled_by,
            scheduled_time, frequency, updated_on_by, last_delivery, pause_schedule,
            COUNT(*) OVER() AS total_count
        FROM workspace.default.scheduled_reports 
        {where_clause}
        ORDER BY report_id
        LIMIT {pagination['limit']} OFFSET {pagination['offset']}
    """
    result = execute_sql(query)
    
    data, total = extract_paginated_results(result, pagination)
    if data is None:
        return jsonify({'success': False, 'error': result['error']}), 500
    
    return jsonify({
        'success': True,
        'data': data,
        'total': total,
        **pagination
    })

@app.route('/api/scheduled-reports/<int:report_id>/pause', methods=['POST'])
@handle_errors
def toggle_pause_schedule(report_id):
    """Toggle pause status of a scheduled report"""
    data = request.get_json() or {}
    pause_status = data.get('pause_schedule', 'Pause')
    
    query = f"""
        UPDATE workspace.default.scheduled_reports
        SET pause_schedule = '{pause_status}'
        WHERE report_id = {report_id}
    """
    result = execute_sql(query)
    
    if result['success']:
        return jsonify({'success': True, 'message': f'Schedule {pause_status.lower()}d successfully'})
    return jsonify({'success': False, 'error': result['error']}), 500

@app.route('/api/scheduled-reports/<int:report_id>/generate', methods=['POST'])
@handle_errors
def generate_report(report_id):
    """Trigger job to generate a report and insert into reports table"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    user_name = sanitize_sql(data.get('user_name', 'System'))
    
    # Get the scheduled report details
    query = f"SELECT * FROM workspace.default.scheduled_reports WHERE report_id = {report_id}"
    result = execute_sql(query)
    
    if not result['success'] or not result['data']:
        return jsonify({'success': False, 'error': 'Report not found'}), 404
    
    scheduled_report = result['data'][0]
    
    # Insert into reports table with user context
    user_id_clause = str(int(user_id)) if user_id else "NULL"
    insert_query = f"""
        INSERT INTO workspace.default.reports 
        (report_id, report_category, report_title, generated_by, generated_on, report_type, schedule_name, status, download_link, delete_flag, user_id)
        VALUES (
            '{report_id}',
            '{scheduled_report['report_category']}',
            '{scheduled_report['report_title']}',
            '{user_name}',
            current_timestamp(),
            '{scheduled_report['frequency']}',
            '{scheduled_report['schedule_name']}',
            'Generated',
            'link',
            'No',
            {user_id_clause}
        )
    """
    insert_result = execute_sql(insert_query)
    
    if not insert_result['success']:
        return jsonify({'success': False, 'error': insert_result['error']}), 500
    
    return jsonify({'success': True, 'message': 'Report generated successfully'})

@app.route('/api/scheduled-reports/<int:report_id>', methods=['DELETE'])
@handle_errors
def delete_scheduled_report(report_id):
    """Delete a scheduled report from the table"""
    query = f"""
        DELETE FROM workspace.default.scheduled_reports
        WHERE report_id = {report_id}
    """
    result = execute_sql(query)
    
    if result['success']:
        return jsonify({'success': True, 'message': 'Report deleted successfully'})
    return jsonify({'success': False, 'error': result['error']}), 500

@app.route('/api/generated-reports', methods=['GET'])
@handle_errors
def get_generated_reports():
    """Get generated reports with optional search and pagination, filtered by user_id"""
    search = get_search_param()
    pagination = get_pagination_params()
    user_id = request.args.get('user_id', '')
    
    # Build WHERE clause starting with delete flag and user filter
    conditions = ["delete_flag = 'No'"]
    if user_id:
        conditions.append(f"user_id = {int(user_id)}")
    
    if search:
        search_conditions = build_search_where_clause(search, [
            'report_category', 'report_title', 'generated_by', 'schedule_name'
        ]).replace('WHERE', '')
        conditions.append(f"({search_conditions})")
    
    where_clause = f"WHERE {' AND '.join(conditions)}"
    
    query = f"""
        SELECT 
            report_id, report_category, report_title, generated_by, generated_on,
            report_type, schedule_name, status, user_id,
            COUNT(*) OVER() AS total_count
        FROM workspace.default.reports 
        {where_clause}
        ORDER BY generated_on DESC
        LIMIT {pagination['limit']} OFFSET {pagination['offset']}
    """
    result = execute_sql(query)
    
    data, total = extract_paginated_results(result, pagination)
    if data is None:
        return jsonify({'success': False, 'error': result['error']}), 500
    
    return jsonify({
        'success': True,
        'data': data,
        'total': total,
        **pagination
    })

@app.route('/api/generated-reports/<int:report_id>', methods=['DELETE'])
@handle_errors
def delete_generated_report(report_id):
    """Delete a generated report from the table"""
    query = f"""
        DELETE FROM workspace.default.reports
        WHERE report_id = {report_id}
    """
    result = execute_sql(query)
    
    if result['success']:
        return jsonify({'success': True, 'message': 'Generated report deleted successfully'})
    return jsonify({'success': False, 'error': result['error']}), 500

@app.route('/api/generated-reports/<int:report_id>/download', methods=['GET'])
@handle_errors
def download_generated_report(report_id):
    """Download a generated report as a text file with all row data"""
    # Fetch the report data with user info via join
    query = f"""
        SELECT r.*, u.name AS user_name, u.practice_name, u.location 
        FROM workspace.default.reports r
        LEFT JOIN workspace.default.users u ON r.user_id = u.user_id
        WHERE r.report_id = {report_id}
    """
    result = execute_sql(query)
    
    if not result['success'] or not result['data']:
        return jsonify({'success': False, 'error': 'Report not found'}), 404
    
    report = result['data'][0]
    
    # Format timestamp
    generated_on = report.get('generated_on', 'N/A')
    if generated_on and generated_on != 'N/A':
        try:
            if isinstance(generated_on, str):
                dt = datetime.fromisoformat(generated_on.replace('Z', '+00:00'))
                generated_on = dt.strftime('%m-%d-%Y %I:%M:%S %p')
        except:
            pass
    
    # Format the report data as a text file
    text_content = f"""{'='*60}
GENERATED REPORT
{'='*60}

Report ID: {report.get('report_id', 'N/A')}
Report Category: {report.get('report_category', 'N/A')}
Report Title: {report.get('report_title', 'N/A')}
Generated By: {report.get('generated_by', 'N/A')}
Generated On: {generated_on}
Report Type: {report.get('report_type', 'N/A')}
Schedule Name: {report.get('schedule_name', 'N/A')}
Status: {report.get('status', 'N/A')}
Download Link: {report.get('download_link', 'N/A')}

--- Practitioner Info ---
Name: {report.get('user_name', 'N/A')}
Practice: {report.get('practice_name', 'N/A')}
Location: {report.get('location', 'N/A')}

{'='*60}
END OF REPORT
{'='*60}
"""
    
    # Create a BytesIO object
    text_file = io.BytesIO(text_content.encode('utf-8'))
    text_file.seek(0)
    
    # Generate filename
    filename = f"report_{report_id}_{report.get('report_title', 'report').replace(' ', '_')}.txt"
    
    return send_file(
        text_file,
        mimetype='text/plain',
        as_attachment=True,
        download_name=filename
    )

# ── Report Catalog (source: iknowmed-reports hardcoded list) ────────────────────────────────────────────────────────────────────────────────
REPORT_CATALOG = [
    {"id": 1,  "name": "Supportive Care Interventions Report",               "category": "General"},
    {"id": 2,  "name": "Decision Support Interventions Feedback Report",      "category": "General"},
    {"id": 3,  "name": "Patient Charts Merged Report",                        "category": "General"},
    {"id": 4,  "name": "Depression Screening Needed and Completed Report",    "category": "General"},
    {"id": 17, "name": "Visit List Report",                                   "category": "General"},
    {"id": 18, "name": "Charge Capture",                                      "category": "General"},
    {"id": 19, "name": "Patient List",                                        "category": "General"},
    {"id": 20, "name": "Clinical Profile Chart Alert",                        "category": "General"},
    {"id": 21, "name": "Order History",                                       "category": "General"},
    {"id": 22, "name": "Diagnosis",                                           "category": "General"},
    {"id": 26, "name": "Unfinished Charting",                                 "category": "General"},
    {"id": 8,  "name": "Outbound Fax Worklist Queue Report",                  "category": "Worklist Queues"},
    {"id": 11, "name": "Ins Auth Fin Counseling Worklist Queue Report",       "category": "Worklist Queues"},
    {"id": 12, "name": "Orders Queue Worklist Queue Report",                  "category": "Worklist Queues"},
    {"id": 15, "name": "Attach Documents Worklist Queue Productivity Report", "category": "Worklist Queues"},
    {"id": 16, "name": "Attach Documents Worklist Queue Audit Report",        "category": "Worklist Queues"},
    {"id": 6,  "name": "Medication Administration Record with Admix Report",  "category": "Medication & Orders"},
    {"id": 9,  "name": "Trending Pain Scores Report",                         "category": "Medication & Orders"},
    {"id": 10, "name": "Pain Scale and PDMP Evaluation Report",               "category": "Medication & Orders"},
    {"id": 13, "name": "Regimen Orders Report",                               "category": "Medication & Orders"},
    {"id": 25, "name": "Precision Medicine Orders & Results",                  "category": "Medication & Orders"},
    {"id": 14, "name": "Prescription Audit Report",                           "category": "Audit Reports"},
    {"id": 5,  "name": "Task & Time Cumulative Dashboard",                    "category": "Task & Time"},
    {"id": 23, "name": "Task and Time Capture Report",                        "category": "Task & Time"},
    {"id": 7,  "name": "iKnowMed G1 Report",                                 "category": "Integrations"},
    {"id": 24, "name": "Genospace iKM Integration",                           "category": "Integrations"},
]

CATEGORY_ORDER = ["General", "Worklist Queues", "Medication & Orders", "Audit Reports", "Task & Time", "Integrations"]

@app.route('/api/reports', methods=['GET'])
@handle_errors
def get_report_catalog():
    """Return the report catalog grouped by category, with optional search."""
    search = request.args.get('search', '')
    reports = REPORT_CATALOG
    if search:
        q = search.lower()
        reports = [r for r in reports if q in r['name'].lower() or q in r['category'].lower()]
    grouped = {}
    for cat in CATEGORY_ORDER:
        grouped[cat] = [r for r in reports if r['category'] == cat]
    return jsonify({'success': True, 'data': grouped, 'total': len(reports)})

@app.route('/api/reports/<int:report_id>/details', methods=['GET'])
@handle_errors
def get_report_details(report_id):
    """Return plot data for a specific report detail page.
    
    For report_id=7 (iKnowMed G1 Report), returns full detail data matching
    iknowmed-reports (volume, time_to_completion, usage, lifecycle, edits).
    All other reports return in_progress=true.
    """
    report = next((r for r in REPORT_CATALOG if r['id'] == report_id), None)
    if not report:
        return jsonify({'success': False, 'error': 'Report not found'}), 404

    if report_id == 7:
        # ── Full iknowmed-reports-style detail data ──
        import random
        random.seed(7 * 37)  # seed = 259
        dates = [f"7/{d}" for d in range(4, 15)]
        tc = 26
        raw = [random.randint(0, 6) for _ in dates]
        raw_sum = sum(raw) or 1
        total = [max(round(v / raw_sum * tc), 0) for v in raw]
        diff = tc - sum(total)
        for i in range(abs(diff)):
            total[i % len(total)] += 1 if diff > 0 else -1
        total = [max(v, 0) for v in total]
        saved = [min(random.randint(0, max(t, 1)), t) for t in total]
        ts = tc
        ss = sum(saved)

        # ── Override with dynamic counts from the database ──
        user_id = request.args.get('user_id', '')
        try:
            count_result = execute_sql("SELECT COUNT(*) AS cnt FROM workspace.default.scheduled_reports")
            if count_result['success'] and count_result['data']:
                ts = int(count_result['data'][0]['cnt'])
        except Exception:
            pass
        try:
            if user_id:
                saved_result = execute_sql(f"SELECT COUNT(*) AS cnt FROM workspace.default.reports WHERE user_id = {int(user_id)} AND delete_flag = 'No'")
            else:
                saved_result = execute_sql("SELECT COUNT(*) AS cnt FROM workspace.default.reports WHERE delete_flag = 'No'")
            if saved_result['success'] and saved_result['data']:
                ss = int(saved_result['data'][0]['cnt'])
        except Exception:
            pass

        rate = round(ss / ts * 100) if ts else 0

        return jsonify({
            'success': True,
            'data': {
                'report': report,
                'in_progress': False,
                'report_type': 'iknowmed',
                'volume': {
                    'dates': dates,
                    'total': total,
                    'saved': saved,
                    'total_sum': ts,
                    'saved_sum': ss,
                    'rate': rate,
                },
                'time_to_completion': {
                    'dates': [f"7/{d}" for d in range(1, 12)],
                    'total_avg': [190000, 186000, 182000, 178000, 174000, 170000, 166000, 158000, 148000, 138000, 125000],
                    'usq_avg': [185000, 182000, 178000, 174000, 170000, 166000, 162000, 155000, 145000, 135000, 122000],
                    'mr_avg': [195000, 190000, 185000, 180000, 175000, 170000, 165000, 160000, 152000, 142000, 128000],
                    'total_avg_str': '3097m 59s',
                    'usq_avg_str': '2106m 39s',
                    'mr_avg_str': '3428m 26s',
                    'map_to_save_avg': '0d 12h',
                },
                'usage_by_practice': {
                    'usage_rate': '100%',
                    'usage_fraction': '1 / 1',
                    'rows': [['Onc Hem of MSH', '24', '9']],
                },
                'usage_by_vendor': {
                    'usage_rate': '50%',
                    'usage_fraction': '1 / 2',
                    'rows': [['Caris', '39%'], ['Foundation', '0%']],
                },
                'lifecycle': {
                    'opened_for_review': 10,
                    'total_launches': 10,
                    'total_edited': 8,
                    'total_not_edited': 2,
                    'total_saved': 10,
                    'node_labels': ['Opened for Review', 'USQ Launch', 'MR Launch', 'Edited (USQ)', 'Not Edited (USQ)', 'Edited (MR)', 'Not Edited (MR)', 'USQ Saved', 'MR Saved'],
                    'link_sources': [0, 0, 1, 1, 2, 2, 3, 4, 5, 6],
                    'link_targets': [1, 2, 3, 4, 5, 6, 7, 7, 8, 8],
                    'link_values': [4, 6, 3, 1, 5, 1, 3, 1, 5, 1],
                },
                'edits': {
                    'diagnosis': [['ALL', '5/8'], ['Uterine Neoplasms - Endometrial Carcinoma', '3/6'], ['Pancreatic Adenocarcinoma', '1/1'], ['cancer', '1/1']],
                    'inference': [['ALL', '7'], ['TMB (Tumor mutational burden)', '6'], ['c-Met overexpression by IHC', '1'], ['ALK rearrangement status', '0'], ['BRAF V600E status', '0'], ['EGFR status', '0'], ['ERBB2 (HER2) mutation status', '0'], ['KRAS status', '0']],
                    'edits': [['ALL', 'ALL'], ['TMB high', 'Unknown'], ['(no value)', '<3+ intensity OR <50%'], ['(no value)', 'Unknown'], ['TMB high', '(no value)'], ['TMB intermediate', 'TMB high'], ['TMB intermediate', 'Unknown']],
                },
            }
        })
    elif report_id == 4:
        # ── Depression Screening Needed and Completed Report ──
        summary_result = execute_sql("""
            SELECT
                COUNT(*) AS total_records,
                COUNT(DISTINCT MRN) AS total_patients,
                COUNT_IF(Depression_Screening_Completed = 'Yes') AS screenings_completed,
                COUNT_IF(Depression_Screening_Completed = 'No') AS screenings_needed
            FROM workspace.default.depression_screening_report
        """)
        summary = summary_result['data'][0] if summary_result['success'] and summary_result['data'] else {}

        location_result = execute_sql("""
            SELECT Appointment_Location, Depression_Screening_Completed, COUNT(*) AS cnt
            FROM workspace.default.depression_screening_report
            GROUP BY Appointment_Location, Depression_Screening_Completed
            ORDER BY Appointment_Location, Depression_Screening_Completed
        """)
        status_by_location = location_result['data'] if location_result['success'] else []

        tools_result = execute_sql("""
            SELECT COALESCE(Screening_Tool_Used, 'None') AS Screening_Tool_Used, COUNT(*) AS cnt
            FROM workspace.default.depression_screening_report
            GROUP BY Screening_Tool_Used
            ORDER BY cnt DESC
        """)
        tools_distribution = tools_result['data'] if tools_result['success'] else []

        sex_result = execute_sql("""
            SELECT Sex_At_Birth, Depression_Screening_Completed, COUNT(*) AS cnt
            FROM workspace.default.depression_screening_report
            GROUP BY Sex_At_Birth, Depression_Screening_Completed
            ORDER BY Sex_At_Birth, Depression_Screening_Completed
        """)
        completion_by_sex = sex_result['data'] if sex_result['success'] else []

        overview_result = execute_sql("""
            SELECT Depression_Screening_Completed, COUNT(*) AS cnt
            FROM workspace.default.depression_screening_report
            GROUP BY Depression_Screening_Completed
        """)
        status_overview = overview_result['data'] if overview_result['success'] else []

        patients_result = execute_sql("""
            SELECT Last_Name, First_Name, MRN, DOB, Sex_At_Birth,
                   Appointment_Date_Time, Appointment_Location, Appointment_Provider_Resource,
                   Depression_Screening_Completed, Screening_Tool_Used, Plan_Date
            FROM workspace.default.depression_screening_report
            ORDER BY Appointment_Date_Time DESC
        """)
        patient_list = patients_result['data'] if patients_result['success'] else []

        return jsonify({
            'success': True,
            'data': {
                'report': report,
                'in_progress': False,
                'report_type': 'depression_screening',
                'summary': {
                    'total_patients': int(summary.get('total_patients', 0)),
                    'screenings_completed': int(summary.get('screenings_completed', 0)),
                    'screenings_needed': int(summary.get('screenings_needed', 0)),
                    'total_records': int(summary.get('total_records', 0)),
                },
                'status_by_location': status_by_location,
                'tools_distribution': tools_distribution,
                'completion_by_sex': completion_by_sex,
                'status_overview': status_overview,
                'patient_list': patient_list,
            }
        })
    else:
        # ── All other reports: in progress ──
        return jsonify({
            'success': True,
            'data': {
                'report': report,
                'in_progress': True,
            }
        })


@app.route('/api/reports/<int:report_id>/generate', methods=['POST'])
@handle_errors
def generate_catalog_report(report_id):
    """Generate a report from the catalog and insert into reports table"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    user_name = sanitize_sql(data.get('user_name', 'System'))

    report = next((r for r in REPORT_CATALOG if r['id'] == report_id), None)
    if not report:
        return jsonify({'success': False, 'error': 'Report not found'}), 404

    user_id_clause = str(int(user_id)) if user_id else "NULL"
    insert_query = f"""
        INSERT INTO workspace.default.reports
        (report_id, report_category, report_title, generated_by, generated_on, report_type, schedule_name, status, download_link, delete_flag, user_id)
        VALUES (
            {report_id},
            '{sanitize_sql(report['category'])}',
            '{sanitize_sql(report['name'])}',
            '{user_name}',
            current_timestamp(),
            'Manual',
            'Manual Generate',
            'Generated',
            'link',
            'No',
            {user_id_clause}
        )
    """
    insert_result = execute_sql(insert_query)

    if not insert_result['success']:
        return jsonify({'success': False, 'error': insert_result['error']}), 500

    return jsonify({'success': True, 'message': 'Report generated successfully'})


@app.route('/api/reports/<int:report_id>/schedule', methods=['POST'])
@handle_errors
def schedule_catalog_report(report_id):
    """Schedule a report from the catalog and insert into scheduled_reports table"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    user_name = sanitize_sql(data.get('user_name', 'System'))
    schedule_name = sanitize_sql(data.get('schedule_name', ''))
    frequency = sanitize_sql(data.get('frequency', 'Weekly'))
    scheduled_time = data.get('scheduled_time', '')

    report = next((r for r in REPORT_CATALOG if r['id'] == report_id), None)
    if not report:
        return jsonify({'success': False, 'error': 'Report not found'}), 404

    if not schedule_name:
        return jsonify({'success': False, 'error': 'Schedule name is required'}), 400

    max_id_result = execute_sql("SELECT COALESCE(MAX(report_id), 0) AS max_id FROM workspace.default.scheduled_reports")
    new_report_id = 1
    if max_id_result['success'] and max_id_result['data']:
        new_report_id = int(max_id_result['data'][0]['max_id']) + 1

    user_id_clause = str(int(user_id)) if user_id else "NULL"
    if scheduled_time:
        scheduled_time_clause = f"'{sanitize_sql(scheduled_time)}'"
    else:
        scheduled_time_clause = "current_timestamp()"

    insert_query = f"""
        INSERT INTO workspace.default.scheduled_reports
        (report_id, report_category, report_title, schedule_name, scheduled_by, scheduled_time,
         frequency, updated_on_by, last_delivery, pause_schedule, action, edit_flag, delete_flag, user_id)
        VALUES (
            {new_report_id},
            '{sanitize_sql(report['category'])}',
            '{sanitize_sql(report['name'])}',
            '{schedule_name}',
            '{user_name}',
            {scheduled_time_clause},
            '{frequency}',
            '{user_name}',
            NULL,
            'Pause',
            'Generate',
            'Edit',
            'No',
            {user_id_clause}
        )
    """
    insert_result = execute_sql(insert_query)

    if not insert_result['success']:
        return jsonify({'success': False, 'error': insert_result['error']}), 500

    return jsonify({'success': True, 'message': 'Report scheduled successfully'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)