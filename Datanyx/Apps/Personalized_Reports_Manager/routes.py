"""API routes for the Personalized Reports Manager."""
from flask import Blueprint, jsonify, request, send_file
from functools import wraps
from datetime import datetime
import io
import csv
import logging

from db import sanitize_sql, execute_sql
from config import REPORT_CATALOG, CATEGORY_ORDER
from generators import generate_generic_report
from embed import get_scoped_token, get_dashboard_id_for_report

bp = Blueprint('api', __name__)


# ── Helper functions ──────────────────────────────────────────────────────────

def handle_errors(f):
    """Decorator to handle errors consistently across all routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logging.exception(f"Error in {f.__name__}")
            return jsonify({'success': False, 'error': str(e)}), 500
    return decorated_function


def get_pagination_params():
    """Extract pagination parameters from request."""
    return {
        'limit': int(request.args.get('limit', 15)),
        'offset': int(request.args.get('offset', 0))
    }


def get_search_param():
    """Extract and sanitize search parameter from request."""
    return request.args.get('search', '').replace("'", "''")


def build_search_where_clause(search, fields):
    """Build WHERE clause for search across multiple fields."""
    if not search:
        return ""
    conditions = [f"{field} LIKE '%{search}%'" for field in fields]
    return f"WHERE {' OR '.join(conditions)}"


def extract_paginated_results(result, pagination):
    """Extract data and total count from paginated query result."""
    if not result['success']:
        return None, None
    total = result['data'][0]['total_count'] if result['data'] else 0
    for row in result['data']:
        row.pop('total_count', None)
    return result['data'], total


# ── Auth Routes ────────────────────────────────────────────────────────────────

@bp.route('/api/signin', methods=['POST'])
@handle_errors
def signin():
    data = request.get_json() or {}
    name = sanitize_sql(data.get('name', ''))
    practice_name = sanitize_sql(data.get('practice_name', ''))
    location = sanitize_sql(data.get('location', ''))
    if not name or not practice_name or not location:
        return jsonify({'success': False, 'error': 'Name, Practice Name, and Location are required'}), 400
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
    return jsonify({'success': False, 'error': 'User not found. Please check your details or sign up.'}), 404


@bp.route('/api/signup', methods=['POST'])
@handle_errors
def signup():
    data = request.get_json() or {}
    name = sanitize_sql(data.get('name', ''))
    practice_name = sanitize_sql(data.get('practice_name', ''))
    location = sanitize_sql(data.get('location', ''))
    email = sanitize_sql(data.get('email', ''))
    if not name or not practice_name or not location:
        return jsonify({'success': False, 'error': 'Name, Practice Name, and Location are required'}), 400
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
    email_clause = f"'{email}'" if email else "NULL"
    insert_query = f"""
        INSERT INTO workspace.default.users (name, practice_name, location, email, created_at)
        VALUES ('{name}', '{practice_name}', '{location}', {email_clause}, current_timestamp())
    """
    insert_result = execute_sql(insert_query)
    if not insert_result['success']:
        return jsonify({'success': False, 'error': insert_result['error']}), 500
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


# ── Scheduled Reports Routes ─────────────────────────────────────────────────

@bp.route('/api/scheduled-reports', methods=['GET'])
@handle_errors
def get_scheduled_reports():
    search = get_search_param()
    pagination = get_pagination_params()
    where_clause = build_search_where_clause(search, ['report_category', 'report_title', 'schedule_name', 'scheduled_by'])
    query = f"""
        SELECT report_id, report_category, report_title, schedule_name, scheduled_by,
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
    return jsonify({'success': True, 'data': data, 'total': total, **pagination})


@bp.route('/api/scheduled-reports/<int:report_id>/pause', methods=['POST'])
@handle_errors
def toggle_pause_schedule(report_id):
    data = request.get_json() or {}
    pause_status = data.get('pause_schedule', 'Pause')
    query = f"UPDATE workspace.default.scheduled_reports SET pause_schedule = '{pause_status}' WHERE report_id = {report_id}"
    result = execute_sql(query)
    if result['success']:
        return jsonify({'success': True, 'message': f'Schedule {pause_status.lower()}d successfully'})
    return jsonify({'success': False, 'error': result['error']}), 500


@bp.route('/api/scheduled-reports/<int:report_id>/generate', methods=['POST'])
@handle_errors
def generate_report(report_id):
    data = request.get_json() or {}
    user_id = data.get('user_id')
    user_name = sanitize_sql(data.get('user_name', 'System'))
    query = f"SELECT * FROM workspace.default.scheduled_reports WHERE report_id = {report_id}"
    result = execute_sql(query)
    if not result['success'] or not result['data']:
        return jsonify({'success': False, 'error': 'Report not found'}), 404
    scheduled_report = result['data'][0]
    user_id_clause = str(int(user_id)) if user_id else "NULL"
    insert_query = f"""
        INSERT INTO workspace.default.reports
        (report_id, report_category, report_title, generated_by, generated_on, report_type, schedule_name, status, download_link, delete_flag, user_id)
        VALUES ('{report_id}', '{scheduled_report['report_category']}', '{scheduled_report['report_title']}',
                '{user_name}', current_timestamp(), '{scheduled_report['frequency']}',
                '{scheduled_report['schedule_name']}', 'Generated', 'link', 'No', {user_id_clause})
    """
    insert_result = execute_sql(insert_query)
    if not insert_result['success']:
        return jsonify({'success': False, 'error': insert_result['error']}), 500
    return jsonify({'success': True, 'message': 'Report generated successfully'})


@bp.route('/api/scheduled-reports/<int:report_id>', methods=['DELETE'])
@handle_errors
def delete_scheduled_report(report_id):
    query = f"DELETE FROM workspace.default.scheduled_reports WHERE report_id = {report_id}"
    result = execute_sql(query)
    if result['success']:
        return jsonify({'success': True, 'message': 'Report deleted successfully'})
    return jsonify({'success': False, 'error': result['error']}), 500


@bp.route('/api/scheduled-reports/<int:report_id>/edit', methods=['PUT'])
@handle_errors
def edit_scheduled_report(report_id):
    data = request.get_json() or {}
    schedule_name = sanitize_sql(data.get('schedule_name', ''))
    frequency = sanitize_sql(data.get('frequency', ''))
    scheduled_time = data.get('scheduled_time', '')
    user_name = sanitize_sql(data.get('user_name', 'System'))
    if not schedule_name:
        return jsonify({'success': False, 'error': 'Schedule name is required'}), 400
    valid_freqs = ['Daily', 'Weekly', 'Monthly', 'Adhoc']
    if frequency and frequency not in valid_freqs:
        return jsonify({'success': False, 'error': f'Invalid frequency. Must be one of: {", ".join(valid_freqs)}'}), 400
    set_clauses = [f"schedule_name = '{schedule_name}'"]
    if frequency:
        set_clauses.append(f"frequency = '{frequency}'")
    if scheduled_time:
        set_clauses.append(f"scheduled_time = '{sanitize_sql(scheduled_time)}'")
    set_clauses.append(f"updated_on_by = '{user_name}'")
    query = f"UPDATE workspace.default.scheduled_reports SET {', '.join(set_clauses)} WHERE report_id = {report_id}"
    result = execute_sql(query)
    if result['success']:
        return jsonify({'success': True, 'message': 'Schedule updated successfully'})
    return jsonify({'success': False, 'error': result['error']}), 500


# ── Generated Reports Routes ──────────────────────────────────────────────────

@bp.route('/api/generated-reports', methods=['GET'])
@handle_errors
def get_generated_reports():
    search = get_search_param()
    pagination = get_pagination_params()
    user_id = request.args.get('user_id', '')
    conditions = ["delete_flag = 'No'"]
    if user_id:
        conditions.append(f"user_id = {int(user_id)}")
    if search:
        search_conditions = build_search_where_clause(search, ['report_category', 'report_title', 'generated_by', 'schedule_name']).replace('WHERE', '')
        conditions.append(f"({search_conditions})")
    where_clause = f"WHERE {' AND '.join(conditions)}"
    query = f"""
        SELECT report_id, report_category, report_title, generated_by, generated_on,
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
    return jsonify({'success': True, 'data': data, 'total': total, **pagination})


@bp.route('/api/generated-reports/<int:report_id>', methods=['DELETE'])
@handle_errors
def delete_generated_report(report_id):
    query = f"DELETE FROM workspace.default.reports WHERE report_id = {report_id}"
    result = execute_sql(query)
    if result['success']:
        return jsonify({'success': True, 'message': 'Generated report deleted successfully'})
    return jsonify({'success': False, 'error': result['error']}), 500


@bp.route('/api/generated-reports/<int:report_id>/download', methods=['GET'])
@handle_errors
def download_generated_report(report_id):
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
    generated_on = report.get('generated_on', 'N/A')
    if generated_on and generated_on != 'N/A':
        try:
            if isinstance(generated_on, str):
                dt = datetime.fromisoformat(generated_on.replace('Z', '+00:00'))
                generated_on = dt.strftime('%m-%d-%Y %I:%M:%S %p')
        except:
            pass
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
    text_file = io.BytesIO(text_content.encode('utf-8'))
    text_file.seek(0)
    filename = f"report_{report_id}_{report.get('report_title', 'report').replace(' ', '_')}.txt"
    return send_file(text_file, mimetype='text/plain', as_attachment=True, download_name=filename)


# ── Report Catalog Routes ────────────────────────────────────────────────────

@bp.route('/api/reports', methods=['GET'])
@handle_errors
def get_report_catalog():
    search = request.args.get('search', '')
    reports = REPORT_CATALOG
    if search:
        q = search.lower()
        reports = [r for r in reports if q in r['name'].lower() or q in r['category'].lower()]
    grouped = {}
    for cat in CATEGORY_ORDER:
        grouped[cat] = [r for r in reports if r['category'] == cat]
    return jsonify({'success': True, 'data': grouped, 'total': len(reports)})


@bp.route('/api/reports/<int:report_id>/details', methods=['GET'])
@handle_errors
def get_report_details(report_id):
    report = next((r for r in REPORT_CATALOG if r['id'] == report_id), None)
    if not report:
        return jsonify({'success': False, 'error': 'Report not found'}), 404

    if report_id == 7:
        import random
        random.seed(7 * 37)
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
        return jsonify({'success': True, 'data': {
            'report': report, 'in_progress': False, 'report_type': 'iknowmed',
            'volume': {'dates': dates, 'total': total, 'saved': saved, 'total_sum': ts, 'saved_sum': ss, 'rate': rate},
            'time_to_completion': {
                'dates': [f"7/{d}" for d in range(1, 12)],
                'total_avg': [190000, 186000, 182000, 178000, 174000, 170000, 166000, 158000, 148000, 138000, 125000],
                'usq_avg': [185000, 182000, 178000, 174000, 170000, 166000, 162000, 155000, 145000, 135000, 122000],
                'mr_avg': [195000, 190000, 185000, 180000, 175000, 170000, 165000, 160000, 152000, 142000, 128000],
                'total_avg_str': '3097m 59s', 'usq_avg_str': '2106m 39s', 'mr_avg_str': '3428m 26s', 'map_to_save_avg': '0d 12h',
            },
            'usage_by_practice': {'usage_rate': '100%', 'usage_fraction': '1 / 1', 'rows': [['Onc Hem of MSH', '24', '9']]},
            'usage_by_vendor': {'usage_rate': '50%', 'usage_fraction': '1 / 2', 'rows': [['Caris', '39%'], ['Foundation', '0%']]},
            'lifecycle': {
                'opened_for_review': 10, 'total_launches': 10, 'total_edited': 8, 'total_not_edited': 2, 'total_saved': 10,
                'node_labels': ['Opened for Review', 'USQ Launch', 'MR Launch', 'Edited (USQ)', 'Not Edited (USQ)', 'Edited (MR)', 'Not Edited (MR)', 'USQ Saved', 'MR Saved'],
                'link_sources': [0, 0, 1, 1, 2, 2, 3, 4, 5, 6], 'link_targets': [1, 2, 3, 4, 5, 6, 7, 7, 8, 8],
                'link_values': [4, 6, 3, 1, 5, 1, 3, 1, 5, 1],
            },
            'edits': {
                'diagnosis': [['ALL', '5/8'], ['Uterine Neoplasms - Endometrial Carcinoma', '3/6'], ['Pancreatic Adenocarcinoma', '1/1'], ['cancer', '1/1']],
                'inference': [['ALL', '7'], ['TMB (Tumor mutational burden)', '6'], ['c-Met overexpression by IHC', '1'], ['ALK rearrangement status', '0'], ['BRAF V600E status', '0'], ['EGFR status', '0'], ['ERBB2 (HER2) mutation status', '0'], ['KRAS status', '0']],
                'edits': [['ALL', 'ALL'], ['TMB high', 'Unknown'], ['(no value)', '<3+ intensity OR <50%'], ['(no value)', 'Unknown'], ['TMB high', '(no value)'], ['TMB intermediate', 'TMB high'], ['TMB intermediate', 'Unknown']],
            },
        }})
    elif report_id == 4:
        # Depression Screening - embedded Databricks AI/BI dashboard
        return jsonify({'success': True, 'data': {
            'report': report,
            'in_progress': False,
            'report_type': 'embedded_dashboard',
        }})
    elif report_id == 25:
        # Precision Medicine Orders & Results - embedded Databricks AI/BI dashboard
        return jsonify({'success': True, 'data': {
            'report': report,
            'in_progress': False,
            'report_type': 'embedded_dashboard',
        }})
    else:
        filters = {
            'mapping_date': request.args.get('mapping_date', 'all'),
            'status': request.args.getlist('status'),
            'launch_location': request.args.getlist('launch_location'),
            'diagnosis': request.args.getlist('diagnosis'),
        }
        data = generate_generic_report(report, report_id, filters)
        return jsonify({'success': True, 'data': data})


@bp.route('/api/reports/<int:report_id>/embed-token', methods=['GET'])
@handle_errors
def get_embed_token(report_id):
    import os
    report = next((r for r in REPORT_CATALOG if r['id'] == report_id), None)
    if not report:
        return jsonify({'success': False, 'error': 'Report not found'}), 404
    external_viewer_id = request.args.get('external_viewer_id')
    external_value = request.args.get('external_value')
    try:
        token = get_scoped_token(report_id, external_viewer_id=external_viewer_id, external_value=external_value)
        return jsonify({
            'success': True,
            'token': token,
            'instance_url': os.environ.get('DATABRICKS_INSTANCE_URL', ''),
            'workspace_id': os.environ.get('DATABRICKS_WORKSPACE_ID', ''),
            'dashboard_id': get_dashboard_id_for_report(report_id),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/reports/<int:report_id>/generate', methods=['POST'])
@handle_errors
def generate_catalog_report(report_id):
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
        VALUES ({report_id}, '{sanitize_sql(report['category'])}', '{sanitize_sql(report['name'])}',
                '{user_name}', current_timestamp(), 'Manual', 'Manual Generate', 'Generated', 'link', 'No', {user_id_clause})
    """
    insert_result = execute_sql(insert_query)
    if not insert_result['success']:
        return jsonify({'success': False, 'error': insert_result['error']}), 500
    return jsonify({'success': True, 'message': 'Report generated successfully'})


@bp.route('/api/reports/<int:report_id>/schedule', methods=['POST'])
@handle_errors
def schedule_catalog_report(report_id):
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
    scheduled_time_clause = f"'{sanitize_sql(scheduled_time)}'" if scheduled_time else "current_timestamp()"
    insert_query = f"""
        INSERT INTO workspace.default.scheduled_reports
        (report_id, report_category, report_title, schedule_name, scheduled_by, scheduled_time,
         frequency, updated_on_by, last_delivery, pause_schedule, action, edit_flag, delete_flag, user_id)
        VALUES ({new_report_id}, '{sanitize_sql(report['category'])}', '{sanitize_sql(report['name'])}',
                '{schedule_name}', '{user_name}', {scheduled_time_clause}, '{frequency}',
                '{user_name}', NULL, 'Pause', 'Generate', 'Edit', 'No', {user_id_clause})
    """
    insert_result = execute_sql(insert_query)
    if not insert_result['success']:
        return jsonify({'success': False, 'error': insert_result['error']}), 500
    return jsonify({'success': True, 'message': 'Report scheduled successfully'})


@bp.route('/api/reports/<int:report_id>/export', methods=['GET'])
@handle_errors
def export_report_csv(report_id):
    report = next((r for r in REPORT_CATALOG if r['id'] == report_id), None)
    if not report:
        return jsonify({'success': False, 'error': 'Report not found'}), 404
    if report_id == 4:
        summary_result = execute_sql("SELECT * FROM workspace.default.depression_screening_report LIMIT 100")
        data_resp = {'table_data': {'columns': ['Col1'], 'rows': [['val1']]}}
        if summary_result['success'] and summary_result['data']:
            cols = list(summary_result['data'][0].keys())
            data_resp = {'table_data': {'columns': cols, 'rows': [[row[c] for c in cols] for row in summary_result['data']]}}
    else:
        data_resp = generate_generic_report(report, report_id)
    table = data_resp.get('table_data', {})
    columns = table.get('columns', [])
    rows = table.get('rows', [])
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    for row in rows:
        writer.writerow(row)
    csv_bytes = io.BytesIO(output.getvalue().encode('utf-8'))
    csv_bytes.seek(0)
    filename = f"{report['name'].replace(' ', '_')}_export.csv"
    return send_file(csv_bytes, mimetype='text/csv', as_attachment=True, download_name=filename)


# ── Dashboard Route ───────────────────────────────────────────────────────────

@bp.route('/api/dashboard', methods=['GET'])
@handle_errors
def get_dashboard_stats():
    user_id = request.args.get('user_id', '')
    stats = {
        'total_reports_available': len(REPORT_CATALOG),
        'total_categories': len(CATEGORY_ORDER),
        'generated_reports': 0, 'scheduled_reports': 0, 'recent_generated': [],
    }
    try:
        gen_result = execute_sql(f"SELECT COUNT(*) AS cnt FROM workspace.default.reports WHERE delete_flag = 'No'" + (f" AND user_id = {int(user_id)}" if user_id else ""))
        if gen_result['success'] and gen_result['data']:
            stats['generated_reports'] = int(gen_result['data'][0]['cnt'])
    except Exception:
        pass
    try:
        sched_result = execute_sql("SELECT COUNT(*) AS cnt FROM workspace.default.scheduled_reports")
        if sched_result['success'] and sched_result['data']:
            stats['scheduled_reports'] = int(sched_result['data'][0]['cnt'])
    except Exception:
        pass
    try:
        recent_result = execute_sql(f"""
            SELECT report_id, report_category, report_title, generated_by, generated_on, status
            FROM workspace.default.reports
            WHERE delete_flag = 'No'""" + (f" AND user_id = {int(user_id)}" if user_id else "") + """
            ORDER BY generated_on DESC LIMIT 5
        """)
        if recent_result['success']:
            stats['recent_generated'] = recent_result['data']
    except Exception:
        pass
    return jsonify({'success': True, 'data': stats})