// ── Filter Sidebar (matches iknowmed-reports) ────────────────────────────────
function IkmFilterSidebar({ onGenerate, onSchedule, onFilterChange, onNotify, reportId, currentUser }) {
    const [openSections, setOpenSections] = useState({
        'Mapping Date': true, 'Status': true, 'Launch Location': true,
        'Edited': false, 'Diagnosis': true, 'Practice': false, 'Vendor': false, 'Panel Name': false,
    });
    const [showScheduleModal, setShowScheduleModal] = useState(false);
    const [scheduleForm, setScheduleForm] = useState({ schedule_name: '', frequency: 'Weekly', scheduled_time: '' });
    const [scheduling, setScheduling] = useState(false);

    // Filter state
    const [mappingDate, setMappingDate] = useState('prior_cal_week');
    const [statusFilters, setStatusFilters] = useState({ received: false, saved: false });
    const [locationFilters, setLocationFilters] = useState({ usq: false, mr: false });
    const [diagnosisFilters, setDiagnosisFilters] = useState({});

    // Notify parent when filters change
    useEffect(() => {
        if (onFilterChange) {
            const params = new URLSearchParams();
            params.set('mapping_date', mappingDate);
            Object.entries(statusFilters).filter(([,v]) => v).forEach(([k]) => params.append('status', k));
            Object.entries(locationFilters).filter(([,v]) => v).forEach(([k]) => params.append('launch_location', k));
            Object.entries(diagnosisFilters).filter(([,v]) => v).forEach(([k]) => params.append('diagnosis', k));
            onFilterChange(params.toString());
        }
    }, [mappingDate, statusFilters, locationFilters, diagnosisFilters]);

    const toggleSection = (name) => setOpenSections(prev => ({ ...prev, [name]: !prev[name] }));

    const handleScheduleSubmit = async () => {
        if (!scheduleForm.schedule_name.trim()) {
            if (onNotify) { onNotify('Please enter a schedule name', 'warning'); return; }
            return;
        }
        setScheduling(true);
        try {
            await onSchedule(scheduleForm);
            setShowScheduleModal(false);
            setScheduleForm({ schedule_name: '', frequency: 'Weekly', scheduled_time: '' });
        } catch (err) {
            if (onNotify) { onNotify('Error scheduling report: ' + err.message, 'error'); }
        } finally {
            setScheduling(false);
        }
    };

    const SECTIONS = [
        { name: 'Mapping Date', type: 'radio', options: [
            { label: '  All', value: 'all' },
            { label: '  Prior Calendar Month', value: 'prior_cal_month' },
            { label: '  Prior Calendar Week (Mon-Sun)', value: 'prior_cal_week', default: true },
            { label: '  Prior Work Week (Mon-Fri)', value: 'prior_work_week' },
            { label: '  Previous Calendar Year', value: 'prev_cal_year' },
            { label: '  Custom Date Range', value: 'custom_range' },
            { label: '  Custom Period', value: 'custom_period' },
        ]},
        { name: 'Status', type: 'checkbox', options: [
            { label: '  Received', value: 'received' },
            { label: '  Saved', value: 'saved' },
        ]},
        { name: 'Launch Location', type: 'checkbox', options: [
            { label: '  USQ', value: 'usq' },
            { label: '  MR', value: 'mr' },
        ]},
        { name: 'Edited', type: 'empty' },
        { name: 'Diagnosis', type: 'checkbox', selectAll: true, options: [
            { label: '  Bladder Cancer - Urothelial', value: 'bladder' },
            { label: '  Genospace sends diagnosis found on the lab results', value: 'genospace' },
            { label: '  Metastatic malignant neoplasm to bone (disorder)', value: 'metastatic' },
            { label: '  Pancreatic Adenocarcinoma', value: 'pancreatic' },
            { label: '  Uterine Neoplasms - Endometrial Carcinoma', value: 'uterine' },
            { label: '  cancer', value: 'cancer' },
        ]},
        { name: 'Practice', type: 'empty' },
        { name: 'Vendor', type: 'empty' },
        { name: 'Panel Name', type: 'empty' },
    ];

    const allOpen = () => setOpenSections(Object.fromEntries(SECTIONS.map(s => [s.name, true])));
    const allClose = () => setOpenSections(Object.fromEntries(SECTIONS.map(s => [s.name, false])));

    return (
        <div className="ikm-filter-sidebar">
            <div className="ikm-filter-buttons-top">
                <button className="ikm-btn-outline">{'\u21bb'} RESET ALL</button>
                <button className="ikm-btn-outline">FILTER PREVIEW</button>
            </div>
            <div className="ikm-filter-preset">
                <div className="ikm-preset-label">Filter Preset</div>
                <div className="ikm-preset-row">
                    <select className="ikm-preset-select"><option value="none">None</option></select>
                    <span className="ikm-preset-save">Save New</span>
                </div>
            </div>
            <div className="ikm-collapse-all">
                <span onClick={allOpen}>{'\u2295'} Open All</span>
                <span onClick={allClose}>{'\u2296'} Collapse All</span>
            </div>
            <div className="ikm-filter-sections">
                {SECTIONS.map(section => (
                    <div className="ikm-filter-section" key={section.name}>
                        <div className="ikm-filter-section-header" onClick={() => toggleSection(section.name)}>
                            <span>{section.name}</span>
                            <span className="ikm-filter-arrow">{openSections[section.name] ? '\u203a' : '\u203a'}</span>
                        </div>
                        {openSections[section.name] && (
                            <div className="ikm-filter-section-body">
                                {section.type === 'radio' && section.options.map(opt => (
                                    <label key={opt.value} className="ikm-filter-option">
                                        <input type="radio" name={section.name} value={opt.value}
                                            checked={mappingDate === opt.value}
                                            onChange={() => setMappingDate(opt.value)} /> {opt.label}
                                    </label>
                                ))}
                                {section.type === 'checkbox' && section.selectAll && (
                                    <label className="ikm-filter-option"><input type="checkbox"
                                        onChange={(e) => {
                                            const newDiag = {};
                                            section.options.forEach(o => newDiag[o.value] = e.target.checked);
                                            setDiagnosisFilters(newDiag);
                                        }} /> Select All</label>
                                )}
                                {section.type === 'checkbox' && section.options && section.options.map(opt => {
                                    const filterState = section.name === 'Status' ? statusFilters : section.name === 'Launch Location' ? locationFilters : diagnosisFilters;
                                    const setFilterState = section.name === 'Status' ? setStatusFilters : section.name === 'Launch Location' ? setLocationFilters : setDiagnosisFilters;
                                    return (
                                        <label key={opt.value} className="ikm-filter-option">
                                            <input type="checkbox" value={opt.value}
                                                checked={filterState[opt.value] || false}
                                                onChange={(e) => setFilterState(prev => ({ ...prev, [opt.value]: e.target.checked }))}
                                            /> {opt.label}
                                        </label>
                                    );
                                })}
                                {section.type === 'empty' && <div className="ikm-filter-empty">No options available</div>}
                            </div>
                        )}
                    </div>
                ))}
            </div>
            <div className="ikm-filter-buttons-bottom">
                <button className="ikm-btn-preview">PREVIEW</button>
                <button className="ikm-btn-generate" onClick={onGenerate}>GENERATE</button>
                <button className="ikm-btn-schedule" title="Schedule Report" onClick={() => setShowScheduleModal(true)}>{'\u23f0'}</button>
            </div>

            {showScheduleModal && (
                <div className="ikm-schedule-modal-overlay" onClick={() => !scheduling && setShowScheduleModal(false)}>
                    <div className="ikm-schedule-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="ikm-schedule-modal-header">
                            <h3>Schedule Report</h3>
                            <button className="ikm-schedule-modal-close" onClick={() => !scheduling && setShowScheduleModal(false)}>{'\u00d7'}</button>
                        </div>
                        <div className="ikm-schedule-modal-body">
                            <div className="ikm-schedule-field">
                                <label>Schedule Name *</label>
                                <input
                                    type="text"
                                    placeholder="Enter schedule name"
                                    value={scheduleForm.schedule_name}
                                    onChange={(e) => setScheduleForm({...scheduleForm, schedule_name: e.target.value})}
                                    className="ikm-schedule-input"
                                />
                            </div>
                            <div className="ikm-schedule-field">
                                <label>Frequency</label>
                                <select
                                    value={scheduleForm.frequency}
                                    onChange={(e) => setScheduleForm({...scheduleForm, frequency: e.target.value})}
                                    className="ikm-schedule-input"
                                >
                                    <option value="Daily">Daily</option>
                                    <option value="Weekly">Weekly</option>
                                    <option value="Monthly">Monthly</option>
                                    <option value="Adhoc">Adhoc</option>
                                </select>
                            </div>
                            <div className="ikm-schedule-field">
                                <label>Scheduled Time</label>
                                <input
                                    type="datetime-local"
                                    value={scheduleForm.scheduled_time}
                                    onChange={(e) => setScheduleForm({...scheduleForm, scheduled_time: e.target.value})}
                                    className="ikm-schedule-input"
                                />
                            </div>
                        </div>
                        <div className="ikm-schedule-modal-footer">
                            <button className="ikm-schedule-btn-cancel" onClick={() => setShowScheduleModal(false)} disabled={scheduling}>Cancel</button>
                            <button className="ikm-schedule-btn-submit" onClick={handleScheduleSubmit} disabled={scheduling}>
                                {scheduling ? 'Scheduling...' : 'Schedule'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}