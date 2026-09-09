// Main App Component
const { useState, useEffect } = React;

function App() {
    const [activeTab, setActiveTab] = useState('practice-scheduled-reports');
    const [reports, setReports] = useState([]);
    const [generatedReports, setGeneratedReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [entriesPerPage, setEntriesPerPage] = useState(15);
    const [currentPage, setCurrentPage] = useState(0);
    const [totalReports, setTotalReports] = useState(0);

    useEffect(() => {
        const timer = setTimeout(() => {
            if (activeTab === 'practice-scheduled-reports') {
                fetchReports();
            } else if (activeTab === 'generated-reports') {
                fetchGeneratedReports();
            }
        }, 300);
        return () => clearTimeout(timer);
    }, [searchTerm, entriesPerPage, currentPage, activeTab]);

    const fetchReports = async () => {
        try {
            setLoading(true);
            const offset = currentPage * entriesPerPage;
            const response = await fetch(
                `/api/scheduled-reports?search=${searchTerm}&limit=${entriesPerPage}&offset=${offset}`
            );
            const data = await response.json();
            
            if (data.success) {
                setReports(data.data);
                setTotalReports(data.total);
                setError(null);
            } else {
                setError(data.error);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const fetchGeneratedReports = async () => {
        try {
            setLoading(true);
            const offset = currentPage * entriesPerPage;
            const response = await fetch(
                `/api/generated-reports?search=${searchTerm}&limit=${entriesPerPage}&offset=${offset}`
            );
            const data = await response.json();
            
            if (data.success) {
                setGeneratedReports(data.data);
                setTotalReports(data.total);
                setError(null);
            } else {
                setError(data.error);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handlePauseToggle = async (reportId, currentStatus) => {
        try {
            const newStatus = currentStatus === 'Pause' ? 'Paused' : 'Pause';
            const response = await fetch(`/api/scheduled-reports/${reportId}/pause`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pause_schedule: newStatus })
            });
            
            if (response.ok) {
                fetchReports();
            }
        } catch (err) {
            console.error('Error toggling pause:', err);
        }
    };

    const handleGenerate = async (reportId) => {
        try {
            const response = await fetch(`/api/scheduled-reports/${reportId}/generate`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                alert('Report generated successfully! Check the Generated Reports tab.');
                // Refresh generated reports if on that tab
                if (activeTab === 'generated-reports') {
                    fetchGeneratedReports();
                }
            } else {
                alert('Error: ' + data.error);
            }
        } catch (err) {
            alert('Error generating report: ' + err.message);
        }
    };

    const handleDelete = async (reportId) => {
        if (!confirm('Are you sure you want to delete this scheduled report?')) return;
        
        try {
            const response = await fetch(`/api/scheduled-reports/${reportId}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            
            if (data.success) {
                alert('Report deleted successfully!');
                fetchReports();
            } else {
                alert('Error: ' + data.error);
            }
        } catch (err) {
            alert('Error deleting report: ' + err.message);
        }
    };

    const handleGeneratedReportDelete = async (reportId) => {
        if (!confirm('Are you sure you want to delete this generated report?')) return;
        
        try {
            const response = await fetch(`/api/generated-reports/${reportId}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            
            if (data.success) {
                alert('Generated report deleted successfully!');
                fetchGeneratedReports();
            } else {
                alert('Error: ' + data.error);
            }
        } catch (err) {
            alert('Error deleting generated report: ' + err.message);
        }
    };

    const handleDownload = async (reportId) => {
        try {
            // Fetch the file from the backend
            const response = await fetch(`/api/generated-reports/${reportId}/download`);
            
            if (!response.ok) {
                alert('Error downloading report');
                return;
            }
            
            // Get the filename from the Content-Disposition header if available
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `report_${reportId}.txt`;
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?(.+?)"?$/i);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                }
            }
            
            // Create a blob from the response
            const blob = await response.blob();
            
            // Create a temporary link and trigger download
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (err) {
            alert('Error downloading report: ' + err.message);
        }
    };

    const formatDate = (timestamp) => {
        if (!timestamp) return 'N/A';
        const date = new Date(timestamp);
        return date.toLocaleString('en-US', { 
            month: '2-digit', 
            day: '2-digit', 
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
    };

    const totalPages = Math.ceil(totalReports / entriesPerPage);

    return (
        <div className="app-container">
            {/* Tab Navigation */}
            <div className="tabs">
                <button 
                    className={`tab ${activeTab === 'reports' ? 'active' : ''}`}
                    onClick={() => setActiveTab('reports')}
                >
                    Reports
                </button>
                <button 
                    className={`tab ${activeTab === 'generated-reports' ? 'active' : ''}`}
                    onClick={() => setActiveTab('generated-reports')}
                >
                    Generated Reports
                </button>
                <button 
                    className={`tab ${activeTab === 'practice-scheduled-reports' ? 'active' : ''}`}
                    onClick={() => setActiveTab('practice-scheduled-reports')}
                >
                    Practice Scheduled Reports
                </button>
            </div>

            {/* Content */}
            {activeTab === 'practice-scheduled-reports' && (
                <div className="table-container">
                    {/* Controls */}
                    <div className="table-controls">
                        <div className="left-controls">
                            <input 
                                type="text" 
                                placeholder="Search..."
                                value={searchTerm}
                                onChange={(e) => {
                                    setSearchTerm(e.target.value);
                                    setCurrentPage(0);
                                }}
                                className="search-input"
                            />
                            <button className="search-btn">🔍</button>
                            <button className="refresh-btn" onClick={fetchReports}>↻</button>
                        </div>
                        <div className="right-controls">
                            <label>Show</label>
                            <select 
                                value={entriesPerPage} 
                                onChange={(e) => {
                                    setEntriesPerPage(Number(e.target.value));
                                    setCurrentPage(0);
                                }}
                            >
                                <option value={10}>10</option>
                                <option value={15}>15</option>
                                <option value={25}>25</option>
                                <option value={50}>50</option>
                            </select>
                            <label>Entries</label>
                        </div>
                    </div>

                    {/* Table */}
                    {loading ? (
                        <div className="loading">Loading...</div>
                    ) : error ? (
                        <div className="error">Error: {error}</div>
                    ) : (
                        <>
                            <table className="reports-table">
                                <thead>
                                    <tr>
                                        <th>Report Category</th>
                                        <th>Report Title</th>
                                        <th>Schedule Name</th>
                                        <th>Scheduled By</th>
                                        <th>Scheduled Time</th>
                                        <th>Frequency</th>
                                        <th>Updated On (by)</th>
                                        <th>Last Delivery</th>
                                        <th>Pause Schedule</th>
                                        <th>Action</th>
                                        <th>Edit</th>
                                        <th>Delete</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {reports.map((report) => (
                                        <tr key={report.report_id}>
                                            <td>{report.report_category}</td>
                                            <td>{report.report_title}</td>
                                            <td>{report.schedule_name}</td>
                                            <td>{report.scheduled_by || 'N/A'}</td>
                                            <td>{formatDate(report.scheduled_time)}</td>
                                            <td>{report.frequency}</td>
                                            <td>{report.updated_on_by || 'N/A'}</td>
                                            <td>{formatDate(report.last_delivery) || 'Yet to Deliver'}</td>
                                            <td>
                                                <button 
                                                    className={`pause-btn ${report.pause_schedule === 'Paused' ? 'paused' : ''}`}
                                                    onClick={() => handlePauseToggle(report.report_id, report.pause_schedule)}
                                                >
                                                    {report.pause_schedule === 'Paused' ? '⏸ Paused' : '⏸ Pause'}
                                                </button>
                                            </td>
                                            <td>
                                                <button 
                                                    className="generate-btn"
                                                    onClick={() => handleGenerate(report.report_id)}
                                                >
                                                    GENERATE
                                                </button>
                                            </td>
                                            <td>
                                                <button className="icon-btn edit-btn">✏️</button>
                                            </td>
                                            <td>
                                                <button 
                                                    className="icon-btn delete-btn"
                                                    onClick={() => handleDelete(report.report_id)}
                                                >
                                                    🗑️
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>

                            {/* Pagination */}
                            <div className="pagination">
                                <span>Showing {currentPage * entriesPerPage + 1} to {Math.min((currentPage + 1) * entriesPerPage, totalReports)} of {totalReports} entries</span>
                                <div className="pagination-controls">
                                    <button 
                                        disabled={currentPage === 0}
                                        onClick={() => setCurrentPage(currentPage - 1)}
                                    >
                                        Previous
                                    </button>
                                    <button 
                                        disabled={currentPage >= totalPages - 1}
                                        onClick={() => setCurrentPage(currentPage + 1)}
                                    >
                                        Next
                                    </button>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            )}

            {activeTab === 'reports' && (
                <div className="placeholder">Reports tab - Coming soon</div>
            )}

            {activeTab === 'generated-reports' && (
                <div className="table-container">
                    {/* Controls */}
                    <div className="table-controls">
                        <div className="left-controls">
                            <input 
                                type="text" 
                                placeholder="Search..."
                                value={searchTerm}
                                onChange={(e) => {
                                    setSearchTerm(e.target.value);
                                    setCurrentPage(0);
                                }}
                                className="search-input"
                            />
                            <button className="search-btn">🔍</button>
                            <button className="refresh-btn" onClick={fetchGeneratedReports}>↻</button>
                        </div>
                        <div className="right-controls">
                            <label>Show</label>
                            <select 
                                value={entriesPerPage} 
                                onChange={(e) => {
                                    setEntriesPerPage(Number(e.target.value));
                                    setCurrentPage(0);
                                }}
                            >
                                <option value={10}>10</option>
                                <option value={15}>15</option>
                                <option value={25}>25</option>
                                <option value={50}>50</option>
                            </select>
                            <label>Entries</label>
                        </div>
                    </div>

                    {/* Table */}
                    {loading ? (
                        <div className="loading">Loading...</div>
                    ) : error ? (
                        <div className="error">Error: {error}</div>
                    ) : (
                        <>
                            <table className="reports-table">
                                <thead>
                                    <tr>
                                        <th>Report Category</th>
                                        <th>Report Title</th>
                                        <th>Generated By</th>
                                        <th>Generated On</th>
                                        <th>Report Type</th>
                                        <th>Schedule Name</th>
                                        <th>Status</th>
                                        <th>Download</th>
                                        <th>Delete</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {generatedReports.map((report) => (
                                        <tr key={report.report_id}>
                                            <td>{report.report_category}</td>
                                            <td>{report.report_title}</td>
                                            <td>{report.generated_by || 'N/A'}</td>
                                            <td>{formatDate(report.generated_on)}</td>
                                            <td>{report.report_type}</td>
                                            <td>{report.schedule_name || 'N/A'}</td>
                                            <td>{report.status}</td>
                                            <td>
                                                <button 
                                                    className="icon-btn download-btn"
                                                    onClick={() => handleDownload(report.report_id)}
                                                    title="Download Report"
                                                >
                                                    📥
                                                </button>
                                            </td>
                                            <td>
                                                <button 
                                                    className="icon-btn delete-btn"
                                                    onClick={() => handleGeneratedReportDelete(report.report_id)}
                                                    title="Delete Report"
                                                >
                                                    🗑️
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>

                            {/* Pagination */}
                            <div className="pagination">
                                <span>Showing {currentPage * entriesPerPage + 1} to {Math.min((currentPage + 1) * entriesPerPage, totalReports)} of {totalReports} entries</span>
                                <div className="pagination-controls">
                                    <button 
                                        disabled={currentPage === 0}
                                        onClick={() => setCurrentPage(currentPage - 1)}
                                    >
                                        Previous
                                    </button>
                                    <button 
                                        disabled={currentPage >= totalPages - 1}
                                        onClick={() => setCurrentPage(currentPage + 1)}
                                    >
                                        Next
                                    </button>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            )}            
        </div>
    );
}

// Render the app
ReactDOM.render(<App />, document.getElementById('root'));