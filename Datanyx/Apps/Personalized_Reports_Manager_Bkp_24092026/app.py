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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)