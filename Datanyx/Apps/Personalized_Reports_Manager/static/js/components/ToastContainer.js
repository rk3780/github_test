// ── Toast Container ─────────────────────────────────────────────────────────
let _toastId = 0;

function ToastContainer({ toasts, onDismiss }) {
    return (
        <div className="toast-container">
            {toasts.map(t => (
                <div key={t.id} className={`toast toast-${t.type || 'success'}`} onClick={() => onDismiss(t.id)}>
                    <div className="toast-icon">
                        {t.type === 'error' ? '\u2715' : t.type === 'warning' ? '!' : t.type === 'info' ? 'i' : '\u2713'}
                    </div>
                    <div className="toast-msg">{t.msg}</div>
                </div>
            ))}
        </div>
    );
}