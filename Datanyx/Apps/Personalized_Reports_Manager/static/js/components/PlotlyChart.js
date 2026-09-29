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