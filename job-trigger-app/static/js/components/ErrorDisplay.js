// ErrorDisplay Component
window.ErrorDisplay = function({ error }) {
    if (!error) return null;
    
    return (
        <div className="error">
            <strong>Error:</strong> {error}
        </div>
    );
};