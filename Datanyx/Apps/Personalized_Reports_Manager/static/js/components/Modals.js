// ── Confirmation Modal ────────────────────────────────────────────────────────
function ConfirmModal({ message, confirmLabel, onConfirm, onCancel }) {
    return (
        <div className="confirm-modal-overlay" onClick={onCancel}>
            <div className="confirm-modal" onClick={(e) => e.stopPropagation()}>
                <div className="confirm-modal-icon">{'\u26a0'}</div>
                <div className="confirm-modal-message">{message}</div>
                <div className="confirm-modal-actions">
                    <button className="confirm-btn-cancel" onClick={onCancel}>Cancel</button>
                    <button className="confirm-btn-delete" onClick={onConfirm}>{confirmLabel || 'Confirm'}</button>
                </div>
            </div>
        </div>
    );
}

// ── Edit Schedule Modal ──────────────────────────────────────────────────────
function EditScheduleModal({ report, onSave, onCancel, saving }) {
    const [form, setForm] = useState({
        schedule_name: report?.schedule_name || '',
        frequency: report?.frequency || 'Weekly',
        scheduled_time: report?.scheduled_time ? new Date(report.scheduled_time).toISOString().slice(0, 16) : ''
    });
    return (
        <div className="confirm-modal-overlay" onClick={() => !saving && onCancel()}>
            <div className="confirm-modal edit-modal" onClick={(e) => e.stopPropagation()}>
                <div className="edit-modal-header">
                    <h3>Edit Schedule</h3>
                    <button className="confirm-btn-cancel" onClick={() => !saving && onCancel()}>{'\u00d7'}</button>
                </div>
                <div style={{ padding: '20px' }}>
                    <div style={{ marginBottom: '16px' }}>
                        <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '6px', color: '#666' }}>Schedule Name</label>
                        <input type="text" value={form.schedule_name} onChange={(e) => setForm({...form, schedule_name: e.target.value})} className="login-input" style={{ width: '100%' }} />
                    </div>
                    <div style={{ marginBottom: '16px' }}>
                        <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '6px', color: '#666' }}>Frequency</label>
                        <select value={form.frequency} onChange={(e) => setForm({...form, frequency: e.target.value})} className="login-input" style={{ width: '100%' }}>
                            <option value="Daily">Daily</option>
                            <option value="Weekly">Weekly</option>
                            <option value="Monthly">Monthly</option>
                            <option value="Adhoc">Adhoc</option>
                        </select>
                    </div>
                    <div style={{ marginBottom: '20px' }}>
                        <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '6px', color: '#666' }}>Scheduled Time</label>
                        <input type="datetime-local" value={form.scheduled_time} onChange={(e) => setForm({...form, scheduled_time: e.target.value})} className="login-input" style={{ width: '100%' }} />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                        <button className="confirm-btn-cancel" onClick={() => !saving && onCancel()} disabled={saving}>Cancel</button>
                        <button className="confirm-btn-delete" style={{ background: '#4a90d9' }} onClick={() => onSave(form)} disabled={saving}>
                            {saving ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}