// ── iKnowMed Report Detail (matches iknowmed-reports app_v3.py) ────────────────
function IkmReportDetail({ data, onBack, currentUser, onGenerateSuccess, onScheduleSuccess, onNotify }) {
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
                onNotify={onNotify}
                onGenerate={async () => {
                    if (!currentUser) { onNotify('Please sign in first', 'warning'); return; }
                    try {
                        const response = await fetch(`/api/reports/${report.id}/generate`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ user_id: currentUser.user_id, user_name: currentUser.name })
                        });
                        const result = await response.json();
                        if (result.success) {
                            onNotify('Report generated! Check the Generated Reports tab.');
                            if (onGenerateSuccess) onGenerateSuccess();
                        } else {
                            onNotify('Error: ' + result.error, 'error');
                        }
                    } catch (err) {
                        onNotify('Error generating report: ' + err.message, 'error');
                    }
                }}
                onSchedule={async (scheduleData) => {
                    if (!currentUser) { onNotify('Please sign in first', 'warning'); return; }
                    const response = await fetch(`/api/reports/${report.id}/schedule`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: currentUser.user_id, user_name: currentUser.name, ...scheduleData })
                    });
                    const result = await response.json();
                    if (result.success) {
                        onNotify('Report scheduled! Check the Practice Scheduled Reports tab.');
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