"""Database utilities for Databricks SQL execution."""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time
import logging

logging.basicConfig(level=logging.INFO)

# Initialize Databricks SDK client
w = WorkspaceClient()


def sanitize_sql(value):
    """Sanitize a string for safe use in SQL queries."""
    if value is None:
        return ''
    return str(value).replace("'", "''")


def get_warehouse_id():
    """Get the first available SQL warehouse."""
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
    """Execute SQL query and return results."""
    try:
        if not WAREHOUSE_ID:
            return {'success': False, 'error': 'No SQL warehouse available'}

        statement = w.statement_execution.execute_statement(
            statement=query,
            warehouse_id=WAREHOUSE_ID
        )

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