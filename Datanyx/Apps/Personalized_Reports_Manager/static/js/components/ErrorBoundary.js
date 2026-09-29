// ── Error Boundary ──────────────────────────────────────────────────────────
const { useState, useEffect, useRef, Component } = React;

class ErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }
    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }
    componentDidCatch(error, info) {
        console.error('ErrorBoundary caught:', error, info);
    }
    render() {
        if (this.state.hasError) {
            return (
                <div style={{ padding: '40px', textAlign: 'center' }}>
                    <h3 style={{ color: '#e74c3c' }}>Something went wrong rendering this page.</h3>
                    <p style={{ color: '#666', fontSize: '14px' }}>{String(this.state.error)}</p>
                    <button onClick={() => this.setState({ hasError: false, error: null })}
                        style={{ marginTop: '16px', padding: '8px 20px', cursor: 'pointer', border: '1px solid #4a90d9', background: 'white', color: '#4a90d9', borderRadius: '4px' }}>
                        Try Again
                    </button>
                </div>
            );
        }
        return this.props.children;
    }
}