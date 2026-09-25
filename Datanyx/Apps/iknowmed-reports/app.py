import dash
from dash import html, dcc, Input, Output
import os

app = dash.Dash(__name__, title="iKnowMed Gen 2 - Reports")
server = app.server

REPORT_CATEGORIES = {
    "General": [
        {"id": 1, "name": "Supportive Care Interventions Report"},
        {"id": 2, "name": "Decision Support Interventions Feedback Report"},
        {"id": 3, "name": "Patient Charts Merged Report"},
        {"id": 4, "name": "Depression Screening Needed and Completed Report"},
        {"id": 5, "name": "Task & Time Cumulative Dashboard"},
        {"id": 6, "name": "Medication Administration Record with Admix Report"},
        {"id": 7, "name": "iKnowMed G1 Report"},
        {"id": 9, "name": "Trending Pain Scores Report"},
        {"id": 10, "name": "Pain Scale and PDMP Evaluation Report"},
        {"id": 17, "name": "Visit List Report"},
        {"id": 18, "name": "Charge Capture"},
        {"id": 19, "name": "Patient List"},
        {"id": 20, "name": "Clinical Profile Chart Alert"},
        {"id": 21, "name": "Order History"},
        {"id": 22, "name": "Diagnosis"},
        {"id": 23, "name": "Task and Time Capture Report"},
        {"id": 26, "name": "Unfinished Charting"},
    ],
    "Worklist Queue Reports": [
        {"id": 8, "name": "Outbound Fax Worklist Queue Report"},
        {"id": 11, "name": "Ins Auth Fin Counseling Worklist Queue Report"},
        {"id": 12, "name": "Orders Queue Worklist Queue Report"},
        {"id": 15, "name": "Attach Documents Worklist Queue Productivity Report"},
        {"id": 16, "name": "Attach Documents Worklist Queue Audit Report"},
    ],
    "Audit & Specialty": [
        {"id": 13, "name": "Regimen Orders Report"},
        {"id": 14, "name": "Prescription Audit Report"},
        {"id": 24, "name": "Genospace iKM Integration"},
        {"id": 25, "name": "Precision Medicine Orders & Results"},
    ],
}


def report_item(report):
    return html.Div(
        report["name"],
        style={
            "padding": "10px 14px",
            "borderBottom": "1px solid #eaeaea",
            "cursor": "pointer",
            "fontSize": "13px",
            "color": "#333",
            "backgroundColor": "white",
        },
    )


def category_card(title, items):
    return html.Div(
        [
            html.Div(
                title,
                style={
                    "backgroundColor": "#6b6b6b",
                    "color": "white",
                    "padding": "10px 14px",
                    "fontSize": "14px",
                    "fontWeight": "bold",
                    "borderRadius": "5px 5px 0 0",
                },
            ),
            html.Div(
                [report_item(r) for r in items],
                style={
                    "maxHeight": "520px",
                    "overflowY": "auto",
                    "backgroundColor": "white",
                    "borderRadius": "0 0 5px 5px",
                    "border": "1px solid #ddd",
                    "borderTop": "none",
                },
            ),
        ],
        style={
            "flex": "1",
            "minWidth": "280px",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.10)",
            "borderRadius": "5px",
        },
    )


app.layout = html.Div(
    [
        # ---- Top header bar ----
        html.Div(
            [
                html.Div(
                    [
                        html.Span(
                            "iKnowMed",
                            style={
                                "fontSize": "18px",
                                "fontWeight": "bold",
                                "color": "white",
                            },
                        ),
                        html.Sup(
                            "\u2122",
                            style={"color": "white", "fontSize": "9px"},
                        ),
                        html.Span(
                            " Generation 2",
                            style={
                                "fontSize": "14px",
                                "color": "#bbb",
                                "marginLeft": "3px",
                            },
                        ),
                    ],
                    style={"display": "flex", "alignItems": "baseline"},
                ),
                html.Div(
                    [
                        dcc.Input(
                            placeholder="Search Patient Name or ID",
                            style={
                                "border": "none",
                                "outline": "none",
                                "width": "210px",
                                "padding": "5px 8px",
                                "fontSize": "12px",
                                "borderRadius": "3px",
                            },
                        ),
                    ],
                    style={"marginLeft": "25px"},
                ),
                html.Div(
                    [
                        html.Div(
                            "Onc Hem of MSH",
                            style={
                                "color": "white",
                                "fontSize": "12px",
                                "fontWeight": "bold",
                            },
                        ),
                        html.Div(
                            "(Unspecified Location) - 05/12/2026",
                            style={"color": "#aaa", "fontSize": "11px"},
                        ),
                    ],
                    style={"marginLeft": "auto", "textAlign": "center"},
                ),
                html.Div(
                    [
                        html.Span(
                            m,
                            style={
                                "color": "white",
                                "fontSize": "12px",
                                "margin": "0 12px",
                                "cursor": "pointer",
                            },
                        )
                        for m in [
                            "Worklist Queues \u25bc",
                            "Manage \u25bc",
                            "Admin \u25bc",
                            "Links",
                        ]
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "marginLeft": "25px",
                    },
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "background": "linear-gradient(to bottom, #555, #3a3a3a)",
                "padding": "8px 16px",
            },
        ),
        # ---- Tab bar ----
        html.Div(
            [
                html.Div(
                    "Imdc's Dashboard",
                    style={
                        "padding": "8px 16px",
                        "fontSize": "13px",
                        "backgroundColor": "#ddd",
                        "borderRadius": "5px 5px 0 0",
                        "marginRight": "3px",
                        "cursor": "pointer",
                    },
                ),
                html.Div(
                    "Reports  \u00d7",
                    style={
                        "padding": "8px 16px",
                        "fontSize": "13px",
                        "backgroundColor": "white",
                        "borderRadius": "5px 5px 0 0",
                        "border": "1px solid #ccc",
                        "borderBottom": "1px solid white",
                        "fontWeight": "bold",
                        "cursor": "pointer",
                    },
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "flex-end",
                "backgroundColor": "#ccc",
                "padding": "6px 12px 0",
            },
        ),
        # ---- Sub-tabs ----
        html.Div(
            [
                html.Span(
                    "Reports",
                    style={
                        "padding": "5px 16px",
                        "border": "2px solid #c8a000",
                        "borderRadius": "15px",
                        "fontWeight": "bold",
                        "fontSize": "13px",
                        "marginRight": "18px",
                        "cursor": "pointer",
                    },
                ),
                html.Span(
                    "Generated Reports",
                    style={
                        "fontSize": "13px",
                        "color": "#555",
                        "marginRight": "18px",
                        "cursor": "pointer",
                    },
                ),
                html.Span(
                    "Practice Scheduled Reports",
                    style={
                        "fontSize": "13px",
                        "color": "#555",
                        "cursor": "pointer",
                    },
                ),
            ],
            style={
                "padding": "12px 16px",
                "backgroundColor": "white",
                "borderBottom": "1px solid #ddd",
                "display": "flex",
                "alignItems": "center",
            },
        ),
        # ---- Search bar ----
        html.Div(
            [
                html.Span(
                    "Reports",
                    style={
                        "fontSize": "13px",
                        "color": "#555",
                        "padding": "4px 10px",
                        "backgroundColor": "#e8e8e8",
                        "borderRadius": "3px",
                    },
                ),
                html.Div(style={"flex": "1"}),
                dcc.Input(
                    id="search-reports",
                    placeholder="Search Report",
                    style={
                        "border": "1px solid #ccc",
                        "borderRadius": "3px",
                        "padding": "6px 12px",
                        "fontSize": "12px",
                        "width": "180px",
                    },
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "padding": "10px 16px",
                "backgroundColor": "#f5f5f5",
                "borderBottom": "1px solid #ddd",
            },
        ),
        # ---- Report cards ----
        html.Div(
            id="reports-container",
            children=[
                category_card(cat, rpts)
                for cat, rpts in REPORT_CATEGORIES.items()
            ],
            style={
                "display": "flex",
                "gap": "20px",
                "padding": "24px 20px",
                "backgroundColor": "#ececec",
                "minHeight": "calc(100vh - 220px)",
                "alignItems": "flex-start",
                "flexWrap": "wrap",
            },
        ),
    ],
    style={
        "fontFamily": "Arial, Helvetica, sans-serif",
        "margin": "0",
        "minHeight": "100vh",
        "backgroundColor": "#ececec",
    },
)


@app.callback(
    Output("reports-container", "children"),
    Input("search-reports", "value"),
)
def filter_reports(query):
    if not query:
        return [
            category_card(c, r) for c, r in REPORT_CATEGORIES.items()
        ]
    q = query.lower()
    cards = []
    for cat, rpts in REPORT_CATEGORIES.items():
        matches = [r for r in rpts if q in r["name"].lower()]
        if matches:
            cards.append(category_card(cat, matches))
    if not cards:
        return [
            html.Div(
                "No reports match your search.",
                style={"padding": "20px", "color": "#888", "fontSize": "14px"},
            )
        ]
    return cards


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
