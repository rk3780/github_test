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