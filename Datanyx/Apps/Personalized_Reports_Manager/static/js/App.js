// Personalized Reports Manager - Main App Entry
// All component definitions are in /static/js/components/
// Components: ErrorBoundary, PlotlyChart, IkmFilterSidebar, IkmReportDetail,
//   DepressionScreeningDetail, GenericReportDetail, ToastContainer, Modals, Skeleton

function App() {
    // User context state
    const [currentUser, setCurrentUser] = useState(null);
    const [authMode, setAuthMode] = useState('signin'); // 'signin' or 'signup'
    const [authForm, setAuthForm] = useState({ name: '', practice_name: '', location: '', email: '' });
    const [authError, setAuthError] = useState(null);
    const [authSuccess, setAuthSuccess] = useState(null);
    const [authLoading, setAuthLoading] = useState(false);

    const [activeTab, setActiveTab] = useState('reports');
    const [reports, setReports] = useState([]);
    const [generatedReports, setGeneratedReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [updatingReportId, setUpdatingReportId] = useState(null);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [entriesPerPage, setEntriesPerPage] = useState(15);
    const [currentPage, setCurrentPage] = useState(0);
    const [totalReports, setTotalReports] = useState(0);

    // Reports catalog + detail state
    const [reportCatalog, setReportCatalog] = useState({});
    const [selectedReportId, setSelectedReportId] = useState(null);
    const [reportDetails, setReportDetails] = useState(null);
    const [reportDetailsLoading, setReportDetailsLoading] = useState(false);
    const [reportSearch, setReportSearch] = useState('');

    // Toast notifications
    const [toasts, setToasts] = useState([]);
    const showToast = (msg, type = 'success') => {
        const id = ++_toastId;
        setToasts(prev => [...prev, { id, msg, type }]);
        setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
    };
    const dismissToast = (id) => setToasts(prev => prev.filter(t => t.id !== id));

    // Confirmation modal
    const [confirmModal, setConfirmModal] = useState(null);

    // Edit modal
    const [editModal, setEditModal] = useState(null);
    const [editSaving, setEditSaving] = useState(false);

    // Report filter state
    const [reportFilterParams, setReportFilterParams] = useState('');

    // Dark mode
    const [darkMode, setDarkMode] = useState(() => localStorage.getItem('prn_darkMode') === 'true');
    useEffect(() => {
        document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
        localStorage.setItem('prn_darkMode', darkMode);
    }, [darkMode]);

    // Load saved user from localStorage on mount
    useEffect(() => {
        const savedUser = localStorage.getItem('prn_currentUser');
        if (savedUser) {
            try {
                setCurrentUser(JSON.parse(savedUser));
            } catch(e) {
                localStorage.removeItem('prn_currentUser');
            }
        }
    }, []);

    const handleSignIn = async () => {
        if (!authForm.name || !authForm.practice_name || !authForm.location) {
            setAuthError('Name, Practice Name, and Location are required');
            setAuthSuccess(null);
            return;
        }
        setAuthLoading(true);
        setAuthError(null);
        setAuthSuccess(null);
        try {
            const response = await fetch('/api/signin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: authForm.name,
                    practice_name: authForm.practice_name,
                    location: authForm.location
                })
            });
            const data = await response.json();
            if (data.success) {
                const userData = data.data;
                localStorage.setItem('prn_currentUser', JSON.stringify(userData));
                setCurrentUser(userData);
                setAuthForm({ name: '', practice_name: '', location: '', email: '' });
            } else {
                setAuthError(data.error || 'Sign in failed');
            }
        } catch (err) {
            setAuthError(err.message);
        } finally {
            setAuthLoading(false);
        }
    };

    const handleSignUp = async () => {
        if (!authForm.name || !authForm.practice_name || !authForm.location) {
            setAuthError('Name, Practice Name, and Location are required');
            setAuthSuccess(null);
            return;
        }
        setAuthLoading(true);
        setAuthError(null);
        setAuthSuccess(null);
        try {
            const response = await fetch('/api/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: authForm.name,
                    practice_name: authForm.practice_name,
                    location: authForm.location,
                    email: authForm.email || ''
                })
            });
            const data = await response.json();
            if (data.success) {
                const userData = data.data;
                localStorage.setItem('prn_currentUser', JSON.stringify(userData));
                setCurrentUser(userData);
                setAuthForm({ name: '', practice_name: '', location: '', email: '' });
            } else {
                setAuthError(data.error || 'Sign up failed');
            }
        } catch (err) {
            setAuthError(err.message);
        } finally {
            setAuthLoading(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('prn_currentUser');
        setCurrentUser(null);
        setReports([]);
        setGeneratedReports([]);
    };

    useEffect(() => {
        if (!currentUser) return;
        const timer = setTimeout(() => {
            if (activeTab === 'practice-scheduled-reports') {
                fetchReports();
            } else if (activeTab === 'generated-reports') {
                fetchGeneratedReports();
            }
        }, 300);
        return () => clearTimeout(timer);
    }, [searchTerm, entriesPerPage, currentPage, activeTab, currentUser]);

    useEffect(() => {
        if (!currentUser || activeTab !== 'reports' || selectedReportId) return;
        const timer = setTimeout(() => {
            fetchReportCatalog();
        }, 300);
        return () => clearTimeout(timer);
    }, [reportSearch, activeTab, currentUser, selectedReportId]);

    const fetchReports = async (showRefreshIndicator = false) => {
        try {
            if (reports.length === 0) {
                setLoading(true);
            } else if (showRefreshIndicator) {
                setIsRefreshing(true);
            }
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
            setIsRefreshing(false);
        }
    };

    const fetchGeneratedReports = async (showRefreshIndicator = false) => {
        try {
            if (generatedReports.length === 0) {
                setLoading(true);
            } else if (showRefreshIndicator) {
                setIsRefreshing(true);
            }
            const offset = currentPage * entriesPerPage;
            const response = await fetch(
                `/api/generated-reports?search=${searchTerm}&limit=${entriesPerPage}&offset=${offset}&user_id=${currentUser.user_id}`
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
            setIsRefreshing(false);
        }
    };

    const fetchReportCatalog = async () => {
        try {
            const response = await fetch(`/api/reports?search=${reportSearch}`);
            const data = await response.json();
            if (data.success) {
                setReportCatalog(data.data);
            }
        } catch (err) {
            console.error('Error fetching report catalog:', err);
        }
    };

    const fetchReportDetails = async (reportId) => {
        setReportDetailsLoading(true);
        setReportDetails(null);
        try {
            const response = await fetch(`/api/reports/${reportId}/details?user_id=${currentUser?.user_id || ''}`);
            const data = await response.json();
            if (data.success) {
                setReportDetails(data.data);
            } else {
                setReportDetails(null);
            }
        } catch (err) {
            console.error('Error fetching report details:', err);
            setReportDetails(null);
        } finally {
            setReportDetailsLoading(false);
        }
    };

    const handlePauseToggle = async (reportId, currentStatus) => {
        try {
            setUpdatingReportId(reportId);
            const newStatus = currentStatus === 'Pause' ? 'Paused' : 'Pause';
            
            // Optimistically update the UI
            setReports(prevReports => 
                prevReports.map(r => 
                    r.report_id === reportId 
                        ? { ...r, pause_schedule: newStatus } 
                        : r
                )
            );
            
            const response = await fetch(`/api/scheduled-reports/${reportId}/pause`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pause_schedule: newStatus })
            });
            
            if (!response.ok) {
                // Revert on error
                setReports(prevReports => 
                    prevReports.map(r => 
                        r.report_id === reportId 
                            ? { ...r, pause_schedule: currentStatus } 
                            : r
                    )
                );
                showToast('Failed to update pause status', 'error');
            }
        } catch (err) {
            console.error('Error toggling pause:', err);
            // Revert on error
            setReports(prevReports => 
                prevReports.map(r => 
                    r.report_id === reportId 
                        ? { ...r, pause_schedule: currentStatus } 
                        : r
                )
            );
        } finally {
            setUpdatingReportId(null);
        }
    };

    const handleGenerate = async (reportId) => {
        try {
            setUpdatingReportId(reportId);
            const response = await fetch(`/api/scheduled-reports/${reportId}/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: currentUser.user_id,
                    user_name: currentUser.name
                })
            });
            const data = await response.json();
            
            if (data.success) {
                showToast('Report generated successfully! Check Generated Reports tab.');
                if (activeTab === 'generated-reports') {
                    fetchGeneratedReports(false);
                }
            } else {
                showToast('Error: ' + data.error, 'error');
            }
        } catch (err) {
            showToast('Error generating report: ' + err.message, 'error');
        } finally {
            setUpdatingReportId(null);
        }
    };

    const handleDelete = async (reportId) => {
        try {
            setUpdatingReportId(reportId);
            
            // Optimistically remove from UI
            const deletedReport = reports.find(r => r.report_id === reportId);
            setReports(prevReports => prevReports.filter(r => r.report_id !== reportId));
            setTotalReports(prev => prev - 1);
            
            const response = await fetch(`/api/scheduled-reports/${reportId}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            
            if (data.success) {
                showToast('Report deleted successfully!');
            } else {
                // Revert on error
                setReports(prevReports => [...prevReports, deletedReport].sort((a, b) => a.report_id - b.report_id));
                setTotalReports(prev => prev + 1);
                showToast('Error: ' + data.error, 'error');
            }
        } catch (err) {
            showToast('Error deleting report: ' + err.message, 'error');
            // Fetch fresh data on error
            fetchReports(false);
        } finally {
            setUpdatingReportId(null);
        }
    };

    const handleGeneratedReportDelete = async (reportId) => {
        try {
            setUpdatingReportId(reportId);
            
            // Optimistically remove from UI
            const deletedReport = generatedReports.find(r => r.report_id === reportId);
            setGeneratedReports(prevReports => prevReports.filter(r => r.report_id !== reportId));
            setTotalReports(prev => prev - 1);
            
            const response = await fetch(`/api/generated-reports/${reportId}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            
            if (data.success) {
                showToast('Generated report deleted successfully!');
            } else {
                // Revert on error
                setGeneratedReports(prevReports => [...prevReports, deletedReport].sort((a, b) => b.generated_on - a.generated_on));
                setTotalReports(prev => prev + 1);
                showToast('Error: ' + data.error, 'error');
            }
        } catch (err) {
            showToast('Error deleting generated report: ' + err.message, 'error');
            // Fetch fresh data on error
            fetchGeneratedReports(false);
        } finally {
            setUpdatingReportId(null);
        }
    };

    const handleDownload = async (reportId) => {
        try {
            // Fetch the file from the backend
            const response = await fetch(`/api/generated-reports/${reportId}/download`);
            
            if (!response.ok) {
                showToast('Error downloading report', 'error');
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
            showToast('Error downloading report: ' + err.message, 'error');
        }
    };

    const handleEditSchedule = async (form) => {
        setEditSaving(true);
        try {
            const response = await fetch(`/api/scheduled-reports/${editModal.report.report_id}/edit`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    schedule_name: form.schedule_name,
                    frequency: form.frequency,
                    scheduled_time: form.scheduled_time,
                    user_name: currentUser.name,
                })
            });
            const data = await response.json();
            if (data.success) {
                showToast('Schedule updated successfully');
                setEditModal(null);
                fetchReports(false);
            } else {
                showToast(data.error || 'Failed to update schedule', 'error');
            }
        } catch (err) {
            showToast('Error updating schedule: ' + err.message, 'error');
        } finally {
            setEditSaving(false);
        }
    };

    const handleExportCSV = async (reportId) => {
        try {
            const response = await fetch(`/api/reports/${reportId}/export`);
            if (!response.ok) { showToast('Error exporting report', 'error'); return; }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            const cd = response.headers.get('Content-Disposition');
            link.download = cd ? cd.match(/filename="?(.+?)"?$/i)?.[1] || `report_${reportId}.csv` : `report_${reportId}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            showToast('Report exported successfully');
        } catch (err) {
            showToast('Error exporting report: ' + err.message, 'error');
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

    // Login Screen
    if (!currentUser) {
        return (
            <div className="login-container">
                <div className="login-card">
                    <h1 className="login-title">Personalized Reports Manager</h1>
                    <p className="login-subtitle">Sign in to your account or create a new one</p>
                    
                    <div className="login-tabs">
                        <button 
                            className={`login-tab ${authMode === 'signin' ? 'active' : ''}`}
                            onClick={() => { setAuthMode('signin'); setAuthError(null); setAuthSuccess(null); }}
                        >Sign In</button>
                        <button 
                            className={`login-tab ${authMode === 'signup' ? 'active' : ''}`}
                            onClick={() => { setAuthMode('signup'); setAuthError(null); setAuthSuccess(null); }}
                        >Sign Up</button>
                    </div>

                    {authError && <div className="login-error">{authError}</div>}
                    {authSuccess && <div className="login-success">{authSuccess}</div>}

                    <div className="register-form">
                        <input
                            type="text"
                            placeholder="Full Name *"
                            value={authForm.name}
                            onChange={(e) => setAuthForm({...authForm, name: e.target.value})}
                            className="login-input"
                        />
                        <input
                            type="text"
                            placeholder="Practice Name *"
                            value={authForm.practice_name}
                            onChange={(e) => setAuthForm({...authForm, practice_name: e.target.value})}
                            className="login-input"
                        />
                        <input
                            type="text"
                            placeholder="Location *"
                            value={authForm.location}
                            onChange={(e) => setAuthForm({...authForm, location: e.target.value})}
                            className="login-input"
                        />
                        {authMode === 'signup' && (
                            <input
                                type="email"
                                placeholder="Email (optional)"
                                value={authForm.email}
                                onChange={(e) => setAuthForm({...authForm, email: e.target.value})}
                                className="login-input"
                            />
                        )}
                        <button 
                            className="login-submit-btn"
                            onClick={authMode === 'signin' ? handleSignIn : handleSignUp}
                            disabled={authLoading}
                        >
                            {authLoading 
                                ? (authMode === 'signin' ? 'Signing in...' : 'Signing up...') 
                                : (authMode === 'signin' ? 'Sign In' : 'Sign Up')
                            }
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="app-container">
            {/* User Header */}
            <div className="user-header">
                <div className="user-header-info">
                    <div className="user-header-avatar">{currentUser.name.charAt(0)}</div>
                    <div>
                        <div className="user-header-name">{currentUser.name}</div>
                        <div className="user-header-details">{currentUser.practice_name} - {currentUser.location}</div>
                    </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <button className="theme-toggle-btn" onClick={() => setDarkMode(!darkMode)} title="Toggle Dark Mode">
                        {darkMode ? '\u2600' : '\u263e'}
                    </button>
                    <button className="logout-btn" onClick={handleLogout}>Logout</button>
                </div>
            </div>

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
                            <button 
                                className="refresh-btn" 
                                onClick={() => fetchReports(true)}
                                disabled={isRefreshing}
                            >
                                {isRefreshing ? '⟳' : '↻'}
                            </button>
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
                            {isRefreshing && (
                                <div style={{ textAlign: 'center', padding: '8px', background: '#f0f0f0', fontSize: '14px' }}>
                                    ⟳ Refreshing...
                                </div>
                            )}
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
                                                    disabled={updatingReportId === report.report_id}
                                                    style={{ opacity: updatingReportId === report.report_id ? 0.6 : 1 }}
                                                >
                                                    {updatingReportId === report.report_id ? '⟳' : (report.pause_schedule === 'Paused' ? '⏸ Paused' : '⏸ Pause')}
                                                </button>
                                            </td>
                                            <td>
                                                <button 
                                                    className="generate-btn"
                                                    onClick={() => handleGenerate(report.report_id)}
                                                    disabled={updatingReportId === report.report_id}
                                                    style={{ opacity: updatingReportId === report.report_id ? 0.6 : 1 }}
                                                >
                                                    {updatingReportId === report.report_id ? '⟳' : 'GENERATE'}
                                                </button>
                                            </td>
                                            <td>
                                                <button className="icon-btn edit-btn" onClick={() => setEditModal({ report })}>✏️</button>
                                            </td>
                                            <td>
                                                <button 
                                                    className="icon-btn delete-btn"
                                                    onClick={() => setConfirmModal({ message: 'Are you sure you want to delete this scheduled report?', confirmLabel: 'Delete', onConfirm: () => { setConfirmModal(null); handleDelete(report.report_id); } })}
                                                    disabled={updatingReportId === report.report_id}
                                                    style={{ opacity: updatingReportId === report.report_id ? 0.6 : 1 }}
                                                >
                                                    {updatingReportId === report.report_id ? '⟳' : '🗑️'}
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

            {activeTab === 'reports' && !selectedReportId && (
                <div className="reports-catalog-container">
                    {/* Search Row - matches iknowmed-reports look */}
                    <div className="ikm-search-row">
                        <div className="ikm-search-label">Reports</div>
                        <div className="ikm-report-search">
                            <input
                                type="text"
                                placeholder="Search Reports..."
                                value={reportSearch}
                                onChange={(e) => setReportSearch(e.target.value)}
                            />
                        </div>
                    </div>

                    {/* Content Area */}
                    <div className="ikm-content">
                        {Object.keys(reportCatalog).length === 0 ? (
                            <div className="loading">Loading reports...</div>
                        ) : Object.values(reportCatalog).every(reports => reports.length === 0) ? (
                            <div className="ikm-no-results">No reports match "{reportSearch}"</div>
                        ) : (
                            <div className="ikm-categories">
                                {Object.entries(reportCatalog).map(([category, reports]) =>
                                    reports.length > 0 && (
                                        <div className="ikm-category-card" key={category}>
                                            <div className="ikm-category-header">{category} <span className="ikm-category-count">{reports.length}</span></div>
                                            <div className="ikm-report-list">
                                                {reports.map(r => (
                                                    <div
                                                        className="ikm-report-item"
                                                        key={r.id}
                                                        onClick={() => {
                                                            setSelectedReportId(r.id);
                                                            fetchReportDetails(r.id);
                                                        }}
                                                    >
                                                        <span className="ikm-report-num">{r.id}</span>
                                                        {r.name}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )
                                )}
                            </div>
                        )}
                    </div>

                    {/* Footer - matches iknowmed-reports look */}
                    <div className="ikm-footer">
                        iKnowMed&trade; Generation 2 &mdash; {Object.values(reportCatalog).reduce((sum, reports) => sum + reports.length, 0)} Reports Available
                    </div>
                </div>
            )}

            {activeTab === 'reports' && selectedReportId && (
                <div className="report-detail-page">
                    {/* Breadcrumb */}
                    <div className="report-detail-breadcrumb">
                        <span
                            className="breadcrumb-link"
                            onClick={() => {
                                setSelectedReportId(null);
                                setReportDetails(null);
                            }}
                        >Reports</span>
                        <span className="breadcrumb-sep">&rsaquo;</span>
                        <span className="breadcrumb-current">{reportDetails?.report?.name || 'Loading...'}</span>
                    </div>

                    {reportDetailsLoading ? (
                        <Skeleton type="cards" />
                    ) : reportDetails ? (
                        <ErrorBoundary>
                        {reportDetails.in_progress ? (
                            <div className="ikm-in-progress">
                                <div className="ikm-in-progress-icon">{'\u23f3'}</div>
                                <h2 className="ikm-in-progress-title">{reportDetails.report.name}</h2>
                                <p className="ikm-in-progress-text">This report is currently in progress. Detailed analytics and charts will be available soon.</p>
                                <button className="ikm-btn-back" onClick={() => { setSelectedReportId(null); setReportDetails(null); }}>{'\u2190'} Back to Reports</button>
                            </div>
                        ) : reportDetails.report_type === 'depression_screening' ? (
                            <DepressionScreeningDetail
                                data={reportDetails}
                                onBack={() => {
                                    setSelectedReportId(null);
                                    setReportDetails(null);
                                }}
                            />
                        ) : reportDetails.report_type === 'embedded_dashboard' ? (
                            <EmbeddedDashboard
                                report={reportDetails.report}
                                onBack={() => {
                                    setSelectedReportId(null);
                                    setReportDetails(null);
                                }}
                                currentUser={currentUser}
                                onNotify={showToast}
                                onGenerate={async () => {
                                    if (!currentUser) { showToast('Please sign in first', 'warning'); return; }
                                    try {
                                        const response = await fetch(`/api/reports/${selectedReportId}/generate`, {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({ user_id: currentUser.user_id, user_name: currentUser.name })
                                        });
                                        const result = await response.json();
                                        if (result.success) {
                                            showToast('Report generated! Check the Generated Reports tab.');
                                        } else {
                                            showToast('Error: ' + result.error, 'error');
                                        }
                                    } catch (err) {
                                        showToast('Error generating report: ' + err.message, 'error');
                                    }
                                }}
                                onSchedule={async (scheduleData) => {
                                    if (!currentUser) { showToast('Please sign in first', 'warning'); return; }
                                    const response = await fetch(`/api/reports/${selectedReportId}/schedule`, {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({ user_id: currentUser.user_id, user_name: currentUser.name, ...scheduleData })
                                    });
                                    const result = await response.json();
                                    if (result.success) {
                                        showToast('Report scheduled! Check the Practice Scheduled Reports tab.');
                                    } else {
                                        throw new Error(result.error || 'Scheduling failed');
                                    }
                                }}
                            />
                        ) : reportDetails.report_type && reportDetails.report_type.startsWith('generic_') ? (
                            <GenericReportDetail
                                data={reportDetails}
                                onBack={() => {
                                    setSelectedReportId(null);
                                    setReportDetails(null);
                                }}
                                currentUser={currentUser}
                                onGenerate={async () => {
                                    if (!currentUser) { showToast('Please sign in first', 'warning'); return; }
                                    try {
                                        const response = await fetch(`/api/reports/${selectedReportId}/generate`, {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({ user_id: currentUser.user_id, user_name: currentUser.name })
                                        });
                                        const result = await response.json();
                                        if (result.success) {
                                            showToast('Report generated! Check the Generated Reports tab.');
                                        } else {
                                            showToast('Error: ' + result.error, 'error');
                                        }
                                    } catch (err) {
                                        showToast('Error generating report: ' + err.message, 'error');
                                    }
                                }}
                                onSchedule={async (scheduleData) => {
                                    if (!currentUser) { showToast('Please sign in first', 'warning'); return; }
                                    const response = await fetch(`/api/reports/${selectedReportId}/schedule`, {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({ user_id: currentUser.user_id, user_name: currentUser.name, ...scheduleData })
                                    });
                                    const result = await response.json();
                                    if (result.success) {
                                        showToast('Report scheduled! Check the Practice Scheduled Reports tab.');
                                    } else {
                                        throw new Error(result.error || 'Scheduling failed');
                                    }
                                }}
                                onExport={() => handleExportCSV(selectedReportId)}
                            />
                        ) : (
                            <IkmReportDetail
                                data={reportDetails}
                                onBack={() => {
                                    setSelectedReportId(null);
                                    setReportDetails(null);
                                }}
                                currentUser={currentUser}
                                onNotify={showToast}
                                onGenerateSuccess={() => {
                                    setSelectedReportId(null);
                                    setReportDetails(null);
                                    setActiveTab('generated-reports');
                                }}
                                onScheduleSuccess={() => {
                                    setSelectedReportId(null);
                                    setReportDetails(null);
                                    setActiveTab('practice-scheduled-reports');
                                }}
                            />
                        )}
                        </ErrorBoundary>
                    ) : (
                        <div className="error">Failed to load report details. Please try again.</div>
                    )}
                </div>
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
                            <button 
                                className="refresh-btn" 
                                onClick={() => fetchGeneratedReports(true)}
                                disabled={isRefreshing}
                            >
                                {isRefreshing ? '⟳' : '↻'}
                            </button>
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
                            {isRefreshing && (
                                <div style={{ textAlign: 'center', padding: '8px', background: '#f0f0f0', fontSize: '14px' }}>
                                    ⟳ Refreshing...
                                </div>
                            )}
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
                                                    disabled={updatingReportId === report.report_id}
                                                    style={{ opacity: updatingReportId === report.report_id ? 0.6 : 1 }}
                                                >
                                                    {updatingReportId === report.report_id ? '⟳' : '📥'}
                                                </button>
                                            </td>
                                            <td>
                                                <button 
                                                    className="icon-btn delete-btn"
                                                    onClick={() => setConfirmModal({ message: 'Are you sure you want to delete this generated report?', confirmLabel: 'Delete', onConfirm: () => { setConfirmModal(null); handleGeneratedReportDelete(report.report_id); } })}
                                                    title="Delete Report"
                                                    disabled={updatingReportId === report.report_id}
                                                    style={{ opacity: updatingReportId === report.report_id ? 0.6 : 1 }}
                                                >
                                                    {updatingReportId === report.report_id ? '⟳' : '🗑️'}
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

            {/* Toast Notifications */}
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />

            {/* Confirmation Modal */}
            {confirmModal && (
                <ConfirmModal
                    message={confirmModal.message}
                    confirmLabel={confirmModal.confirmLabel}
                    onConfirm={confirmModal.onConfirm}
                    onCancel={() => setConfirmModal(null)}
                />
            )}

            {/* Edit Schedule Modal */}
            {editModal && (
                <EditScheduleModal
                    report={editModal.report}
                    onSave={handleEditSchedule}
                    onCancel={() => setEditModal(null)}
                    saving={editSaving}
                />
            )}
        </div>
    );
}

// Render the app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);