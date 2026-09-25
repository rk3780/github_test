// Main App Component
const { useState, useEffect, useRef, Component } = React;

// ── Error Boundary ──────────────────────────────────────────────────────────
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

// ── Plotly Chart Component ──────────────────────────────────────────────────
function PlotlyChart({ data, layout, config }) {
    const chartRef = useRef(null);
    useEffect(() => {
        if (chartRef.current && data && data.length > 0 && window.Plotly) {
            Plotly.newPlot(chartRef.current, data, layout || {}, config || { displayModeBar: false, responsive: true });
        }
        return () => {
            if (chartRef.current && window.Plotly) {
                Plotly.purge(chartRef.current);
            }
        };
    }, [data, layout]);
    return <div ref={chartRef} style={{ width: '100%' }} />;
}

// ── Filter Sidebar (matches iknowmed-reports) ────────────────────────────────
function IkmFilterSidebar({ onGenerate, onSchedule, reportId, currentUser }) {
    const [openSections, setOpenSections] = useState({
        'Mapping Date': true, 'Status': true, 'Launch Location': true,
        'Edited': false, 'Diagnosis': true, 'Practice': false, 'Vendor': false, 'Panel Name': false,
    });
    const [showScheduleModal, setShowScheduleModal] = useState(false);
    const [scheduleForm, setScheduleForm] = useState({ schedule_name: '', frequency: 'Weekly', scheduled_time: '' });
    const [scheduling, setScheduling] = useState(false);

    const toggleSection = (name) => setOpenSections(prev => ({ ...prev, [name]: !prev[name] }));

    const handleScheduleSubmit = async () => {
        if (!scheduleForm.schedule_name.trim()) {
            alert('Please enter a schedule name');
            return;
        }
        setScheduling(true);
        try {
            await onSchedule(scheduleForm);
            setShowScheduleModal(false);
            setScheduleForm({ schedule_name: '', frequency: 'Weekly', scheduled_time: '' });
        } catch (err) {
            alert('Error scheduling report: ' + err.message);
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
                            <span className="ikm-filter-arrow">{openSections[section.name] ? '\u203A' : '\u203A'}</span>
                        </div>
                        {openSections[section.name] && (
                            <div className="ikm-filter-section-body">
                                {section.type === 'radio' && section.options.map(opt => (
                                    <label key={opt.value} className="ikm-filter-option">
                                        <input type="radio" name={section.name} value={opt.value} defaultChecked={opt.default} /> {opt.label}
                                    </label>
                                ))}
                                {section.type === 'checkbox' && section.selectAll && (
                                    <label className="ikm-filter-option"><input type="checkbox" /> Select All</label>
                                )}
                                {section.type === 'checkbox' && section.options && section.options.map(opt => (
                                    <label key={opt.value} className="ikm-filter-option"><input type="checkbox" value={opt.value} /> {opt.label}</label>
                                ))}
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

// ── iKnowMed Report Detail (matches iknowmed-reports app_v3.py) ────────────────
function IkmReportDetail({ data, onBack, currentUser, onGenerateSuccess, onScheduleSuccess }) {
    const { report, volume, time_to_completion, usage_by_practice, usage_by_vendor, lifecycle, edits } = data;
    const [activeTab, setActiveTab] = useState(null);

    const DETAIL_TABS = [
        { name: 'Volume', key: 'volume' },
        { name: 'Time to Completion', key: 'ttc' },
        { name: 'Usage by Practice', key: 'practice' },
        { name: 'Usage by Vendor', key: 'vendor' },
        { name: 'Lifecycle', key: 'lifecycle' },
        { name: 'Edits', key: 'edits' },
    ];

    // ── Chart data ──
    const volChart = [
        { x: volume.dates, y: volume.total, type: 'scatter', mode: 'lines+markers', name: 'Total Reports',
          line: { color: '#4a90d9', width: 2 }, marker: { size: 7, symbol: 'circle-open', line: { width: 2, color: '#4a90d9' } } },
        { x: volume.dates, y: volume.saved, type: 'scatter', mode: 'lines+markers', name: 'Total Saved Reports',
          line: { color: '#c9a0dc', width: 2 }, marker: { size: 7, symbol: 'circle-open', line: { width: 2, color: '#c9a0dc' } } },
    ];
    const volLayout = {
        xaxis: { title: 'Received Date', gridcolor: '#eee' },
        yaxis: { title: 'Reports', gridcolor: '#eee', rangemode: 'tozero' },
        legend: { orientation: 'h', y: -0.25, xanchor: 'center', x: 0.5 },
        margin: { l: 50, r: 20, t: 20, b: 70 }, height: 350, paper_bgcolor: 'white', plot_bgcolor: 'white',
    };

    const ttc = time_to_completion;
    const ttcChart = [
        { x: ttc.dates, y: ttc.total_avg, type: 'scatter', mode: 'lines+markers', name: 'Total Avg', line: { color: '#c9a0dc', width: 2 }, marker: { size: 5, symbol: 'circle-open', line: { width: 2, color: '#c9a0dc' } } },
        { x: ttc.dates, y: ttc.usq_avg, type: 'scatter', mode: 'lines+markers', name: 'USQ Avg', line: { color: '#4a90d9', width: 2 }, marker: { size: 5, symbol: 'circle-open', line: { width: 2, color: '#4a90d9' } } },
        { x: ttc.dates, y: ttc.mr_avg, type: 'scatter', mode: 'lines+markers', name: 'MR Avg', line: { color: '#7ec8e3', width: 2 }, marker: { size: 5, symbol: 'circle-open', line: { width: 2, color: '#7ec8e3' } } },
    ];
    const ttcLayout = {
        xaxis: { title: 'Received Date', gridcolor: '#eee' },
        yaxis: { title: 'Review Average with duration in Seconds', gridcolor: '#eee', rangemode: 'tozero' },
        legend: { orientation: 'h', y: -0.25, xanchor: 'center', x: 0.5 },
        margin: { l: 60, r: 20, t: 20, b: 70 }, height: 320, paper_bgcolor: 'white', plot_bgcolor: 'white',
    };

    const lifecycleChart = [{
        type: 'sankey', arrangement: 'snap',
        node: { pad: 20, thickness: 20, label: lifecycle.node_labels,
            color: ['#b8d4e3', '#9b8ec4', '#6ab0a3', '#9b8ec4', '#c4bfdc', '#6ab0a3', '#a0cfc4', '#9b8ec4', '#6ab0a3'] },
        link: { source: lifecycle.link_sources, target: lifecycle.link_targets, value: lifecycle.link_values,
            color: ['rgba(155,142,196,0.4)', 'rgba(106,176,163,0.4)', 'rgba(155,142,196,0.4)', 'rgba(196,191,220,0.4)', 'rgba(106,176,163,0.4)', 'rgba(160,207,196,0.4)', 'rgba(155,142,196,0.4)', 'rgba(196,191,220,0.4)', 'rgba(106,176,163,0.4)', 'rgba(160,207,196,0.4)'] },
    }];
    const lifecycleLayout = { margin: { l: 10, r: 10, t: 10, b: 10 }, height: 280, paper_bgcolor: 'white', font: { size: 11 } };

    // ── Section header helper ──
    const SectionHeader = ({ title, showDisplay = true }) => (
        <div className="ikm-section-header">
            <span className="ikm-section-title">{title}</span>
            {!activeTab && <span className="ikm-section-more" onClick={() => { const tab = DETAIL_TABS.find(t => t.name === title); if (tab) setActiveTab(tab.key); }}>See more {'\u2192'}</span>}
            <div className="ikm-section-spacer" />
            {showDisplay && <><span className="ikm-display-label">Display by:</span><select className="ikm-display-select" defaultValue="day"><option value="day">Day</option><option value="week">Week</option><option value="month">Month</option></select></>}
        </div>
    );

    // ── Sections ──
    const volSection = (
        <div className="ikm-detail-section">
            <SectionHeader title="Volume" />
            <div className="ikm-volume-row">
                <div className="ikm-volume-cards">
                    <div className="ikm-vol-card"><div className="summary-value">{volume.total_sum}</div><div className="summary-label"><span className="ikm-dot-blue">{'\u25a0'}</span> Total Reports</div></div>
                    <div className="ikm-vol-card"><div className="summary-value" style={{ color: '#c9a0dc' }}>{volume.saved_sum}</div><div className="summary-label"><span className="ikm-dot-purple">{'\u25a0'}</span> Total Saved Reports</div><div className="ikm-vol-rate">Saved Rate: {volume.rate}%</div></div>
                </div>
                <div className="ikm-volume-chart"><PlotlyChart data={volChart} layout={volLayout} /></div>
            </div>
        </div>
    );

    const ttcSection = (
        <div className="ikm-detail-section">
            <SectionHeader title="Time to Completion" />
            <div className="ikm-ttc-subtitle">Review Time (Launch to Save)</div>
            <div className="ikm-volume-row">
                <div className="ikm-volume-cards">
                    <div className="ikm-vol-card"><div className="summary-value">{ttc.total_avg_str}</div><div className="summary-label"><span style={{ color: '#c9a0dc' }}>{'\u25a0'}</span> Total Avg</div></div>
                    <div className="ikm-vol-card"><div className="summary-value">{ttc.usq_avg_str}</div><div className="summary-label"><span style={{ color: '#4a90d9' }}>{'\u25a0'}</span> USQ Avg</div></div>
                    <div className="ikm-vol-card"><div className="summary-value">{ttc.mr_avg_str}</div><div className="summary-label"><span style={{ color: '#7ec8e3' }}>{'\u25a0'}</span> MR Avg</div></div>
                    <div className="ikm-vol-card"><div className="summary-value">{ttc.map_to_save_avg}</div><div className="summary-label">Map to Save Avg</div></div>
                </div>
                <div className="ikm-volume-chart"><PlotlyChart data={ttcChart} layout={ttcLayout} /></div>
            </div>
        </div>
    );

    const practiceSection = (
        <div className="ikm-detail-section">
            <SectionHeader title="Usage by Practice" showDisplay={false} />
            <div className="ikm-volume-row">
                <div className="ikm-usage-card"><div className="summary-value">{usage_by_practice.usage_fraction}</div><div className="summary-label">Usage Rate <span style={{ color: '#4a90d9', fontWeight: 'bold' }}>{usage_by_practice.usage_rate}</span></div></div>
                <div className="ikm-table-wrapper"><table className="ikm-detail-table"><thead><tr><th>Practice</th><th>Total Reports</th><th>Saved</th></tr></thead><tbody>{usage_by_practice.rows.map((r, i) => <tr key={i}><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td></tr>)}</tbody></table></div>
            </div>
        </div>
    );

    const vendorSection = (
        <div className="ikm-detail-section">
            <SectionHeader title="Usage by Vendor" showDisplay={false} />
            <div className="ikm-volume-row">
                <div className="ikm-usage-card"><div className="summary-value">{usage_by_vendor.usage_fraction}</div><div className="summary-label">Usage Rate <span style={{ color: '#4a90d9', fontWeight: 'bold' }}>{usage_by_vendor.usage_rate}</span></div></div>
                <div className="ikm-table-wrapper"><table className="ikm-detail-table"><thead><tr><th>Vendor</th><th>Usage {'\u2193'}</th></tr></thead><tbody>{usage_by_vendor.rows.map((r, i) => <tr key={i}><td>{r[0]}</td><td>{r[1]}</td></tr>)}</tbody></table></div>
            </div>
        </div>
    );

    const lifecycleSection = (
        <div className="ikm-detail-section">
            <SectionHeader title="Lifecycle" showDisplay={false} />
            <div className="ikm-lifecycle-stats">
                <div className="ikm-lc-stat"><div className="summary-value">{lifecycle.opened_for_review}</div><div className="summary-label">Opened for Review</div></div>
                <div className="ikm-lc-stat"><div className="summary-value">{lifecycle.total_launches}</div><div className="summary-label">Total Launches</div></div>
                <div className="ikm-lc-stat"><div className="summary-value">{lifecycle.total_edited}</div><div className="summary-label">Total Edited</div><div className="ikm-lc-sub">Total Not Edited {lifecycle.total_not_edited}</div></div>
                <div className="ikm-lc-stat"><div className="summary-value">{lifecycle.total_saved}</div><div className="summary-label">Total Saved</div></div>
            </div>
            <PlotlyChart data={lifecycleChart} layout={lifecycleLayout} />
            <div className="ikm-section-note">Note: Data represented in this section is available from 10/11/2025 onward.</div>
        </div>
    );

    const editsSection = (
        <div className="ikm-detail-section">
            <SectionHeader title="Edits" showDisplay={false} />
            <div className="ikm-edits-row">
                <div className="ikm-edits-col"><table className="ikm-detail-table"><thead><tr><th>Diagnosis</th><th>Edit/Total Reports</th></tr></thead><tbody>{edits.diagnosis.map((r, i) => <tr key={i}><td>{r[0]}</td><td>{r[1]}</td></tr>)}</tbody></table></div>
                <div className="ikm-edits-col"><table className="ikm-detail-table"><thead><tr><th>Inference Group</th><th>Total Edits</th></tr></thead><tbody>{edits.inference.map((r, i) => <tr key={i}><td>{r[0]}</td><td>{r[1]}</td></tr>)}</tbody></table></div>
                <div className="ikm-edits-col"><table className="ikm-detail-table"><thead><tr><th>Original Value</th><th>Edited Value</th></tr></thead><tbody>{edits.edits.map((r, i) => <tr key={i}><td>{r[0]}</td><td>{r[1]}</td></tr>)}</tbody></table></div>
            </div>
        </div>
    );

    const sections = { volume: volSection, ttc: ttcSection, practice: practiceSection, vendor: vendorSection, lifecycle: lifecycleSection, edits: editsSection };

    return (
        <div className="ikm-report-detail-wrapper">
            <IkmFilterSidebar
                reportId={report.id}
                currentUser={currentUser}
                onGenerate={async () => {
                    if (!currentUser) { alert('Please sign in first'); return; }
                    try {
                        const response = await fetch(`/api/reports/${report.id}/generate`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ user_id: currentUser.user_id, user_name: currentUser.name })
                        });
                        const result = await response.json();
                        if (result.success) {
                            alert('Report generated! Check the Generated Reports tab.');
                            if (onGenerateSuccess) onGenerateSuccess();
                        } else {
                            alert('Error: ' + result.error);
                        }
                    } catch (err) {
                        alert('Error generating report: ' + err.message);
                    }
                }}
                onSchedule={async (scheduleData) => {
                    if (!currentUser) { alert('Please sign in first'); return; }
                    const response = await fetch(`/api/reports/${report.id}/schedule`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: currentUser.user_id, user_name: currentUser.name, ...scheduleData })
                    });
                    const result = await response.json();
                    if (result.success) {
                        alert('Report scheduled! Check the Practice Scheduled Reports tab.');
                        if (onScheduleSuccess) onScheduleSuccess();
                    } else {
                        throw new Error(result.error || 'Scheduling failed');
                    }
                }}
            />
            <div className="ikm-report-detail-main">
                <div className="ikm-detail-back-bar"><span className="ikm-detail-back-link" onClick={onBack}>{'\u2190'} Back to Main Dashboard</span></div>
                <h2 className="report-detail-title">{report.name}</h2>
                <div className="report-detail-subtitle">Data Last Extracted: 08/16/2025 at 12:00am PST</div>

                {activeTab && (
                    <div className="ikm-detail-tabs">
                        {DETAIL_TABS.map(tab => (
                            <div key={tab.key} className={`ikm-detail-tab ${activeTab === tab.key ? 'active' : ''}`} onClick={() => setActiveTab(tab.key)}>{tab.name}</div>
                        ))}
                    </div>
                )}

                {!activeTab ? (
                    <>{volSection}{ttcSection}<div className="ikm-detail-row">{practiceSection}{vendorSection}</div>{lifecycleSection}{editsSection}</>
                ) : (
                    sections[activeTab]
                )}
            </div>
        </div>
    );
}


// ── Depression Screening Detail (matches AI/BI dashboard) ──────────────────
function DepressionScreeningDetail({ data, onBack }) {
    const { report, summary, status_by_location, tools_distribution, completion_by_sex, status_overview, patient_list } = data;
    const [filterStatus, setFilterStatus] = useState({ Yes: true, No: true });

    const filteredPatients = (patient_list || []).filter(p => filterStatus[p.Depression_Screening_Completed]);

    // ── Counter cards ──
    const counters = [
        { label: 'Total Patients', value: summary.total_patients, color: '#4a90d9' },
        { label: 'Screenings Completed', value: summary.screenings_completed, color: '#27ae60' },
        { label: 'Screenings Needed', value: summary.screenings_needed, color: '#e74c3c' },
        { label: 'Total Records', value: summary.total_records, color: '#8e44ad' },
    ];

    // ── Bar chart: Screening Status by Location ──
    const locations = [...new Set((status_by_location || []).map(r => r.Appointment_Location))];
    const locYes = locations.map(loc => {
        const row = (status_by_location || []).find(r => r.Appointment_Location === loc && r.Depression_Screening_Completed === 'Yes');
        return row ? parseInt(row.cnt) : 0;
    });
    const locNo = locations.map(loc => {
        const row = (status_by_location || []).find(r => r.Appointment_Location === loc && r.Depression_Screening_Completed === 'No');
        return row ? parseInt(row.cnt) : 0;
    });
    const locationChart = [
        { x: locations, y: locYes, type: 'bar', name: 'Yes', marker: { color: '#4a90d9' } },
        { x: locations, y: locNo, type: 'bar', name: 'No', marker: { color: '#e74c3c' } },
    ];
    const locationLayout = {
        xaxis: { title: 'Appointment Location', gridcolor: '#eee' },
        yaxis: { title: 'Patient Count', gridcolor: '#eee', rangemode: 'tozero' },
        barmode: 'group', legend: { orientation: 'h', y: -0.3 },
        margin: { l: 50, r: 20, t: 20, b: 80 }, height: 350, paper_bgcolor: 'white', plot_bgcolor: 'white',
    };

    // ── Bar chart: Screening Tools Distribution ──
    const toolsChart = [{
        x: (tools_distribution || []).map(r => r.Screening_Tool_Used),
        y: (tools_distribution || []).map(r => parseInt(r.cnt)),
        type: 'bar', marker: { color: '#4a90d9' },
    }];
    const toolsLayout = {
        xaxis: { title: 'Screening Tool', gridcolor: '#eee' },
        yaxis: { title: 'Patient Count', gridcolor: '#eee', rangemode: 'tozero' },
        margin: { l: 50, r: 20, t: 20, b: 60 }, height: 350, paper_bgcolor: 'white', plot_bgcolor: 'white',
    };

    // ── Bar chart: Screening Completion by Sex ──
    const sexes = [...new Set((completion_by_sex || []).map(r => r.Sex_At_Birth))];
    const sexYes = sexes.map(s => {
        const row = (completion_by_sex || []).find(r => r.Sex_At_Birth === s && r.Depression_Screening_Completed === 'Yes');
        return row ? parseInt(row.cnt) : 0;
    });
    const sexNo = sexes.map(s => {
        const row = (completion_by_sex || []).find(r => r.Sex_At_Birth === s && r.Depression_Screening_Completed === 'No');
        return row ? parseInt(row.cnt) : 0;
    });
    const sexChart = [
        { x: sexes, y: sexYes, type: 'bar', name: 'Yes', marker: { color: '#4a90d9' } },
        { x: sexes, y: sexNo, type: 'bar', name: 'No', marker: { color: '#e74c3c' } },
    ];
    const sexLayout = {
        xaxis: { title: 'Sex At Birth', gridcolor: '#eee' },
        yaxis: { title: 'Patient Count', gridcolor: '#eee', rangemode: 'tozero' },
        barmode: 'group', legend: { orientation: 'h', y: -0.3 },
        margin: { l: 50, r: 20, t: 20, b: 60 }, height: 320, paper_bgcolor: 'white', plot_bgcolor: 'white',
    };

    // ── Pie chart: Screening Status Overview ──
    const pieChart = [{
        values: (status_overview || []).map(r => parseInt(r.cnt)),
        labels: (status_overview || []).map(r => r.Depression_Screening_Completed),
        type: 'pie', marker: { colors: ['#4a90d9', '#e74c3c'] },
        textinfo: 'label+value+percent',
    }];
    const pieLayout = { margin: { l: 20, r: 20, t: 20, b: 20 }, height: 300, paper_bgcolor: 'white' };

    return (
        <div className="ds-report-wrapper">
            <div className="ds-back-bar">
                <span className="ds-back-link" onClick={onBack}>{'\u2190'} Back to Reports</span>
            </div>
            <h2 className="ds-report-title">{report.name}</h2>

            {/* Counter cards */}
            <div className="ds-counter-row">
                {counters.map((c, i) => (
                    <div className="ds-counter-card" key={i}>
                        <div className="ds-counter-value" style={{ color: c.color }}>{c.value}</div>
                        <div className="ds-counter-label">{c.label}</div>
                    </div>
                ))}
            </div>

            {/* Charts row 1 */}
            <div className="ds-chart-row">
                <div className="ds-chart-card">
                    <h3 className="ds-chart-title">Screening Status by Location</h3>
                    <PlotlyChart data={locationChart} layout={locationLayout} />
                </div>
                <div className="ds-chart-card">
                    <h3 className="ds-chart-title">Screening Status Overview</h3>
                    <PlotlyChart data={pieChart} layout={pieLayout} />
                </div>
            </div>

            {/* Charts row 2 */}
            <div className="ds-chart-row">
                <div className="ds-chart-card">
                    <h3 className="ds-chart-title">Screening Tools Distribution</h3>
                    <PlotlyChart data={toolsChart} layout={toolsLayout} />
                </div>
                <div className="ds-chart-card">
                    <h3 className="ds-chart-title">Screening Completion by Sex</h3>
                    <PlotlyChart data={sexChart} layout={sexLayout} />
                </div>
            </div>

            {/* Filter */}
            <div className="ds-filter-bar">
                <span className="ds-filter-label">Filter by Screening Status:</span>
                <label className="ds-filter-option">
                    <input type="checkbox" checked={filterStatus.Yes} onChange={() => setFilterStatus(prev => ({ ...prev, Yes: !prev.Yes }))} /> Yes
                </label>
                <label className="ds-filter-option">
                    <input type="checkbox" checked={filterStatus.No} onChange={() => setFilterStatus(prev => ({ ...prev, No: !prev.No }))} /> No
                </label>
            </div>

            {/* Patient table */}
            <div className="ds-table-wrapper">
                <h3 className="ds-chart-title">Detailed Patient List</h3>
                <table className="ds-patient-table">
                    <thead>
                        <tr>
                            <th>Last Name</th>
                            <th>First Name</th>
                            <th>MRN</th>
                            <th>DOB</th>
                            <th>Sex</th>
                            <th>Appointment Date</th>
                            <th>Location</th>
                            <th>Provider</th>
                            <th>Screening Completed</th>
                            <th>Screening Tool</th>
                            <th>Plan Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredPatients.map((p, i) => (
                            <tr key={i}>
                                <td>{p.Last_Name}</td>
                                <td>{p.First_Name}</td>
                                <td>{p.MRN}</td>
                                <td>{p.DOB}</td>
                                <td>{p.Sex_At_Birth}</td>
                                <td>{p.Appointment_Date_Time || 'N/A'}</td>
                                <td>{p.Appointment_Location}</td>
                                <td>{p.Appointment_Provider_Resource || 'N/A'}</td>
                                <td>{p.Depression_Screening_Completed}</td>
                                <td>{p.Screening_Tool_Used || 'N/A'}</td>
                                <td>{p.Plan_Date || 'N/A'}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}


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
                alert('Failed to update pause status');
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
                alert('Report generated successfully! Check the Generated Reports tab.');
                // Silently refresh generated reports in background if on that tab
                if (activeTab === 'generated-reports') {
                    fetchGeneratedReports(false);
                }
            } else {
                alert('Error: ' + data.error);
            }
        } catch (err) {
            alert('Error generating report: ' + err.message);
        } finally {
            setUpdatingReportId(null);
        }
    };

    const handleDelete = async (reportId) => {
        if (!confirm('Are you sure you want to delete this scheduled report?')) return;
        
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
                alert('Report deleted successfully!');
            } else {
                // Revert on error
                setReports(prevReports => [...prevReports, deletedReport].sort((a, b) => a.report_id - b.report_id));
                setTotalReports(prev => prev + 1);
                alert('Error: ' + data.error);
            }
        } catch (err) {
            alert('Error deleting report: ' + err.message);
            // Fetch fresh data on error
            fetchReports(false);
        } finally {
            setUpdatingReportId(null);
        }
    };

    const handleGeneratedReportDelete = async (reportId) => {
        if (!confirm('Are you sure you want to delete this generated report?')) return;
        
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
                alert('Generated report deleted successfully!');
            } else {
                // Revert on error
                setGeneratedReports(prevReports => [...prevReports, deletedReport].sort((a, b) => b.generated_on - a.generated_on));
                setTotalReports(prev => prev + 1);
                alert('Error: ' + data.error);
            }
        } catch (err) {
            alert('Error deleting generated report: ' + err.message);
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
                <button className="logout-btn" onClick={handleLogout}>Logout</button>
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
                                                <button className="icon-btn edit-btn">✏️</button>
                                            </td>
                                            <td>
                                                <button 
                                                    className="icon-btn delete-btn"
                                                    onClick={() => handleDelete(report.report_id)}
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
                                            <div className="ikm-category-header">{category}</div>
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
                        <div className="loading">Loading report details...</div>
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
                        ) : (
                            <IkmReportDetail
                                data={reportDetails}
                                onBack={() => {
                                    setSelectedReportId(null);
                                    setReportDetails(null);
                                }}
                                currentUser={currentUser}
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
                                                    onClick={() => handleGeneratedReportDelete(report.report_id)}
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
        </div>
    );
}

// Render the app
ReactDOM.render(<App />, document.getElementById('root'));