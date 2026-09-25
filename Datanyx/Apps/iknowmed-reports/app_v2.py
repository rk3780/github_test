import dash
from dash import html, dcc, Input, Output
import plotly.graph_objects as go
import os
import random

app = dash.Dash(
    __name__,
    title="iKnowMed Gen 2 - Reports",
    suppress_callback_exceptions=True,
)
server = app.server

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
ALL_REPORTS = [
    {"id": 1,  "name": "Supportive Care Interventions Report"},
    {"id": 2,  "name": "Decision Support Interventions Feedback Report"},
    {"id": 3,  "name": "Patient Charts Merged Report"},
    {"id": 4,  "name": "Depression Screening Needed and Completed Report"},
    {"id": 5,  "name": "Task & Time Cumulative Dashboard"},
    {"id": 6,  "name": "Medication Administration Record with Admix Report"},
    {"id": 7,  "name": "iKnowMed G1 Report"},
    {"id": 8,  "name": "Outbound Fax Worklist Queue Report"},
    {"id": 9,  "name": "Trending Pain Scores Report"},
    {"id": 10, "name": "Pain Scale and PDMP Evaluation Report"},
    {"id": 11, "name": "Ins Auth Fin Counseling Worklist Queue Report"},
    {"id": 12, "name": "Orders Queue Worklist Queue Report"},
    {"id": 13, "name": "Regimen Orders Report"},
    {"id": 14, "name": "Prescription Audit Report"},
    {"id": 15, "name": "Attach Documents Worklist Queue Productivity Report"},
    {"id": 16, "name": "Attach Documents Worklist Queue Audit Report"},
    {"id": 17, "name": "Visit List Report"},
    {"id": 18, "name": "Charge Capture"},
    {"id": 19, "name": "Patient List"},
    {"id": 20, "name": "Clinical Profile Chart Alert"},
    {"id": 21, "name": "Order History"},
    {"id": 22, "name": "Diagnosis"},
    {"id": 23, "name": "Task and Time Capture Report"},
    {"id": 24, "name": "Genospace iKM Integration"},
    {"id": 25, "name": "Precision Medicine Orders & Results"},
    {"id": 26, "name": "Unfinished Charting"},
]

REPORT_BY_ID = {r["id"]: r for r in ALL_REPORTS}

REPORT_CATEGORIES = {
    "General": [r for r in ALL_REPORTS if r["id"] in
                [1,2,3,4,5,6,7,9,10,17,18,19,20,21,22,23,26]],
    "Worklist Queue Reports": [r for r in ALL_REPORTS if r["id"] in
                               [8,11,12,15,16]],
    "Audit & Specialty": [r for r in ALL_REPORTS if r["id"] in
                          [13,14,24,25]],
}

FILTER_SECTIONS = [
    "Mapping Date", "Status", "Launch Location", "Edited",
    "Diagnosis", "Practice", "Vendor", "Panel Name",
]

DIAGNOSIS_OPTIONS = [
    "Bladder Cancer - Urothelial",
    "Genospace sends diagnosis found on the lab results",
    "Metastatic malignant neoplasm to bone (disorder)",
    "Pancreatic Adenocarcinoma",
    "Uterine Neoplasms - Endometrial Carcinoma",
    "cancer",
]

DETAIL_TABS = [
    "Volume", "Time to Completion", "Usage by Practice",
    "Usage by Vendor", "Lifecycle", "Edits",
]


# ---------------------------------------------------------------------------
# Mock data generator
# ---------------------------------------------------------------------------
def get_report_data(report_id):
    random.seed(report_id * 37)
    dates = [f"7/{d}" for d in range(4, 15)]
    total = [random.randint(0, 8) for _ in dates]
    saved = [min(random.randint(0, max(t, 1)), t) for t in total]
    total_sum = max(sum(total), random.randint(10, 50))
    saved_sum = min(max(sum(saved), random.randint(3, 15)), total_sum)
    rate = round(saved_sum / total_sum * 100) if total_sum else 0
    return dict(dates=dates, total=total, saved=saved,
                total_sum=total_sum, saved_sum=saved_sum, rate=rate)


# ---------------------------------------------------------------------------
# Shared UI components
# ---------------------------------------------------------------------------
def header_bar():
    return html.Div([
        html.Div([
            html.Span("iKnowMed",
                      style={"fontSize": "18px", "fontWeight": "bold", "color": "white"}),
            html.Sup("\u2122", style={"color": "white", "fontSize": "9px"}),
            html.Span(" Generation 2",
                      style={"fontSize": "14px", "color": "#bbb", "marginLeft": "3px"}),
        ], style={"display": "flex", "alignItems": "baseline"}),
        html.Div([
            dcc.Input(placeholder="Search Patient Name or ID",
                      style={"border": "none", "outline": "none", "width": "210px",
                             "padding": "5px 8px", "fontSize": "12px",
                             "borderRadius": "3px"}),
        ], style={"marginLeft": "25px"}),
        html.Div([
            html.Div("Onc Hem of MSH",
                     style={"color": "white", "fontSize": "12px", "fontWeight": "bold"}),
            html.Div("(Unspecified Location) - 05/12/2026",
                     style={"color": "#aaa", "fontSize": "11px"}),
        ], style={"marginLeft": "auto", "textAlign": "center"}),
        html.Div([
            html.Span(m, style={"color": "white", "fontSize": "12px",
                                "margin": "0 12px", "cursor": "pointer"})
            for m in ["Worklist Queues \u25bc", "Manage \u25bc", "Admin \u25bc", "Links"]
        ], style={"display": "flex", "alignItems": "center", "marginLeft": "25px"}),
    ], style={"display": "flex", "alignItems": "center",
              "background": "linear-gradient(to bottom, #555, #3a3a3a)",
              "padding": "8px 16px"})


def tab_bar():
    return html.Div([
        html.Div("Imdc's Dashboard",
                 style={"padding": "8px 16px", "fontSize": "13px",
                        "backgroundColor": "#ddd", "borderRadius": "5px 5px 0 0",
                        "marginRight": "3px", "cursor": "pointer"}),
        dcc.Link("Reports  \u00d7", href="/",
                 style={"padding": "8px 16px", "fontSize": "13px",
                        "backgroundColor": "white", "borderRadius": "5px 5px 0 0",
                        "border": "1px solid #ccc", "borderBottom": "1px solid white",
                        "fontWeight": "bold", "cursor": "pointer",
                        "textDecoration": "none", "color": "#333"}),
    ], style={"display": "flex", "alignItems": "flex-end",
              "backgroundColor": "#ccc", "padding": "6px 12px 0"})


def sub_tabs_bar():
    return html.Div([
        html.Span("Reports",
                  style={"padding": "5px 16px", "border": "2px solid #c8a000",
                         "borderRadius": "15px", "fontWeight": "bold",
                         "fontSize": "13px", "marginRight": "18px", "cursor": "pointer"}),
        html.Span("Generated Reports",
                  style={"fontSize": "13px", "color": "#555",
                         "marginRight": "18px", "cursor": "pointer"}),
        html.Span("Practice Scheduled Reports",
                  style={"fontSize": "13px", "color": "#555", "cursor": "pointer"}),
    ], style={"padding": "12px 16px", "backgroundColor": "white",
              "borderBottom": "1px solid #ddd", "display": "flex", "alignItems": "center"})


# ---------------------------------------------------------------------------
# Main listing page
# ---------------------------------------------------------------------------
def report_item(r):
    return dcc.Link(
        html.Div(r["name"],
                 style={"padding": "10px 14px", "borderBottom": "1px solid #eaeaea",
                        "cursor": "pointer", "fontSize": "13px", "color": "#333",
                        "backgroundColor": "white"}),
        href=f"/report/{r['id']}",
        style={"textDecoration": "none"},
    )


def category_card(title, items):
    return html.Div([
        html.Div(title,
                 style={"backgroundColor": "#6b6b6b", "color": "white",
                        "padding": "10px 14px", "fontSize": "14px",
                        "fontWeight": "bold", "borderRadius": "5px 5px 0 0"}),
        html.Div([report_item(r) for r in items],
                 style={"maxHeight": "520px", "overflowY": "auto",
                        "backgroundColor": "white", "borderRadius": "0 0 5px 5px",
                        "border": "1px solid #ddd", "borderTop": "none"}),
    ], style={"flex": "1", "minWidth": "280px",
              "boxShadow": "0 1px 4px rgba(0,0,0,0.10)", "borderRadius": "5px"})


def main_page():
    return html.Div([
        sub_tabs_bar(),
        html.Div([
            html.Span("Reports",
                      style={"fontSize": "13px", "color": "#555", "padding": "4px 10px",
                             "backgroundColor": "#e8e8e8", "borderRadius": "3px"}),
            html.Div(style={"flex": "1"}),
            dcc.Input(id="search-reports", placeholder="Search Report",
                      style={"border": "1px solid #ccc", "borderRadius": "3px",
                             "padding": "6px 12px", "fontSize": "12px", "width": "180px"}),
        ], style={"display": "flex", "alignItems": "center", "padding": "10px 16px",
                  "backgroundColor": "#f5f5f5", "borderBottom": "1px solid #ddd"}),
        html.Div(
            id="reports-container",
            children=[category_card(c, r) for c, r in REPORT_CATEGORIES.items()],
            style={"display": "flex", "gap": "20px", "padding": "24px 20px",
                   "backgroundColor": "#ececec", "minHeight": "calc(100vh - 230px)",
                   "alignItems": "flex-start", "flexWrap": "wrap"},
        ),
    ])


# ---------------------------------------------------------------------------
# Detail page components
# ---------------------------------------------------------------------------
def filter_section(name):
    body = html.Div()
    if name == "Diagnosis":
        body = html.Div([
            dcc.Checklist(
                options=[{"label": "  Select All", "value": "all"}] +
                        [{"label": f"  {d}", "value": d} for d in DIAGNOSIS_OPTIONS],
                value=[],
                style={"fontSize": "12px", "lineHeight": "24px"},
                inputStyle={"marginRight": "6px"},
            ),
        ], style={"paddingLeft": "8px", "paddingTop": "6px", "paddingBottom": "6px"})
    return html.Details([
        html.Summary(
            html.Div([
                html.Span(name, style={"fontSize": "13px", "fontWeight": "500",
                                       "color": "#333"}),
                html.Span("\u203a", style={"fontSize": "16px", "color": "#4a90d9",
                                          "marginLeft": "auto"}),
            ], style={"display": "flex", "alignItems": "center", "width": "100%"}),
            style={"listStyle": "none", "cursor": "pointer",
                   "padding": "9px 0", "borderBottom": "1px solid #eee"},
        ),
        body,
    ], open=(name == "Diagnosis"))


def filter_sidebar_panel():
    return html.Div([
        html.Div([
            html.Button("\u21bb RESET ALL",
                        style={"border": "1px solid #4a90d9", "backgroundColor": "white",
                               "color": "#4a90d9", "borderRadius": "3px",
                               "padding": "5px 10px", "fontSize": "11px",
                               "cursor": "pointer", "marginRight": "8px"}),
            html.Button("FILTER PREVIEW",
                        style={"border": "1px solid #4a90d9", "backgroundColor": "white",
                               "color": "#4a90d9", "borderRadius": "3px",
                               "padding": "5px 10px", "fontSize": "11px", "cursor": "pointer"}),
        ], style={"display": "flex", "marginBottom": "12px"}),

        html.Div([
            html.Div("Filter Preset",
                     style={"fontSize": "11px", "color": "#666", "marginBottom": "4px"}),
            html.Div([
                dcc.Dropdown(options=[{"label": "None", "value": "none"}],
                             value="none",
                             style={"fontSize": "12px", "width": "130px"},
                             clearable=False),
                html.Span("Save New",
                          style={"fontSize": "12px", "color": "#4a90d9",
                                 "cursor": "pointer", "marginLeft": "8px",
                                 "whiteSpace": "nowrap"}),
            ], style={"display": "flex", "alignItems": "center"}),
        ], style={"marginBottom": "10px"}),

        html.Div([
            html.Span("\u2295 Open All",
                      style={"fontSize": "12px", "color": "#4a90d9",
                             "cursor": "pointer", "marginRight": "10px"}),
            html.Span("\u2296 Collapse All",
                      style={"fontSize": "12px", "color": "#4a90d9", "cursor": "pointer"}),
        ], style={"marginBottom": "6px"}),

        html.Div([filter_section(s) for s in FILTER_SECTIONS]),

        html.Div([
            html.Button("PREVIEW",
                        style={"border": "1px solid #4a90d9", "backgroundColor": "white",
                               "color": "#4a90d9", "borderRadius": "3px",
                               "padding": "8px 18px", "fontSize": "12px",
                               "cursor": "pointer", "marginRight": "8px"}),
            html.Button("GENERATE",
                        style={"border": "none", "backgroundColor": "#4a90d9",
                               "color": "white", "borderRadius": "3px",
                               "padding": "8px 18px", "fontSize": "12px",
                               "cursor": "pointer"}),
        ], style={"display": "flex", "marginTop": "18px"}),
    ], style={"width": "240px", "minWidth": "240px", "padding": "14px",
              "backgroundColor": "white", "borderRight": "1px solid #ddd",
              "overflowY": "auto", "height": "calc(100vh - 165px)"})


def volume_chart(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data["dates"], y=data["total"], mode="lines+markers",
        name="Total Reports",
        line=dict(color="#4a90d9", width=2),
        marker=dict(size=7, symbol="circle-open",
                    line=dict(width=2, color="#4a90d9"))))
    fig.add_trace(go.Scatter(
        x=data["dates"], y=data["saved"], mode="lines+markers",
        name="Total Saved Reports",
        line=dict(color="#c9a0dc", width=2),
        marker=dict(size=7, symbol="circle-open",
                    line=dict(width=2, color="#c9a0dc"))))
    fig.update_layout(
        xaxis_title="Received Date", yaxis_title="Reports",
        legend=dict(orientation="h", yanchor="top", y=-0.25,
                    xanchor="center", x=0.5),
        margin=dict(l=50, r=20, t=20, b=70), height=350,
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(gridcolor="#eee", showgrid=True),
        yaxis=dict(gridcolor="#eee", showgrid=True, rangemode="tozero"),
    )
    return fig


def volume_section(data):
    return html.Div([
        html.Div([
            html.Span("Reports Volume",
                      style={"fontSize": "18px", "fontWeight": "bold", "color": "#333"}),
            html.Span("See more \u2192",
                      style={"fontSize": "12px", "color": "#4a90d9",
                             "cursor": "pointer", "marginLeft": "10px"}),
            html.Div(style={"flex": "1"}),
            html.Span("Display by:",
                      style={"fontSize": "12px", "color": "#555", "marginRight": "6px"}),
            dcc.Dropdown(
                options=[{"label": "Day", "value": "day"},
                         {"label": "Week", "value": "week"},
                         {"label": "Month", "value": "month"}],
                value="day",
                style={"width": "90px", "fontSize": "12px"},
                clearable=False,
            ),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "16px"}),

        html.Div([
            # Left: summary cards
            html.Div([
                html.Div([
                    html.Div(str(data["total_sum"]),
                             style={"fontSize": "30px", "fontWeight": "bold",
                                    "color": "#333"}),
                    html.Div([
                        html.Span("\u25a0 ",
                                  style={"color": "#4a90d9", "fontSize": "11px"}),
                        html.Span("Total Reports",
                                  style={"fontSize": "12px", "color": "#333"}),
                    ]),
                ], style={"padding": "14px 16px", "border": "1px solid #ddd",
                          "borderRadius": "4px", "marginBottom": "10px"}),
                html.Div([
                    html.Div(str(data["saved_sum"]),
                             style={"fontSize": "30px", "fontWeight": "bold",
                                    "color": "#333"}),
                    html.Div([
                        html.Span("\u25a0 ",
                                  style={"color": "#c9a0dc", "fontSize": "11px"}),
                        html.Span("Total Saved Reports",
                                  style={"fontSize": "12px", "color": "#333"}),
                    ]),
                    html.Div(f"Saved Rate: {data['rate']}%",
                             style={"fontSize": "11px", "color": "#888", "marginTop": "4px"}),
                ], style={"padding": "14px 16px", "border": "1px solid #ddd",
                          "borderRadius": "4px"}),
            ], style={"width": "200px", "marginRight": "20px"}),

            # Right: line chart
            html.Div([
                dcc.Graph(figure=volume_chart(data), config={"displayModeBar": False}),
            ], style={"flex": "1"}),
        ], style={"display": "flex", "alignItems": "flex-start"}),
    ], style={"padding": "20px", "border": "1px solid #ddd",
              "borderRadius": "6px", "backgroundColor": "white", "marginTop": "16px"})


def detail_page(report_id):
    r = REPORT_BY_ID.get(report_id)
    if not r:
        return html.Div("Report not found.",
                        style={"padding": "40px", "fontSize": "16px", "color": "#888"})
    data = get_report_data(report_id)

    tab_base = {
        "padding": "8px 14px", "fontSize": "13px", "cursor": "pointer",
        "border": "1px solid #ddd", "borderBottom": "none",
        "borderRadius": "4px 4px 0 0", "marginRight": "3px",
        "backgroundColor": "#f5f5f5", "color": "#555",
    }
    tab_active = {**tab_base, "backgroundColor": "white",
                  "fontWeight": "bold", "color": "#333"}

    return html.Div([
        sub_tabs_bar(),
        # Breadcrumb
        html.Div([
            dcc.Link("Reports", href="/",
                     style={"fontSize": "13px", "color": "#555", "textDecoration": "none"}),
            html.Span("  \u203a  ", style={"color": "#999", "fontSize": "14px"}),
            html.Span(r["name"], style={"fontSize": "13px", "color": "#333"}),
        ], style={"padding": "10px 16px", "backgroundColor": "#f5f5f5",
                  "borderBottom": "1px solid #ddd"}),

        # Sidebar + main content
        html.Div([
            filter_sidebar_panel(),
            html.Div([
                dcc.Link("\u2190 Back to Main Dashboard", href="/",
                         style={"fontSize": "13px", "color": "#4a90d9",
                                "textDecoration": "none"}),
                html.H2(r["name"],
                        style={"margin": "6px 0 2px", "fontSize": "22px", "color": "#333"}),
                html.Div("Data Last Extracted: 08/16/2025 at 12:00am PST",
                         style={"fontSize": "12px", "color": "#888", "marginBottom": "14px"}),

                # Section tabs
                html.Div([
                    html.Span(t, style=tab_active if t == "Volume" else tab_base)
                    for t in DETAIL_TABS
                ], style={"display": "flex", "alignItems": "flex-end",
                          "borderBottom": "1px solid #ddd"}),

                volume_section(data),
            ], style={"flex": "1", "padding": "16px 20px",
                      "overflowY": "auto", "height": "calc(100vh - 165px)"}),
        ], style={"display": "flex", "backgroundColor": "#f9f9f9"}),
    ])


# ---------------------------------------------------------------------------
# App layout + routing
# ---------------------------------------------------------------------------
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    header_bar(),
    tab_bar(),
    html.Div(id="page-content"),
], style={"fontFamily": "Arial, Helvetica, sans-serif", "margin": "0",
          "minHeight": "100vh", "backgroundColor": "#ececec"})


@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname and pathname.startswith("/report/"):
        try:
            rid = int(pathname.rstrip("/").split("/")[-1])
            return detail_page(rid)
        except (ValueError, IndexError):
            pass
    return main_page()


@app.callback(
    Output("reports-container", "children"),
    Input("search-reports", "value"),
    prevent_initial_call=True,
)
def filter_reports(query):
    if not query:
        return [category_card(c, r) for c, r in REPORT_CATEGORIES.items()]
    q = query.lower()
    cards = []
    for cat, rpts in REPORT_CATEGORIES.items():
        matches = [r for r in rpts if q in r["name"].lower()]
        if matches:
            cards.append(category_card(cat, matches))
    if not cards:
        return [html.Div("No reports match your search.",
                         style={"padding": "20px", "color": "#888", "fontSize": "14px"})]
    return cards


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
