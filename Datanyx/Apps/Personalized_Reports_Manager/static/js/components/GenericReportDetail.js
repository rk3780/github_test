// ── Generic Report Detail ─────────────────────────────────────────────────────
function GenericReportDetail({ data, onBack, currentUser, onGenerate, onSchedule, onExport }) {
    const { report, archetype, kpi_cards, charts, table_data } = data;
    const [activeChart, setActiveChart] = useState(0);
    const [showAllCharts, setShowAllCharts] = useState(false);

    // Build Plotly data from backend chart spec
    const buildPlotlyData = (chart) => {
        if (chart.type === 'pie') {
            return [{
                values: chart.values || [],
                labels: chart.labels || [],
                type: 'pie',
                textinfo: 'label+value+percent',
                marker: { colors: ['#4a90d9', '#27ae60', '#f39c12', '#e74c3c', '#8e44ad', '#16a085'] }
            }];
        }
        const series = chart.series || [];
        return series.map(s => {
            if (chart.type === 'line') {
                return {
                    x: chart.x || [],
                    y: s.y || [],
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: s.name || '',
                    line: { color: s.color || '#4a90d9', width: 2 },
                    marker: { size: 6 }
                };
            } else {
                return {
                    x: chart.x || [],
                    y: s.y || [],
                    type: 'bar',
                    name: s.name || '',
                    marker: { color: s.color || '#4a90d9' }
                };
            }
        });
    };

    const buildLayout = (chart) => {
        const base = {
            margin: { l: 50, r: 20, t: 20, b: 60 },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { size: 12, color: '#666' },
            xaxis: { gridcolor: '#eee', tickfont: { size: 11 } },
            yaxis: { gridcolor: '#eee', tickfont: { size: 11 }, rangemode: 'tozero' },
            legend: { orientation: 'h', y: -0.3, xanchor: 'center', x: 0.5 }
        };
        if (chart.type === 'pie') {
            return { margin: { l: 10, r: 10, t: 10, b: 10 }, height: 300, paper_bgcolor: 'transparent', font: { size: 12, color: '#666' } };
        }
        return { ...base, height: 300 };
    };

    return (
        <div className="ikm-report-detail-wrapper">
            <div className="ikm-report-detail-main">
                <div className="ikm-detail-back-bar">
                    <span className="ikm-detail-back-link" onClick={onBack}>{'\u2190'} Back to Reports</span>
                </div>
                <h2 className="report-detail-title">{report.name}</h2>
                <div className="report-detail-subtitle">Archetype: {archetype} | Data Last Extracted: {new Date().toLocaleDateString()}</div>

                {/* KPI Cards */}
                {kpi_cards && kpi_cards.length > 0 && (
                    <div className="generic-kpi-row">
                        {kpi_cards.map((kpi, i) => (
                            <div className="generic-kpi-card" key={i} style={{ borderTop: `4px solid ${kpi.color || '#4a90d9'}` }}>
                                <div className="generic-kpi-value" style={{ color: kpi.color || '#4a90d9' }}>{kpi.value}</div>
                                <div className="generic-kpi-label">{kpi.label}</div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Charts */}
                {charts && charts.length > 0 && (
                    <>
                        <div className="generic-chart-tabs">
                            <button className={`generic-chart-tab ${!showAllCharts && activeChart === 0 ? 'active' : ''}`} onClick={() => { setShowAllCharts(false); setActiveChart(0); }}>{charts[0].title}</button>
                            {charts.length > 1 && charts.slice(1).map((ch, i) => (
                                <button key={i + 1} className={`generic-chart-tab ${!showAllCharts && activeChart === i + 1 ? 'active' : ''}`} onClick={() => { setShowAllCharts(false); setActiveChart(i + 1); }}>{ch.title}</button>
                            ))}
                            <button className={`generic-chart-tab ${showAllCharts ? 'active' : ''}`} onClick={() => setShowAllCharts(true)}>All Charts</button>
                        </div>

                        {!showAllCharts ? (
                            <div className="generic-chart-container">
                                <PlotlyChart data={buildPlotlyData(charts[activeChart])} layout={buildLayout(charts[activeChart])} />
                            </div>
                        ) : (
                            <div className="generic-all-charts">
                                {charts.map((ch, i) => (
                                    <div className="generic-chart-card" key={i}>
                                        <div className="generic-chart-title">{ch.title}</div>
                                        <PlotlyChart data={buildPlotlyData(ch)} layout={buildLayout(ch)} />
                                    </div>
                                ))}
                            </div>
                        )}
                    </>
                )}

                {/* Data Table */}
                {table_data && (
                    <div className="generic-table-container">
                        <div className="generic-table-header">
                            <h3 className="ds-chart-title">Data Table</h3>
                            {onExport && (
                                <button className="generic-export-btn" onClick={onExport}>{'\u2193'} Export CSV</button>
                            )}
                        </div>
                        <div className="ds-table-wrapper">
                            <table className="ds-patient-table">
                                <thead>
                                    <tr>
                                        {table_data.columns.map((col, i) => <th key={i}>{col}</th>)}
                                    </tr>
                                </thead>
                                <tbody>
                                    {table_data.rows.map((row, i) => (
                                        <tr key={i}>
                                            {row.map((cell, j) => <td key={j}>{cell}</td>)}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}