"""Token generation for embedding Databricks AI/BI dashboards.

Uses two strategies depending on available credentials:

1. SCOPED TOKEN (preferred): If a service principal with OAuth credentials is
   configured (DATABRICKS_SP_CLIENT_ID + DATABRICKS_SP_CLIENT_SECRET), generates
   a downscoped token via the 3-step OAuth flow. This token only grants access
   to the specific dashboard being embedded and is safe for browser use.

2. RUNTIME TOKEN (fallback): If no SP credentials are configured, falls back to
   the Databricks SDK's WorkspaceClient runtime token. This works out-of-the-box
   with Databricks Apps but grants the app's full permissions (not scoped).
   To upgrade to scoped tokens later, create a service principal with an OAuth
   secret in the Databricks Admin Console and set the env vars in app.yaml.
"""
import os
import json
import base64
import logging
import urllib.request
import urllib.parse
import urllib.error

logging.basicConfig(level=logging.INFO)

# ── Configuration (from environment variables set in app.yaml) ────────────────
INSTANCE_URL = os.environ.get("DATABRICKS_INSTANCE_URL", "").rstrip("/")
WORKSPACE_ID = os.environ.get("DATABRICKS_WORKSPACE_ID", "")
SP_CLIENT_ID = os.environ.get("DATABRICKS_SP_CLIENT_ID", "")
SP_CLIENT_SECRET = os.environ.get("DATABRICKS_SP_CLIENT_SECRET", "")
DASHBOARD_ID = os.environ.get("DATABRICKS_DASHBOARD_ID", "")
DASHBOARD_ID_DS = os.environ.get("DATABRICKS_DASHBOARD_ID_DS", "")

# Mapping of report IDs to their embedded dashboard IDs
REPORT_DASHBOARD_MAP = {
    25: DASHBOARD_ID,       # Precision Medicine Orders & Results
    4:  DASHBOARD_ID_DS,     # Depression Screening Needed and Completed Report
}


def get_dashboard_id_for_report(report_id):
    """Look up the dashboard ID for a given report ID."""
    dashboard_id = REPORT_DASHBOARD_MAP.get(report_id)
    if not dashboard_id:
        raise Exception(f"No embedded dashboard configured for report ID {report_id}")
    return dashboard_id


def _http_request(url, method="GET", headers=None, body=None):
    """Make an HTTP request using urllib and return parsed JSON."""
    if headers is None:
        headers = {}
    data = None
    if body is not None:
        data = body.encode("utf-8") if isinstance(body, str) else body
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode("utf-8")
            return json.loads(response_data) if response_data else {}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise Exception(f"HTTP {e.code}: {error_body}")
    except Exception as e:
        raise Exception(f"Request failed: {str(e)}")


def _is_sp_configured():
    """Check if service principal OAuth credentials are properly configured."""
    return all([
        SP_CLIENT_ID,
        SP_CLIENT_SECRET,
        not SP_CLIENT_ID.startswith("<"),
        not SP_CLIENT_SECRET.startswith("<"),
    ])


def _get_scoped_token(dashboard_id, external_viewer_id=None, external_value=None):
    """Generate a scoped token via the 3-step OAuth flow.

    Args:
        external_viewer_id: Optional identifier for the external viewer.
        external_value: Optional value associated with the viewer.

    Returns:
        A scoped access token (string) safe for browser use.
    """
    # Step 1: Get an all-api OAuth token using service principal credentials
    basic_auth = base64.b64encode(
        f"{SP_CLIENT_ID}:{SP_CLIENT_SECRET}".encode("utf-8")
    ).decode("utf-8")

    token_url = f"{INSTANCE_URL}/oidc/v1/token?o={WORKSPACE_ID}"
    token_body = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "scope": "all-apis",
    })

    token_response = _http_request(
        token_url,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic_auth}",
        },
        body=token_body,
    )
    oidc_token = token_response.get("access_token")
    if not oidc_token:
        raise Exception("Failed to obtain all-api OAuth token")

    # Step 2: Get tokeninfo for the published dashboard
    tokeninfo_url = (
        f"{INSTANCE_URL}/api/2.0/lakeview/dashboards/{dashboard_id}"
        f"/published/tokeninfo?o={WORKSPACE_ID}"
    )
    if external_viewer_id:
        tokeninfo_url += f"&external_viewer_id={urllib.parse.quote(external_viewer_id)}"
    if external_value:
        tokeninfo_url += f"&external_value={urllib.parse.quote(external_value)}"

    token_info = _http_request(
        tokeninfo_url,
        headers={"Authorization": f"Bearer {oidc_token}"},
    )

    # Step 3: Generate a scoped token using tokeninfo parameters
    authorization_details = token_info.get("authorization_details")
    scoped_params = {k: v for k, v in token_info.items() if k != "authorization_details"}
    scoped_params["grant_type"] = "client_credentials"

    scoped_body = urllib.parse.urlencode(scoped_params)
    if authorization_details:
        scoped_body += "&authorization_details=" + urllib.parse.quote(
            json.dumps(authorization_details)
        )

    scoped_response = _http_request(
        token_url,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic_auth}",
        },
        body=scoped_body,
    )

    scoped_token = scoped_response.get("access_token")
    if not scoped_token:
        raise Exception("Failed to generate scoped token")

    return scoped_token


def _get_runtime_token(dashboard_id):
    """Get the Databricks App's runtime token using the SDK's WorkspaceClient.

    This works with the Databricks App's built-in identity without requiring
    a separate service principal. The token grants the app's full permissions
    (not scoped to a single dashboard).
    """
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()
    auth_headers = w.config.authenticate()
    token = auth_headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise Exception("Failed to obtain runtime token from WorkspaceClient")

    # Verify the app has access to the dashboard via the SDK
    try:
        w.lakeview_embedded.get_published_dashboard_token_info(
            dashboard_id=dashboard_id
        )
    except Exception as e:
        raise Exception(f"Dashboard access check failed: {str(e)}")

    return token


def get_scoped_token(report_id, external_viewer_id=None, external_value=None):
    """Generate a token for embedding a Databricks dashboard.

    Uses scoped token (3-step OAuth flow) if SP credentials are configured,
    otherwise falls back to the Databricks App's runtime token.

    Args:
        report_id: The report ID to look up the correct dashboard.
        external_viewer_id: Optional identifier for the external viewer.
        external_value: Optional value associated with the viewer.

    Returns:
        An access token (string) for the DatabricksDashboard SDK.
    """
    dashboard_id = get_dashboard_id_for_report(report_id)

    if not all([INSTANCE_URL, WORKSPACE_ID, dashboard_id]):
        raise Exception("Missing required environment variables for embedding. "
                        "Ensure DATABRICKS_INSTANCE_URL, DATABRICKS_WORKSPACE_ID, "
                        "and the dashboard ID for report "
                        f"{report_id} are set.")

    if _is_sp_configured():
        return _get_scoped_token(
            dashboard_id,
            external_viewer_id=external_viewer_id,
            external_value=external_value,
        )
    else:
        return _get_runtime_token(dashboard_id)