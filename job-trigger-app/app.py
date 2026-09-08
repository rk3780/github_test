from flask import Flask, jsonify, render_template, request, Response, send_file
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import os
import io
import time
import logging
from datetime import datetime

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
            time.sleep(0.5)
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

@app.route('/')
def home():
    """Serve the React frontend"""
    return render_template('index.html')

# @app.route('/api/jobs', methods=['GET'])
# def list_jobs():
#     """List all available jobs in the workspace"""
#     try:
#         jobs = w.jobs.list()
#         job_list = [{
#             'job_id': job.job_id,
#             'name': job.settings.name if job.settings else f"Job {job.job_id}",
#             'created_time': job.created_time
#         } for job in jobs]
        
#         return jsonify({'jobs': job_list})
#     except Exception as e:
#         print(f"Error listing jobs: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/test', methods=['GET'])
# def test_permissions():
#     """Test endpoint to check permissions"""
#     try:
#         # Try to get the specific job
#         job = w.jobs.get(job_id=280040695852859)
#         return jsonify({
#             'success': True,
#             'job_name': job.settings.name if job.settings else 'Unknown',
#             'job_id': job.job_id,
#             'message': 'Successfully retrieved job details'
#         })
#     except Exception as e:
#         print(f"Error getting job: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({
#             'success': False,
#             'error': str(e),
#             'message': 'Failed to retrieve job. The app service principal may not have permission to access this job.'
#         }), 403

# @app.route('/api/jobs/<int:job_id>/run', methods=['POST'])
# def trigger_job(job_id):
#     """Trigger a job run using w.jobs.run_now()"""
#     try:
#         # Get parameter from request body
#         data = request.get_json() or {}
#         parameter_value = data.get('parameter')
        
#         # Prepare notebook parameters
#         notebook_params = {}
#         if parameter_value is not None:
#             notebook_params['report_id'] = str(parameter_value)
        
#         # Trigger the job with parameters
#         run = w.jobs.run_now(
#             job_id=job_id,
#             notebook_params=notebook_params if notebook_params else None
#         )
        
#         # Get initial run details
#         run_details = w.jobs.get_run(run_id=run.run_id)
        
#         return jsonify({
#             'run_id': run.run_id,
#             'job_id': job_id,
#             'state': run_details.state.life_cycle_state.value if run_details.state else 'UNKNOWN',
#             'run_page_url': run_details.run_page_url,
#             'start_time': run_details.start_time,
#             'parameters': notebook_params
#         })
#     except Exception as e:
#         # Log the full error
#         print(f"Error triggering job {job_id}: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({'error': f'Failed to trigger job: {str(e)}'}), 500

# @app.route('/api/runs/<int:run_id>', methods=['GET'])
# def get_run_status(run_id):
#     """Check the status of a job run"""
#     try:
#         run = w.jobs.get_run(run_id=run_id)
        
#         response = {
#             'run_id': run_id,
#             'job_id': run.job_id,
#             'state': run.state.life_cycle_state.value if run.state else 'UNKNOWN',
#             'run_page_url': run.run_page_url,
#             'start_time': run.start_time,
#             'end_time': run.end_time
#         }
        
#         # Add result state if available
#         if run.state and run.state.result_state:
#             response['result_state'] = run.state.result_state.value
        
#         # Add state message if available
#         if run.state and run.state.state_message:
#             response['state_message'] = run.state.state_message
            
#         return jsonify(response)
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

@app.route('/api/scheduled-reports', methods=['GET'])
def get_scheduled_reports():
    """Get scheduled reports with optional search and pagination"""
    try:
        search = request.args.get('search', '')
        limit = int(request.args.get('limit', 15))
        offset = int(request.args.get('offset', 0))
        
        # Build query with search filter
        where_clause = ""
        if search:
            where_clause = f"""WHERE 
                report_category LIKE '%{search}%' OR 
                report_title LIKE '%{search}%' OR 
                schedule_name LIKE '%{search}%' OR
                scheduled_by LIKE '%{search}%'
            """
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM workspace.default.scheduled_reports {where_clause}"
        count_result = execute_sql(count_query)
        total = count_result['data'][0]['total'] if count_result['success'] and count_result['data'] else 0
        
        # Get paginated data
        query = f"""
            SELECT * FROM workspace.default.scheduled_reports 
            {where_clause}
            ORDER BY report_id
            LIMIT {limit} OFFSET {offset}
        """
        result = execute_sql(query)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['data'],
                'total': total,
                'limit': limit,
                'offset': offset
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
    except Exception as e:
        print(f"Error fetching scheduled reports: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduled-reports/<int:report_id>/pause', methods=['POST'])
def toggle_pause_schedule(report_id):
    """Toggle pause status of a scheduled report"""
    try:
        data = request.get_json() or {}
        pause_status = data.get('pause_schedule', 'Pause')  # 'Pause' or 'Paused'
        
        query = f"""
            UPDATE workspace.default.scheduled_reports
            SET pause_schedule = '{pause_status}'
            WHERE report_id = {report_id}
        """
        result = execute_sql(query)
        
        if result['success']:
            return jsonify({'success': True, 'message': f'Schedule {pause_status.lower()}d successfully'})
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
    except Exception as e:
        print(f"Error toggling pause: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduled-reports/<int:report_id>/generate', methods=['POST'])
def generate_report(report_id):
    """Trigger job to generate a report and insert into reports table"""
    try:
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
        
        # # Trigger the job with report_id parameter
        # run = w.jobs.run_now(
        #     job_id=280040695852859,
        #     notebook_params={'report_id': str(report_id)}
        # )
        
        return jsonify({
            'success': True,
            'message': 'Report generated successfully'#,
            # 'run_id': run.run_id
        })
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scheduled-reports/<int:report_id>', methods=['DELETE'])
def delete_scheduled_report(report_id):
    """Delete a scheduled report from the table"""
    try:
        query = f"""
            DELETE FROM workspace.default.scheduled_reports
            WHERE report_id = {report_id}
        """
        result = execute_sql(query)
        
        if result['success']:
            return jsonify({'success': True, 'message': 'Report deleted successfully'})
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
    except Exception as e:
        print(f"Error deleting report: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generated-reports', methods=['GET'])
def get_generated_reports():
    """Get generated reports with optional search and pagination"""
    try:
        search = request.args.get('search', '')
        limit = int(request.args.get('limit', 15))
        offset = int(request.args.get('offset', 0))
        
        # Build query with search filter, excluding deleted reports
        where_clause = "WHERE delete_flag = 'No'"
        if search:
            where_clause += f""" AND (
                report_category LIKE '%{search}%' OR 
                report_title LIKE '%{search}%' OR 
                generated_by LIKE '%{search}%' OR
                schedule_name LIKE '%{search}%'
            )"""
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM workspace.default.reports {where_clause}"
        count_result = execute_sql(count_query)
        total = count_result['data'][0]['total'] if count_result['success'] and count_result['data'] else 0
        
        # Get paginated data
        query = f"""
            SELECT * FROM workspace.default.reports 
            {where_clause}
            ORDER BY generated_on DESC
            LIMIT {limit} OFFSET {offset}
        """
        result = execute_sql(query)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['data'],
                'total': total,
                'limit': limit,
                'offset': offset
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
    except Exception as e:
        print(f"Error fetching generated reports: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generated-reports/<int:report_id>', methods=['DELETE'])
def delete_generated_report(report_id):
    """Delete a generated report from the table"""
    try:
        query = f"""
            DELETE FROM workspace.default.reports
            WHERE report_id = {report_id}
        """
        result = execute_sql(query)
        
        if result['success']:
            return jsonify({'success': True, 'message': 'Generated report deleted successfully'})
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
    except Exception as e:
        print(f"Error deleting generated report: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generated-reports/<int:report_id>/download', methods=['GET'])
def download_generated_report(report_id):
    """Download a generated report as a text file with all row data"""
    try:
        # Fetch the report data
        query = f"SELECT * FROM workspace.default.reports WHERE report_id = {report_id}"
        result = execute_sql(query)
        
        if not result['success'] or not result['data']:
            return jsonify({'success': False, 'error': 'Report not found'}), 404
        
        report = result['data'][0]
        
        # Format the report data as a text file
        text_content = "="*60 + "\n"
        text_content += "GENERATED REPORT\n"
        text_content += "="*60 + "\n\n"
        
        text_content += f"Report ID: {report.get('report_id', 'N/A')}\n"
        text_content += f"Report Category: {report.get('report_category', 'N/A')}\n"
        text_content += f"Report Title: {report.get('report_title', 'N/A')}\n"
        text_content += f"Generated By: {report.get('generated_by', 'N/A')}\n"
        
        # Format timestamp
        generated_on = report.get('generated_on', 'N/A')
        if generated_on and generated_on != 'N/A':
            try:
                if isinstance(generated_on, str):
                    dt = datetime.fromisoformat(generated_on.replace('Z', '+00:00'))
                    generated_on = dt.strftime('%m-%d-%Y %I:%M:%S %p')
            except:
                pass
        text_content += f"Generated On: {generated_on}\n"
        
        text_content += f"Report Type: {report.get('report_type', 'N/A')}\n"
        text_content += f"Schedule Name: {report.get('schedule_name', 'N/A')}\n"
        text_content += f"Status: {report.get('status', 'N/A')}\n"
        text_content += f"Download Link: {report.get('download_link', 'N/A')}\n"
        
        text_content += "\n" + "="*60 + "\n"
        text_content += "END OF REPORT\n"
        text_content += "="*60 + "\n"
        
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
    # except Exception as e:
    #     print(f"Error downloading report: {str(e)}")
    #     import traceback
    #     traceback.print_exc()
    #     return jsonify({'success': False, 'error': str(e)}), 500

    except Exception as e:
        logging.exception("Error downloading report")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)