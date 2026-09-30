// ── Embedded Databricks Dashboard ───────────────────────────────────────────
// Renders a Databricks AI/BI dashboard using the @databricks/aibi-client SDK.
// The scoped token is fetched from the Flask backend (never exposed in the frontend).
// The aibi-client library is loaded as an ES module in index.html and exposed
// globally as window.DatabricksDashboardSDK.

function EmbeddedDashboard({ report, onBack, currentUser, onGenerate, onSchedule, onNotify }) {
    const containerRef = useRef(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Force container to refit on window resize
    useEffect(() => {
        const handleResize = () => {
            if (containerRef.current) {
                containerRef.current.style.height = '100%';
            }
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    useEffect(() => {
        let dashboard = null;
        let isMounted = true;

        async function loadDashboard() {
            try {
                setLoading(true);
                setError(null);

                // Fetch the scoped token from the backend
                const params = new URLSearchParams();
                if (currentUser?.user_id) params.set('external_viewer_id', String(currentUser.user_id));
                if (currentUser?.name) params.set('external_value', currentUser.name);

                const response = await fetch(`/api/reports/${report.id}/embed-token?${params.toString()}`);
                const data = await response.json();

                if (!data.success) {
                    throw new Error(data.error || 'Failed to get embed token');
                }

                if (!isMounted) return;

                // Wait for the SDK to be loaded (loaded as ES module in index.html)
                let attempts = 0;
                while (!window.DatabricksDashboardSDK && attempts < 50) {
                    await new Promise(resolve => setTimeout(resolve, 100));
                    attempts++;
                }
                if (!window.DatabricksDashboardSDK) {
                    throw new Error('Databricks dashboard SDK failed to load');
                }

                if (!isMounted || !containerRef.current) return;

                // Initialize the embedded dashboard
                const { DatabricksDashboard } = window.DatabricksDashboardSDK;
                dashboard = new DatabricksDashboard({
                    instanceUrl: data.instance_url,
                    workspaceId: data.workspace_id,
                    dashboardId: data.dashboard_id,
                    token: data.token,
                    container: containerRef.current,
                    config: {
                        version: 1,
                        hideDatabricksLogo: true,
                    },
                });
                await dashboard.initialize();

                if (isMounted) setLoading(false);
            } catch (err) {
                if (isMounted) {
                    setError(err.message);
                    setLoading(false);
                    if (onNotify) onNotify('Error loading dashboard: ' + err.message, 'error');
                }
            }
        }

        loadDashboard();

        return () => {
            isMounted = false;
            // Clean up the dashboard instance if the SDK supports it
            if (dashboard && typeof dashboard.destroy === 'function') {
                dashboard.destroy();
            }
            // Clear the container
            if (containerRef.current) {
                containerRef.current.innerHTML = '';
            }
        };
    }, [report.id]);

    return (
        <div className="ikm-report-detail-wrapper" style={{ minHeight: 'calc(100vh - 165px)' }}>
            <div
                className="ikm-report-detail-main"
                style={{
                    display: 'flex',
                    flexDirection: 'column',
                    padding: '8px 12px',
                    height: 'calc(100vh - 165px)',
                    overflow: 'hidden',
                }}
            >
                <div className="ikm-detail-back-bar" style={{ flexShrink: 0, marginBottom: '4px' }}>
                    <span className="ikm-detail-back-link" onClick={onBack}>{'\u2190'} Back to Reports</span>
                </div>
                <h2 className="report-detail-title" style={{ fontSize: '18px', margin: '2px 0 0' }}>{report.name}</h2>
                <div className="report-detail-subtitle" style={{ margin: '0 0 8px' }}>Embedded Databricks AI/BI Dashboard</div>

                {loading && (
                    <div style={{ padding: '40px', textAlign: 'center', color: '#666', fontSize: '16px', flex: 1 }}>
                        Loading dashboard...
                    </div>
                )}
                {error && (
                    <div style={{ padding: '40px', textAlign: 'center', flex: 1 }}>
                        <h3 style={{ color: '#e74c3c', marginBottom: '10px' }}>Failed to load dashboard</h3>
                        <p style={{ color: '#666', fontSize: '14px' }}>{error}</p>
                    </div>
                )}
                {/* Dashboard renders inside this container — fills all remaining space */}
                <div
                    ref={containerRef}
                    id="databricks-dashboard-container"
                    style={{
                        width: '100%',
                        flex: 1,
                        minHeight: 0,
                        display: loading || error ? 'none' : 'block',
                    }}
                />
            </div>
        </div>
    );
}