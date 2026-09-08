// RunStatus Component
window.RunStatus = function({ runStatus }) {
    if (!runStatus) return null;
    
    const getStatusBadge = (state) => {
        if (!state) return null;
        const stateUpper = state.toUpperCase();
        
        if (stateUpper === 'SUCCESS' || stateUpper === 'TERMINATED') {
            return <span className="badge badge-success">{state}</span>;
        } else if (stateUpper === 'RUNNING') {
            return <span className="badge badge-running">{state}</span>;
        } else if (stateUpper === 'PENDING') {
            return <span className="badge badge-pending">{state}</span>;
        } else {
            return <span className="badge badge-error">{state}</span>;
        }
    };
    
    return (
        <div className="status-card">
            <h3>Job Run Status</h3>
            <div className="status-item">
                <span className="status-label">Run ID:</span>
                <a 
                    href={runStatus.run_page_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="run-link"
                >
                    {runStatus.run_id}
                </a>
            </div>
            <div className="status-item">
                <span className="status-label">Job ID:</span>
                <span className="status-value">{runStatus.job_id}</span>
            </div>
            <div className="status-item">
                <span className="status-label">State:</span>
                {getStatusBadge(runStatus.state)}
            </div>
            {runStatus.start_time && (
                <div className="status-item">
                    <span className="status-label">Start Time:</span>
                    <span className="status-value">
                        {new Date(runStatus.start_time).toLocaleString()}
                    </span>
                </div>
            )}
            {runStatus.end_time && (
                <div className="status-item">
                    <span className="status-label">End Time:</span>
                    <span className="status-value">
                        {new Date(runStatus.end_time).toLocaleString()}
                    </span>
                </div>
            )}
        </div>
    );
};