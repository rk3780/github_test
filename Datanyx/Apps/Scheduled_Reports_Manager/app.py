from flask import Flask, jsonify, render_template, request, send_file
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import io
import time
import logging
from datetime import datetime
from functools import wraps

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

@app.route('/api/scheduled-reports', methods=['GET'])
@handle_errors
def get_scheduled_reports():
    """Get scheduled reports with optional search and pagination"""
    search = get_search_param()
    pagination = get_pagination_params()
    
    # Build query with search filter
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
    # Get the scheduled report details
    query = f"SELECT * FROM workspace.default.scheduled_reports WHERE report_id = {report_id}"
    result = execute_sql(query)
    
    if not result['success'] or not result['data']:
        return jsonify({'success': False, 'error': 'Report not found'}), 404
    
    scheduled_report = result['data'][0]
    
    # Insert into reports table
    insert_query = f"""
        INSERT INTO workspace.default.reports 
        (report_id, report_category, report_title, generated_by, generated_on, report_type, schedule_name, status, download_link, delete_flag)
        VALUES (
            '{report_id}',
            '{scheduled_report['report_category']}',
            '{scheduled_report['report_title']}',
            'System',
            current_timestamp(),
            '{scheduled_report['frequency']}',
            '{scheduled_report['schedule_name']}',
            'Generated',
            'link',
            'No'
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
    """Get generated reports with optional search and pagination"""
    search = get_search_param()
    pagination = get_pagination_params()
    
    # Build query with search filter, excluding deleted reports
    where_clause = "WHERE delete_flag = 'No'"
    if search:
        search_conditions = build_search_where_clause(search, [
            'report_category', 'report_title', 'generated_by', 'schedule_name'
        ]).replace('WHERE', '')
        where_clause += f" AND ({search_conditions})"
    
    query = f"""
        SELECT 
            report_id, report_category, report_title, generated_by, generated_on,
            report_type, schedule_name, status,
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
    # Fetch the report data
    query = f"SELECT * FROM workspace.default.reports WHERE report_id = {report_id}"
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