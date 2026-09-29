// ── Loading Skeleton ──────────────────────────────────────────────────────────
function Skeleton({ type }) {
    if (type === 'cards') {
        return (
            <div className="skeleton-wrapper">
                <div className="skeleton-row">
                    {[1, 2, 3, 4].map(i => (
                        <div key={i} className="skeleton-card">
                            <div className="skeleton-line skeleton-w40" />
                            <div className="skeleton-line" />
                            <div className="skeleton-line skeleton-w60" />
                        </div>
                    ))}
                </div>
            </div>
        );
    }
    return (
        <div className="skeleton-wrapper">
            {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="skeleton-row">
                    {[1, 2, 3, 4, 5].map(j => <div key={j} className="skeleton-cell" />)}
                </div>
            ))}
        </div>
    );
}