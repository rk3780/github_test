import dash
from dash import html, dcc, Input, Output, State, no_update, ctx, ALL
import plotly.graph_objects as go
import os, random, io, csv, zipfile, base64
from datetime import datetime


def _load_reports_from_table():
    """Load reports from dev.gold.G2_reports via Databricks SDK Statement Execution API."""
    try:
        from databricks.sdk import WorkspaceClient
        wh = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
        if not wh:
            print("No DATABRICKS_WAREHOUSE_ID set, skipping live query")
            return None
        w = WorkspaceClient()
        result = w.statement_execution.execute_statement(
            warehouse_id=wh,
            statement="SELECT report_id, report_name FROM dev.gold.G2_reports ORDER BY report_id",
            wait_timeout="30s",
        )
        if result.result and result.result.data_array:
            rows = result.result.data_array
            reports = [{"id": int(r[0]), "name": str(r[1])} for r in rows]
            print(f"Loaded {len(reports)} reports from dev.gold.G2_reports (max id={max(r['id'] for r in reports)})")
            return reports
        print(f"Query returned no data, status: {result.status}")
    except Exception as e:
        print(f"Could not load from table, using fallback: {e}")
    return None

app = dash.Dash(__name__, title="iKnowMed Gen 2 - Reports",
                suppress_callback_exceptions=True)
server = app.server

# ── data (source: dev.gold.G2_reports, fallback: hardcoded snapshot) ──────────────────────────────────────────────────────────────────
ALL_REPORTS = [
    {"id": 1,  "name": "Supportive Care Interventions Report"},
    {"id": 2,  "name": "Decision Support Interventions Feedback Report"},
    {"id": 3,  "name": "Patient Charts Merged Report"},
    {"id": 4,  "name": "Depression Screening Needed and Completed Report"},
    {"id": 5,  "name": "Task & Time Cumulative Dashboard"},
    {"id": 6,  "name": "Medication Administration Record with Admix Report"},
    {"id": 7,  "name": "iKnowMed G2 Report"},
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
]

# Cache for live data with TTL
import time as _time
_cache = {"data": None, "ts": 0, "ttl": 60}  # refresh every 60 seconds

def get_all_reports():
    """Return live reports from table (cached 60s), or hardcoded fallback."""
    now = _time.time()
    if _cache["data"] and (now - _cache["ts"]) < _cache["ttl"]:
        return _cache["data"]
    live = _load_reports_from_table()
    if live:
        _cache["data"] = live
        _cache["ts"] = now
        return live
    return ALL_REPORTS  # hardcoded fallback

def get_total_report_count():
    """Return max(report_id) from current report data."""
    rpts = get_all_reports()
    return max(r["id"] for r in rpts) if rpts else 0

TOTAL_REPORT_COUNT = max(r["id"] for r in ALL_REPORTS)  # startup default
_GENERATED_REPORTS = []  # in-memory store for generated report entries
_SCHEDULED_REPORTS = []  # in-memory store for practice scheduled reports
_JOB_ID = "754574519892113"  # Databricks job: iKnowMed_G2_Report_veiw

REPORT_BY_ID = {r["id"]: r for r in ALL_REPORTS}

def _build_categories(reports):
    gen_ids = {1,2,3,4,5,6,7,9,10,17,18,19,20,21,22,23}
    wl_ids = {8,11,12,15,16}
    audit_ids = {13,14,24,25}
    known = gen_ids | wl_ids | audit_ids
    gen = [r for r in reports if r["id"] in gen_ids]
    # auto-assign unknown new reports to General
    gen += [r for r in reports if r["id"] not in known]
    return {
        "General": gen,
        "Worklist Queue Reports": [r for r in reports if r["id"] in wl_ids],
        "Audit & Specialty": [r for r in reports if r["id"] in audit_ids],
    }

REPORT_CATEGORIES = _build_categories(ALL_REPORTS)
FILTER_SECTIONS = ["Mapping Date","Status","Launch Location","Edited",
                   "Diagnosis","Practice","Vendor","Panel Name"]
DIAGNOSIS_OPTIONS = [
    "Bladder Cancer - Urothelial",
    "Genospace sends diagnosis found on the lab results",
    "Metastatic malignant neoplasm to bone (disorder)",
    "Pancreatic Adenocarcinoma",
    "Uterine Neoplasms - Endometrial Carcinoma",
    "cancer",
]
DETAIL_TABS = ["Volume","Time to Completion","Usage by Practice",
               "Usage by Vendor","Lifecycle","Edits"]
EXPORT_OPTIONS = [
    {"label": "  Full Report Dataset",            "value": "full_report"},
    {"label": "  Usage by Practice",               "value": "usage_practice"},
    {"label": "  Full Report Dataset - Biomarker Details", "value": "biomarker_details"},
    {"label": "  Usage by Vendor",                  "value": "usage_vendor"},
    {"label": "  Edits by Diagnosis",               "value": "edits_diagnosis"},
    {"label": "  Edits by Biomarker",               "value": "edits_biomarker"},
]


def get_report_data(rid):
    random.seed(rid * 37)
    dates = [f"7/{d}" for d in range(4, 15)]
    tc = get_total_report_count()
    # distribute tc reports across the date range
    raw = [random.randint(0, 6) for _ in dates]
    raw_sum = sum(raw) or 1
    total = [max(round(v / raw_sum * tc), 0) for v in raw]
    # adjust so they sum to exactly tc
    diff = tc - sum(total)
    for i in range(abs(diff)):
        total[i % len(total)] += 1 if diff > 0 else -1
    total = [max(v, 0) for v in total]
    saved = [min(random.randint(0, max(t, 1)), t) for t in total]
    ts = tc
    ss = sum(saved)
    rate = round(ss / ts * 100) if ts else 0
    return dict(dates=dates, total=total, saved=saved,
                total_sum=ts, saved_sum=ss, rate=rate)


# ── overlay style helpers ─────────────────────────────────────────────────
_OVERLAY_SHOW = {"position":"fixed","top":"0","left":"0","width":"100%",
    "height":"100%","backgroundColor":"rgba(0,0,0,0.5)",
    "display":"flex","justifyContent":"center","alignItems":"center",
    "zIndex":"1000"}
_OVERLAY_HIDE = dict(_OVERLAY_SHOW, display="none")
_OVERLAY2_SHOW = dict(_OVERLAY_SHOW, zIndex="1001")
_OVERLAY2_HIDE = dict(_OVERLAY2_SHOW, display="none")
_BOX = {"backgroundColor":"white","borderRadius":"8px","padding":"24px",
    "width":"540px","maxHeight":"80vh","overflowY":"auto",
    "boxShadow":"0 4px 20px rgba(0,0,0,0.25)"}
_BOX_LG = dict(_BOX, width="600px", padding="28px", maxHeight="85vh")


# ── shared chrome ─────────────────────────────────────────────────────────
def header_bar():
    return html.Div([
        html.Div([
            html.Span("iKnowMed",style={"fontSize":"18px","fontWeight":"bold","color":"white"}),
            html.Sup("\u2122",style={"color":"white","fontSize":"9px"}),
            html.Span(" Generation 2",style={"fontSize":"14px","color":"#bbb","marginLeft":"3px"}),
        ],style={"display":"flex","alignItems":"baseline"}),
        html.Div([dcc.Input(placeholder="Search Patient Name or ID",
                  style={"border":"none","outline":"none","width":"210px",
                         "padding":"5px 8px","fontSize":"12px","borderRadius":"3px"})],
                 style={"marginLeft":"25px"}),
        html.Div([
            html.Div("Onc Hem of MSH",style={"color":"white","fontSize":"12px","fontWeight":"bold"}),
            html.Div("(Unspecified Location) - 05/12/2026",style={"color":"#aaa","fontSize":"11px"}),
        ],style={"marginLeft":"auto","textAlign":"center"}),
        html.Div([html.Span(m,style={"color":"white","fontSize":"12px","margin":"0 12px","cursor":"pointer"})
                  for m in ["Worklist Queues \u25bc","Manage \u25bc","Admin \u25bc","Links"]],
                 style={"display":"flex","alignItems":"center","marginLeft":"25px"}),
    ],style={"display":"flex","alignItems":"center",
             "background":"linear-gradient(to bottom,#555,#3a3a3a)","padding":"8px 16px"})

def tab_bar():
    return html.Div([
        html.Div("Imdc's Dashboard",style={"padding":"8px 16px","fontSize":"13px",
            "backgroundColor":"#ddd","borderRadius":"5px 5px 0 0","marginRight":"3px","cursor":"pointer"}),
        dcc.Link("Reports  \u00d7",href="/",style={"padding":"8px 16px","fontSize":"13px",
            "backgroundColor":"white","borderRadius":"5px 5px 0 0","border":"1px solid #ccc",
            "borderBottom":"1px solid white","fontWeight":"bold","cursor":"pointer",
            "textDecoration":"none","color":"#333"}),
    ],style={"display":"flex","alignItems":"flex-end","backgroundColor":"#ccc","padding":"6px 12px 0"})

def sub_tabs_bar(active="reports"):
    _gold={"padding":"5px 16px","border":"2px solid #c8a000","borderRadius":"15px",
           "fontWeight":"bold","fontSize":"13px","marginRight":"18px","cursor":"pointer",
           "textDecoration":"none","color":"#333"}
    _plain={"fontSize":"13px","color":"#555","marginRight":"18px","cursor":"pointer","textDecoration":"none"}
    return html.Div([
        dcc.Link("Reports",href="/",style=_gold if active=="reports" else _plain),
        dcc.Link("Generated Reports",href="/generated",style=_gold if active=="generated" else _plain),
        dcc.Link("Practice Scheduled Reports",href="/scheduled",style=_gold if active=="scheduled" else _plain),
    ],style={"padding":"12px 16px","backgroundColor":"white","borderBottom":"1px solid #ddd",
             "display":"flex","alignItems":"center"})


# ── main listing page ─────────────────────────────────────────────────────
def report_item(r):
    return dcc.Link(
        html.Div(r["name"],style={"padding":"10px 14px","borderBottom":"1px solid #eaeaea",
            "cursor":"pointer","fontSize":"13px","color":"#333","backgroundColor":"white"}),
        href=f"/report/{r['id']}",style={"textDecoration":"none"})

def category_card(title, items):
    return html.Div([
        html.Div(title,style={"backgroundColor":"#6b6b6b","color":"white","padding":"10px 14px",
            "fontSize":"14px","fontWeight":"bold","borderRadius":"5px 5px 0 0"}),
        html.Div([report_item(r) for r in items],style={"maxHeight":"520px","overflowY":"auto",
            "backgroundColor":"white","borderRadius":"0 0 5px 5px","border":"1px solid #ddd","borderTop":"none"}),
    ],style={"flex":"1","minWidth":"280px","boxShadow":"0 1px 4px rgba(0,0,0,0.10)","borderRadius":"5px"})

def main_page():
    return html.Div([
        sub_tabs_bar(),
        html.Div([
            html.Span("Reports",style={"fontSize":"13px","color":"#555","padding":"4px 10px",
                "backgroundColor":"#e8e8e8","borderRadius":"3px"}),
            html.Div(style={"flex":"1"}),
            dcc.Input(id="search-reports",placeholder="Search Report",
                      style={"border":"1px solid #ccc","borderRadius":"3px",
                             "padding":"6px 12px","fontSize":"12px","width":"180px"}),
        ],style={"display":"flex","alignItems":"center","padding":"10px 16px",
                 "backgroundColor":"#f5f5f5","borderBottom":"1px solid #ddd"}),
        html.Div(id="reports-container",
                 children=[category_card(c,r) for c,r in _build_categories(get_all_reports()).items()],
                 style={"display":"flex","gap":"20px","padding":"24px 20px",
                        "backgroundColor":"#ececec","minHeight":"calc(100vh - 230px)",
                        "alignItems":"flex-start","flexWrap":"wrap"}),
    ])


# ── detail: sidebar ───────────────────────────────────────────────────────
def filter_section(name):
    body = html.Div()
    if name == "Mapping Date":
        body = html.Div([
            dcc.RadioItems(
                options=[
                    {"label":"  All","value":"all"},
                    {"label":"  Prior Calendar Month","value":"prior_cal_month"},
                    {"label":html.Span(["  Prior Calendar Week (Mon -Sun)",html.Br(),
                        html.Span("    05/04/2026 - 05/10/2026",
                            style={"fontSize":"11px","color":"#555","paddingLeft":"6px"})]),
                     "value":"prior_cal_week"},
                    {"label":"  Prior Work Week (Mon -Fri)","value":"prior_work_week"},
                    {"label":"  Previous Calendar Year","value":"prev_cal_year"},
                    {"label":"  Custom Date Range","value":"custom_range"},
                    {"label":"  Custom Period","value":"custom_period"},
                ],
                value="prior_cal_week",
                style={"fontSize":"12px","lineHeight":"28px"},
                inputStyle={"marginRight":"6px"},
            ),
        ],style={"paddingLeft":"8px","paddingTop":"6px","paddingBottom":"6px"})
    elif name == "Launch Location":
        body = html.Div([
            dcc.Checklist(
                options=[{"label":"  USQ","value":"usq"},
                         {"label":"  MR","value":"mr"}],
                value=[],
                style={"fontSize":"12px","lineHeight":"28px"},
                inputStyle={"marginRight":"6px"},
            ),
        ],style={"paddingLeft":"8px","paddingTop":"6px","paddingBottom":"6px"})
    elif name == "Status":
        body = html.Div([
            dcc.Checklist(
                options=[{"label":"  Received","value":"received"},
                         {"label":"  Saved","value":"saved"}],
                value=[],
                style={"fontSize":"12px","lineHeight":"28px"},
                inputStyle={"marginRight":"6px"},
            ),
        ],style={"paddingLeft":"8px","paddingTop":"6px","paddingBottom":"6px"})
    elif name == "Diagnosis":
        body = html.Div([dcc.Checklist(
            options=[{"label":"  Select All","value":"all"}]+
                    [{"label":f"  {d}","value":d} for d in DIAGNOSIS_OPTIONS],
            value=[],style={"fontSize":"12px","lineHeight":"24px"},
            inputStyle={"marginRight":"6px"})],
            style={"paddingLeft":"8px","paddingTop":"6px","paddingBottom":"6px"})
    return html.Details([
        html.Summary(html.Div([
            html.Span(name,style={"fontSize":"13px","fontWeight":"500","color":"#333"}),
            html.Span("\u203a",style={"fontSize":"16px","color":"#4a90d9","marginLeft":"auto"}),
        ],style={"display":"flex","alignItems":"center","width":"100%"}),
            style={"listStyle":"none","cursor":"pointer","padding":"9px 0","borderBottom":"1px solid #eee"}),
        body],open=(name in ("Diagnosis","Mapping Date","Status","Launch Location")))

def filter_sidebar_panel():
    btn_out = {"border":"1px solid #4a90d9","backgroundColor":"white","color":"#4a90d9",
               "borderRadius":"3px","padding":"5px 10px","fontSize":"11px","cursor":"pointer"}
    return html.Div([
        html.Div([
            html.Button("\u21bb RESET ALL",style={**btn_out,"marginRight":"8px"}),
            html.Button("FILTER PREVIEW",style=btn_out),
        ],style={"display":"flex","marginBottom":"12px"}),
        html.Div([
            html.Div("Filter Preset",style={"fontSize":"11px","color":"#666","marginBottom":"4px"}),
            html.Div([
                dcc.Dropdown(options=[{"label":"None","value":"none"}],value="none",
                             style={"fontSize":"12px","width":"130px"},clearable=False),
                html.Span("Save New",style={"fontSize":"12px","color":"#4a90d9",
                    "cursor":"pointer","marginLeft":"8px","whiteSpace":"nowrap"}),
            ],style={"display":"flex","alignItems":"center"}),
        ],style={"marginBottom":"10px"}),
        html.Div([
            html.Span("\u2295 Open All",style={"fontSize":"12px","color":"#4a90d9","cursor":"pointer","marginRight":"10px"}),
            html.Span("\u2296 Collapse All",style={"fontSize":"12px","color":"#4a90d9","cursor":"pointer"}),
        ],style={"marginBottom":"6px"}),
        html.Div([filter_section(s) for s in FILTER_SECTIONS]),
        html.Div([
            html.Button("PREVIEW",style={"border":"1px solid #4a90d9","backgroundColor":"white",
                "color":"#4a90d9","borderRadius":"3px","padding":"8px 18px","fontSize":"12px",
                "cursor":"pointer","marginRight":"8px"}),
            html.Button("GENERATE",id="btn-generate",style={"border":"none","backgroundColor":"#4a90d9",
                "color":"white","borderRadius":"3px","padding":"8px 18px","fontSize":"12px",
                "cursor":"pointer"}),
            html.Button("\u23f0",id="btn-schedule-open",title="Schedule Report",
                style={"border":"1px solid #ccc","backgroundColor":"white","borderRadius":"3px",
                       "padding":"6px 10px","fontSize":"14px","cursor":"pointer","marginLeft":"6px"}),
        ],style={"display":"flex","marginTop":"18px","alignItems":"center"}),
    ],style={"width":"240px","minWidth":"240px","padding":"14px","backgroundColor":"white",
             "borderRight":"1px solid #ddd","overflowY":"auto","height":"calc(100vh - 165px)"})


# ── detail: chart ─────────────────────────────────────────────────────────
def volume_chart(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data["dates"],y=data["total"],mode="lines+markers",
        name="Total Reports",line=dict(color="#4a90d9",width=2),
        marker=dict(size=7,symbol="circle-open",line=dict(width=2,color="#4a90d9"))))
    fig.add_trace(go.Scatter(x=data["dates"],y=data["saved"],mode="lines+markers",
        name="Total Saved Reports",line=dict(color="#c9a0dc",width=2),
        marker=dict(size=7,symbol="circle-open",line=dict(width=2,color="#c9a0dc"))))
    fig.update_layout(xaxis_title="Received Date",yaxis_title="Reports",
        legend=dict(orientation="h",yanchor="top",y=-0.25,xanchor="center",x=0.5),
        margin=dict(l=50,r=20,t=20,b=70),height=350,
        plot_bgcolor="white",paper_bgcolor="white",
        xaxis=dict(gridcolor="#eee",showgrid=True),
        yaxis=dict(gridcolor="#eee",showgrid=True,rangemode="tozero"))
    return fig

def volume_section(data,rid=None):
    return html.Div([
        html.Div([
            html.Span("Reports Volume",style={"fontSize":"18px","fontWeight":"bold","color":"#333"}),
            (dcc.Link("See more \u2192",href=f"/report/{rid}/volume",style={"fontSize":"12px","color":"#4a90d9","textDecoration":"none","marginLeft":"10px"}) if rid else html.Span("See more \u2192",style={"fontSize":"12px","color":"#4a90d9","cursor":"pointer","marginLeft":"10px"})),
            html.Div(style={"flex":"1"}),
            html.Span("Display by:",style={"fontSize":"12px","color":"#555","marginRight":"6px"}),
            dcc.Dropdown(options=[{"label":"Day","value":"day"},{"label":"Week","value":"week"},
                {"label":"Month","value":"month"}],value="day",
                style={"width":"90px","fontSize":"12px"},clearable=False),
        ],style={"display":"flex","alignItems":"center","marginBottom":"16px"}),
        html.Div([
            html.Div([
                html.Div([
                    html.Div(str(data["total_sum"]),style={"fontSize":"30px","fontWeight":"bold","color":"#333"}),
                    html.Div([html.Span("\u25a0 ",style={"color":"#4a90d9","fontSize":"11px"}),
                              html.Span("Total Reports",style={"fontSize":"12px","color":"#333"})]),
                ],style={"padding":"14px 16px","border":"1px solid #ddd","borderRadius":"4px","marginBottom":"10px"}),
                html.Div([
                    html.Div(str(data["saved_sum"]),style={"fontSize":"30px","fontWeight":"bold","color":"#333"}),
                    html.Div([html.Span("\u25a0 ",style={"color":"#c9a0dc","fontSize":"11px"}),
                              html.Span("Total Saved Reports",style={"fontSize":"12px","color":"#333"})]),
                    html.Div(f"Saved Rate: {data['rate']}%",style={"fontSize":"11px","color":"#888","marginTop":"4px"}),
                ],style={"padding":"14px 16px","border":"1px solid #ddd","borderRadius":"4px"}),
            ],style={"width":"200px","marginRight":"20px"}),
            html.Div([dcc.Graph(figure=volume_chart(data),config={"displayModeBar":False})],
                     style={"flex":"1"}),
        ],style={"display":"flex","alignItems":"flex-start"}),
    ],style={"padding":"20px","border":"1px solid #ddd","borderRadius":"6px",
             "backgroundColor":"white","marginTop":"16px"})


# ── modal: select reports to export ───────────────────────────────────────
def _sec_hdr(title,show_display=True,rid=None):
    _TM={"Reports Volume":"volume","Time to Completion":"ttc","Usage by Practice":"practice","Usage by Vendor":"vendor","Lifecycle":"lifecycle","Edits":"edits"}
    _tk=_TM.get(title)
    _sm=dcc.Link("See more \u2192",href=f"/report/{rid}/{_tk}",style={"fontSize":"12px","color":"#4a90d9","textDecoration":"none","marginLeft":"10px"}) if rid and _tk else html.Span("See more \u2192",style={"fontSize":"12px","color":"#4a90d9","cursor":"pointer","marginLeft":"10px"})
    items = [html.Span(title,style={"fontSize":"18px","fontWeight":"bold","color":"#333"}),
             _sm,
             html.Div(style={"flex":"1"})]
    if show_display:
        items += [html.Span("Display by:",style={"fontSize":"12px","color":"#555","marginRight":"6px"}),
                  dcc.Dropdown(options=[{"label":"Day","value":"day"}],value="day",
                      style={"width":"90px","fontSize":"12px"},clearable=False)]
    return html.Div(items,style={"display":"flex","alignItems":"center","marginBottom":"14px"})

_SECBOX = {"padding":"20px","border":"1px solid #ddd","borderRadius":"6px","backgroundColor":"white","marginTop":"16px"}
_NOTE = "Note: Data represented in this section is available from 10/11/2025 onward."
_TH = {"backgroundColor":"#f0f0f0","padding":"8px 10px","fontSize":"12px","fontWeight":"bold","color":"#4a90d9","textAlign":"left","borderBottom":"2px solid #ddd"}
_TD = {"padding":"6px 10px","fontSize":"12px","color":"#333","borderBottom":"1px solid #eee","verticalAlign":"top"}

def _tbl(heads,rows):
    return html.Table([html.Thead(html.Tr([html.Th(h,style=_TH) for h in heads])),
        html.Tbody([html.Tr([html.Td(c,style=_TD) for c in r]) for r in rows])],
        style={"borderCollapse":"collapse","width":"100%"})


def time_to_completion_section(rid=None):
    dates=[f"7/{d}" for d in range(1,12)]
    ta_k=[190000,186000,182000,178000,174000,170000,166000,158000,148000,138000,125000]
    ua_k=[185000,182000,178000,174000,170000,166000,162000,155000,145000,135000,122000]
    ma_k=[195000,190000,185000,180000,175000,170000,165000,160000,152000,142000,128000]
    fig=go.Figure()
    for vals,nm,clr in [(ta_k,"Total Avg","#c9a0dc"),(ua_k,"USQ Avg","#4a90d9"),(ma_k,"MR Avg","#7ec8e3")]:
        fig.add_trace(go.Scatter(x=dates,y=vals,mode="lines+markers",name=nm,
            line=dict(color=clr,width=2),marker=dict(size=5,symbol="circle-open",line=dict(width=2,color=clr))))
    fig.update_layout(xaxis_title="Received Date",yaxis_title="Review Average with duration in Seconds",
        legend=dict(orientation="h",yanchor="top",y=-0.25,xanchor="center",x=0.5),
        margin=dict(l=60,r=20,t=20,b=70),height=320,plot_bgcolor="white",paper_bgcolor="white",
        xaxis=dict(gridcolor="#eee"),yaxis=dict(gridcolor="#eee",rangemode="tozero"))
    cs={"padding":"10px 12px","border":"1px solid #ddd","borderRadius":"4px","marginBottom":"8px"}
    sv={"fontSize":"20px","fontWeight":"bold","color":"#333"}
    def _card(val,label,clr):
        return html.Div([html.Div(val,style=sv),
            html.Div([html.Span("\u25a0 ",style={"color":clr,"fontSize":"10px"}),html.Span(label,style={"fontSize":"11px"})]),
        ],style=cs)
    return html.Div([_sec_hdr("Time to Completion",rid=rid),
        html.Div("Review Time (Launch to Save)",style={"fontSize":"13px","color":"#555","marginBottom":"10px"}),
        html.Div([html.Div([_card("3097m 59s","Total Avg","#c9a0dc"),_card("2106m 39s","USQ Avg","#4a90d9"),
            _card("3428m 26s","MR Avg","#7ec8e3"),html.Div("Map to Save",style={"fontSize":"11px","color":"#555","marginTop":"4px"}),
            html.Div([html.Div("0d 12h",style=sv),html.Span("Map to Save Avg",style={"fontSize":"11px"})],style=cs),
        ],style={"width":"170px","marginRight":"14px"}),
        html.Div([dcc.Graph(figure=fig,config={"displayModeBar":False})],style={"flex":"1"})],
        style={"display":"flex","alignItems":"flex-start"}),
        html.Div(_NOTE,style={"fontSize":"11px","color":"#888","marginTop":"8px","borderTop":"1px solid #eee","paddingTop":"8px"}),
    ],style=_SECBOX)


def usage_sections(rid=None):
    rs={"fontSize":"28px","fontWeight":"bold","color":"#333"}
    ss={"fontSize":"11px","color":"#888"}
    bs={"padding":"12px","border":"1px solid #ddd","borderRadius":"4px","marginRight":"14px","minWidth":"80px"}
    practice=html.Div([_sec_hdr("Usage by Practice",False,rid=rid),html.Div([
        html.Div([html.Div("1 / 1",style=rs),html.Div(["Usage Rate ",html.Span("100%",style={"color":"#4a90d9","fontWeight":"bold"})],style=ss)],style=bs),
        _tbl(["Practice","Total Reports","Saved"],[("Onc Hem of MSH","24","9")]),
    ],style={"display":"flex","alignItems":"flex-start"})],style={"padding":"20px","border":"1px solid #ddd","borderRadius":"6px","backgroundColor":"white","flex":"1"})
    vendor=html.Div([_sec_hdr("Usage by Vendor",False,rid=rid),html.Div([
        html.Div([html.Div("1 / 2",style=rs),html.Div(["Usage Rate ",html.Span("50%",style={"color":"#4a90d9","fontWeight":"bold"})],style=ss)],style=bs),
        _tbl(["Vendor","Usage \u2193"],[("Caris","39%"),("Foundation","0%")]),
    ],style={"display":"flex","alignItems":"flex-start"})],style={"padding":"20px","border":"1px solid #ddd","borderRadius":"6px","backgroundColor":"white","flex":"1"})
    return html.Div([practice,vendor],style={"display":"flex","gap":"16px","marginTop":"16px"})


def lifecycle_section(rid=None):
    fig=go.Figure(go.Sankey(arrangement="snap",
        node=dict(pad=20,thickness=20,
            label=["Opened for Review","USQ Launch","MR Launch","Edited (USQ)","Not Edited (USQ)",
                   "Edited (MR)","Not Edited (MR)","USQ Saved","MR Saved"],
            color=["#b8d4e3","#9b8ec4","#6ab0a3","#9b8ec4","#c4bfdc","#6ab0a3","#a0cfc4","#9b8ec4","#6ab0a3"]),
        link=dict(source=[0,0,1,1,2,2,3,4,5,6],target=[1,2,3,4,5,6,7,7,8,8],value=[4,6,3,1,5,1,3,1,5,1],
            color=["rgba(155,142,196,0.4)","rgba(106,176,163,0.4)","rgba(155,142,196,0.4)","rgba(196,191,220,0.4)",
                   "rgba(106,176,163,0.4)","rgba(160,207,196,0.4)","rgba(155,142,196,0.4)","rgba(196,191,220,0.4)",
                   "rgba(106,176,163,0.4)","rgba(160,207,196,0.4)"])))
    fig.update_layout(margin=dict(l=10,r=10,t=10,b=10),height=280,paper_bgcolor="white",font=dict(size=11))
    sv={"fontSize":"24px","fontWeight":"bold","color":"#333"}
    sl={"fontSize":"11px","color":"#888"}
    st={"textAlign":"center","flex":"1"}
    return html.Div([_sec_hdr("Lifecycle",False,rid=rid),
        html.Div([html.Div([html.Div("10",style=sv),html.Div("Opened for Review",style=sl)],style=st),
            html.Div([html.Div("10",style=sv),html.Div("Total Launches",style=sl)],style=st),
            html.Div([html.Div("8",style=sv),html.Div("Total Edited",style=sl),
                html.Div("Total Not Edited 2",style={"fontSize":"10px","color":"#aaa"})],style=st),
            html.Div([html.Div("10",style=sv),html.Div("Total Saved",style=sl)],style=st),
        ],style={"display":"flex","marginBottom":"6px"}),
        dcc.Graph(figure=fig,config={"displayModeBar":False}),
        html.Div(_NOTE,style={"fontSize":"11px","color":"#888","marginTop":"4px","borderTop":"1px solid #eee","paddingTop":"8px"}),
    ],style=_SECBOX)


def edits_section(rid=None):
    diag=[("ALL","5/8"),("Uterine Neoplasms - Endometrial Carcinoma","3/6"),
          ("Pancreatic Adenocarcinoma","1/1"),("cancer","1/1")]
    infer=[("ALL","7"),("TMB (Tumor mutational burden)","6"),("c-Met overexpression by IHC","1"),
           ("ALK rearrangement status","0"),("BRAF V600E status","0"),("EGFR status","0"),
           ("ERBB2 (HER2) mutation status","0"),("KRAS status","0")]
    edits=[("ALL","ALL"),("TMB high","Unknown"),("(no value)","<3+ intensity OR <50%"),
           ("(no value)","Unknown"),("TMB high","(no value)"),("TMB intermediate","TMB high"),
           ("TMB intermediate","Unknown")]
    return html.Div([_sec_hdr("Edits",False,rid=rid),
        html.Div([html.Div([_tbl(["Diagnosis","Edit/Total Reports"],diag)],style={"flex":"1","marginRight":"10px"}),
            html.Div([_tbl(["Inference Group","Total Edits"],infer)],style={"flex":"1","marginRight":"10px"}),
            html.Div([_tbl(["Original Value","Edited Value"],edits)],style={"flex":"1"}),
        ],style={"display":"flex","alignItems":"flex-start"}),
    ],style=_SECBOX)


def export_modal_dialog():
    return html.Div([
        html.Div([
            html.Div([
                html.H3("Select Reports to Export",
                    style={"margin":"0","fontSize":"18px","color":"#333"}),
                html.Span("\u00d7",id="btn-export-close",n_clicks=0,
                    style={"fontSize":"22px","cursor":"pointer","color":"#888","lineHeight":"1"}),
            ],style={"display":"flex","justifyContent":"space-between","alignItems":"center","marginBottom":"12px"}),
            html.P("Choose one or more reports to include in your export.",
                style={"fontSize":"13px","color":"#555","margin":"0 0 3px"}),
            html.P("The generated report will reflect the currently applied filters.",
                style={"fontSize":"13px","color":"#555","margin":"0 0 14px"}),
            html.Hr(style={"border":"none","borderTop":"1px solid #eee","margin":"0 0 10px"}),
            dcc.Checklist(id="export-checklist",
                options=[{"label":"  Select All","value":"all"},
                         {"label":"  Full Report Dataset","value":"full_report"},
                         {"label":"  Usage by Practice","value":"usage_practice"},
                         {"label":"  Full Report Dataset - Biomarker Details","value":"biomarker_details"},
                         {"label":"  Usage by Vendor","value":"usage_vendor"},
                         {"label":"  Edits by Diagnosis","value":"edits_diagnosis"},
                         {"label":"  Edits by Biomarker","value":"edits_biomarker"}],
                value=["full_report","usage_practice"],
                style={"fontSize":"13px","lineHeight":"36px"},
                inputStyle={"marginRight":"8px"}),
            html.Hr(style={"border":"none","borderTop":"1px solid #eee","margin":"14px 0"}),
            html.Div([
                html.Button("CANCEL",id="btn-export-cancel",n_clicks=0,
                    style={"border":"1px solid #ccc","backgroundColor":"white","color":"#555",
                           "borderRadius":"4px","padding":"8px 24px","fontSize":"13px",
                           "cursor":"pointer","marginRight":"10px"}),
                html.Button("NEXT",id="btn-export-next",n_clicks=0,
                    style={"border":"none","backgroundColor":"#2a5db0","color":"white",
                           "borderRadius":"4px","padding":"8px 28px","fontSize":"13px",
                           "cursor":"pointer"}),
            ],style={"display":"flex","justifyContent":"flex-end"}),
        ],style=_BOX),
    ],id="export-modal",style=_OVERLAY_HIDE)


# ── modal: new schedule ───────────────────────────────────────────────────
def schedule_modal_dialog():
    lbl = {"fontSize":"13px","fontWeight":"bold","color":"#333","marginBottom":"6px"}
    inp = {"border":"1px solid #ccc","borderRadius":"4px","padding":"6px 10px","fontSize":"12px"}
    dot_g = {"width":"18px","height":"18px","borderRadius":"50%","backgroundColor":"#2e7d32","display":"inline-block"}
    dot_x = {"width":"18px","height":"18px","borderRadius":"50%","backgroundColor":"#999","display":"inline-block"}
    line  = {"flex":"1","height":"2px","backgroundColor":"#ccc","margin":"0 8px"}
    return html.Div([
        html.Div([
            # title bar
            html.Div([
                html.Span("New Schedule",style={"fontSize":"16px","fontWeight":"bold","color":"#333"}),
                html.Span("\u00d7",id="btn-sched-close",n_clicks=0,
                    style={"fontSize":"22px","cursor":"pointer","color":"#888"}),
            ],style={"display":"flex","justifyContent":"space-between","alignItems":"center",
                     "borderBottom":"1px solid #eee","paddingBottom":"10px","marginBottom":"6px"}),
            # subtitle
            html.Div([
                html.Span("Specify report details and scheduling preferences",
                    style={"fontSize":"13px","fontWeight":"bold","color":"#333"}),
                html.Span("  \u25cf Required",style={"fontSize":"11px","color":"#c00","marginLeft":"6px"}),
            ],style={"marginBottom":"16px"}),
            # stepper dots
            html.Div([
                html.Div(style=dot_g),html.Div(style=line),
                html.Div(style=dot_x),html.Div(style=line),
                html.Div(style=dot_x),
            ],style={"display":"flex","alignItems":"center","marginBottom":"4px"}),
            html.Div([
                html.Span("Create a Schedule",style={"fontSize":"11px","color":"#2e7d32","flex":"1"}),
                html.Span("Define Recipients",style={"fontSize":"11px","color":"#999","flex":"1","textAlign":"center"}),
                html.Span("Review and Confirm",style={"fontSize":"11px","color":"#999","flex":"1","textAlign":"right"}),
            ],style={"display":"flex","marginBottom":"20px"}),
            # schedule name
            html.Div([
                html.Div(["Schedule Name ",html.Span("\u25cf",style={"color":"#c00","fontSize":"8px"})],style=lbl),
                dcc.Input(id="sched-name",placeholder="Type something",style=dict(inp,width="240px")),
            ],style={"marginBottom":"18px"}),
            # frequency
            html.Div([
                html.Div(["Frequency and Timing ",html.Span("\u25cf",style={"color":"#c00","fontSize":"8px"})],style=lbl),
                html.Div([
                    html.Div([
                        html.Div("Recurrence",style={"fontSize":"11px","color":"#666","marginBottom":"3px"}),
                        dcc.Dropdown(id="sched-recurrence",options=[{"label":"Daily","value":"daily"},{"label":"Weekly","value":"weekly"},
                            {"label":"Monthly","value":"monthly"}],value="daily",clearable=False,
                            style={"width":"110px","fontSize":"12px"}),
                    ],style={"marginRight":"10px"}),
                    html.Span("at",style={"fontSize":"12px","color":"#555","alignSelf":"flex-end","paddingBottom":"8px","marginRight":"8px"}),
                    html.Div([
                        html.Div("Hour",style={"fontSize":"11px","color":"#666","marginBottom":"3px"}),
                        dcc.Dropdown(id="sched-hour",options=[{"label":str(h),"value":h} for h in range(24)],
                            value=18,clearable=False,style={"width":"70px","fontSize":"12px"}),
                    ],style={"marginRight":"4px"}),
                    html.Span(":",style={"fontSize":"14px","alignSelf":"flex-end","paddingBottom":"8px","marginRight":"4px"}),
                    html.Div([
                        html.Div("Minute",style={"fontSize":"11px","color":"#666","marginBottom":"3px"}),
                        dcc.Dropdown(id="sched-minute",options=[{"label":f"{m:02d}","value":m} for m in range(60)],
                            value=17,clearable=False,style={"width":"75px","fontSize":"12px"}),
                    ],style={"marginRight":"10px"}),
                    html.Span("(UTC+05:30) IST",style={"fontSize":"12px","color":"#555","alignSelf":"flex-end","paddingBottom":"8px"}),
                ],style={"display":"flex","alignItems":"flex-start","marginBottom":"14px"}),
                html.Div([
                    html.Div([
                        html.Div("Schedule Starts on",style={"fontSize":"11px","color":"#666","marginBottom":"3px"}),
                        dcc.DatePickerSingle(id="sched-starts",date="2026-05-12",display_format="MM/DD/YYYY",
                            style={"fontSize":"12px"}),
                    ],style={"marginRight":"14px"}),
                    html.Div([
                        html.Div("Schedule Ends on",style={"fontSize":"11px","color":"#666","marginBottom":"3px"}),
                        dcc.DatePickerSingle(id="sched-ends",placeholder="mm/dd/yyyy",display_format="MM/DD/YYYY",
                            style={"fontSize":"12px"}),
                    ],style={"marginRight":"14px"}),
                    html.Div([
                        dcc.Checklist(id="sched-no-end",options=[{"label":" No end date","value":"no_end"}],
                            value=[],style={"fontSize":"12px"},inputStyle={"marginRight":"4px"}),
                    ],style={"alignSelf":"flex-end","paddingBottom":"4px"}),
                ],style={"display":"flex","alignItems":"flex-start"}),
            ],style={"marginBottom":"18px"}),
            html.Hr(style={"border":"none","borderTop":"1px solid #eee","margin":"8px 0 16px"}),
            html.Div([
                html.Button("CANCEL",id="btn-sched-cancel",n_clicks=0,
                    style={"border":"1px solid #ccc","backgroundColor":"white","color":"#555",
                           "borderRadius":"4px","padding":"8px 24px","fontSize":"13px",
                           "cursor":"pointer","marginRight":"10px"}),
                html.Button("NEXT",id="btn-sched-next",n_clicks=0,
                    style={"border":"none","backgroundColor":"#2a5db0","color":"white",
                           "borderRadius":"4px","padding":"8px 28px","fontSize":"13px",
                           "cursor":"pointer"}),
            ],style={"display":"flex","justifyContent":"flex-end"}),
        ],style=_BOX_LG),
    ],id="schedule-modal",style=_OVERLAY2_HIDE)


# ── detail page ───────────────────────────────────────────────────────────
_GEN_TH={"padding":"10px 12px","fontSize":"12px","fontWeight":"bold","color":"#c8a000",
    "textAlign":"left","borderBottom":"2px solid #ddd","backgroundColor":"#fff"}
_GEN_TD={"padding":"10px 12px","fontSize":"12px","color":"#333","borderBottom":"1px solid #eee"}

def _build_gen_table():
    rows=list(reversed(_GENERATED_REPORTS))
    if rows:
        tbody=html.Tbody([
            html.Tr([
                html.Td(r.get("category","General"),style=_GEN_TD),
                html.Td(r.get("title",""),style=_GEN_TD),
                html.Td(r.get("generated_by",""),style=_GEN_TD),
                html.Td(r.get("generated_on",""),style=_GEN_TD),
                html.Td(r.get("report_type","Scheduled"),style=_GEN_TD),
                html.Td(r.get("schedule_name",""),style=_GEN_TD),
                html.Td(r.get("status","Generated"),style=_GEN_TD),
                html.Td(html.Button("\u2B07",id={"type":"btn-dl","index":i},n_clicks=0,
                    style={"border":"none","background":"none","color":"#c8a000","cursor":"pointer","fontSize":"16px"}),
                    style={**_GEN_TD,"textAlign":"center"}),
                html.Td(html.Button("\u2716",id={"type":"btn-del","index":i},n_clicks=0,
                    style={"border":"none","background":"none","color":"#c00","cursor":"pointer","fontSize":"14px"}),
                    style={**_GEN_TD,"textAlign":"center"}),
            ],style={"backgroundColor":"#f9f9f9" if i%2 else "white"}) for i,r in enumerate(rows)])
    else:
        tbody=html.Tbody([html.Tr([html.Td(
            "No generated reports yet. Click GENERATE on a report detail page to add one.",
            colSpan="9",style={"padding":"40px","textAlign":"center","color":"#888","fontSize":"14px"})])])
    cnt=len(rows)
    return cnt, html.Table([
        html.Thead(html.Tr([
            html.Th("Report Category",style=_GEN_TH),html.Th("Report Title",style=_GEN_TH),
            html.Th("Generated By",style=_GEN_TH),html.Th("Generated On",style=_GEN_TH),
            html.Th("Report Type \u25bc",style=_GEN_TH),html.Th("Schedule Name",style=_GEN_TH),
            html.Th("Status",style=_GEN_TH),
            html.Th("Download",style={**_GEN_TH,"textAlign":"center"}),
            html.Th("Delete",style={**_GEN_TH,"textAlign":"center"}),
        ])),tbody],style={"width":"100%","borderCollapse":"collapse"})

def _query_report_table():
    """Query dev.gold.iKnowMed_G2_Report and return (headers, rows)."""
    try:
        from databricks.sdk import WorkspaceClient
        wh=os.environ.get("DATABRICKS_WAREHOUSE_ID","")
        if not wh: return None
        w=WorkspaceClient()
        r=w.statement_execution.execute_statement(
            warehouse_id=wh,statement="SELECT * FROM dev.gold.iKnowMed_G2_Report",wait_timeout="30s")
        if r.result and r.result.data_array:
            hdrs=[c.name for c in r.manifest.schema.columns]
            return hdrs, r.result.data_array
    except Exception as e:
        print(f"Download query failed: {e}")
    return None

_SCH_TH={"padding":"8px 10px","fontSize":"11px","fontWeight":"bold","color":"#c8a000",
    "textAlign":"left","borderBottom":"2px solid #ddd","backgroundColor":"#fff","whiteSpace":"nowrap"}
_SCH_TD={"padding":"8px 10px","fontSize":"11px","color":"#333","borderBottom":"1px solid #eee",
    "maxWidth":"140px","overflow":"hidden","textOverflow":"ellipsis","whiteSpace":"nowrap"}
_PAUSE_S={"border":"1px solid #888","backgroundColor":"white","color":"#555","borderRadius":"3px",
    "padding":"3px 10px","fontSize":"11px","cursor":"pointer"}
_GENSCH_S={"border":"none","backgroundColor":"#2e7d32","color":"white","borderRadius":"3px",
    "padding":"4px 10px","fontSize":"10px","fontWeight":"bold","cursor":"pointer","letterSpacing":"0.5px"}

def _build_sched_table():
    rows=list(reversed(_SCHEDULED_REPORTS))
    if rows:
        tbody=html.Tbody([
            html.Tr([
                html.Td(r.get("category","General"),style=_SCH_TD),
                html.Td(r.get("report_title",""),style=_SCH_TD),
                html.Td(r.get("schedule_name",""),style=_SCH_TD),
                html.Td(r.get("scheduled_by",""),style=_SCH_TD),
                html.Td(r.get("scheduled_time",""),style=_SCH_TD),
                html.Td(html.Span(r.get("frequency","Daily"),style={
                    "padding":"2px 8px","borderRadius":"3px","fontSize":"10px",
                    "backgroundColor":"#e8f5e9" if r.get("frequency")=="Daily" else "#fff3e0",
                    "color":"#2e7d32" if r.get("frequency")=="Daily" else "#e65100"}),style=_SCH_TD),
                html.Td(r.get("updated_on",""),style=_SCH_TD),
                html.Td(r.get("last_delivery",""),style=_SCH_TD),
                html.Td(html.Button("\u23f8 Pause",style=_PAUSE_S),style={**_SCH_TD,"textAlign":"center"}),
                html.Td(html.Button("\u270e",id={"type":"btn-sched-edit","index":i},n_clicks=0,
                    style={"border":"none","background":"none","color":"#4a90d9","cursor":"pointer","fontSize":"14px"}),
                    style={**_SCH_TD,"textAlign":"center"}),
                html.Td(html.Button("GENERATE",id={"type":"btn-sched-gen","index":i},n_clicks=0,
                    style=_GENSCH_S),style={**_SCH_TD,"textAlign":"center"}),
                html.Td(html.Button("\u2716",id={"type":"btn-sched-del","index":i},n_clicks=0,
                    style={"border":"none","background":"none","color":"#c00","cursor":"pointer","fontSize":"12px"}),
                    style={**_SCH_TD,"textAlign":"center"}),
            ],style={"backgroundColor":"#fffde7" if r.get("_highlight") else ("#f9f9f9" if i%2 else "white")})
            for i,r in enumerate(rows)])
    else:
        tbody=html.Tbody([html.Tr([html.Td(
            "No scheduled reports yet. Use the Schedule button on a report detail page to create one.",
            colSpan="12",style={"padding":"40px","textAlign":"center","color":"#888","fontSize":"14px"})])])
    cnt=len(rows)
    return cnt, html.Table([
        html.Thead(html.Tr([
            html.Th("Report Category",style=_SCH_TH),html.Th("Report Title",style=_SCH_TH),
            html.Th("Schedule Name",style=_SCH_TH),html.Th("Scheduled By",style=_SCH_TH),
            html.Th("Scheduled Time",style=_SCH_TH),html.Th("Frequency",style=_SCH_TH),
            html.Th("Updated On (by)",style=_SCH_TH),html.Th("Last Delivery",style=_SCH_TH),
            html.Th("Pause Schedule",style={**_SCH_TH,"textAlign":"center"}),
            html.Th("Edit",style={**_SCH_TH,"textAlign":"center"}),
            html.Th("",style={**_SCH_TH,"textAlign":"center"}),
            html.Th("Delete",style={**_SCH_TH,"textAlign":"center"}),
        ])),tbody],style={"width":"100%","borderCollapse":"collapse"})

def scheduled_reports_page():
    cnt, tbl = _build_sched_table()
    total=max(cnt,1)
    pages=max((total+14)//15,1)
    pg_btn={"border":"1px solid #ddd","backgroundColor":"white","padding":"4px 10px",
            "fontSize":"12px","cursor":"pointer","borderRadius":"3px","marginRight":"3px"}
    pg_act={**pg_btn,"backgroundColor":"#c8a000","color":"white","border":"1px solid #c8a000"}
    page_nums=[html.Span(str(p+1),style=pg_act if p==0 else pg_btn) for p in range(min(pages,5))]
    if pages>5:
        page_nums+=[html.Span("...",style={"margin":"0 4px","fontSize":"12px"}),
                    html.Span(str(pages),style=pg_btn)]
    return html.Div([
        sub_tabs_bar("scheduled"),
        html.Div([
            dcc.Input(placeholder="Search...",style={"border":"1px solid #ccc","borderRadius":"3px",
                "padding":"6px 12px","fontSize":"12px","width":"220px"}),
            html.Button("\u2315",style={"border":"none","backgroundColor":"#4a90d9",
                "color":"white","borderRadius":"3px","padding":"6px 10px","marginLeft":"4px","cursor":"pointer"}),
            html.Button("\u21bb",style={"border":"1px solid #ccc","backgroundColor":"white",
                "borderRadius":"3px","padding":"6px 10px","marginLeft":"4px","cursor":"pointer"}),
            html.Div(style={"flex":"1"}),
            html.Span("\u276e",style={"cursor":"pointer","marginRight":"6px","color":"#888"}),
            *page_nums,
            html.Span("\u276f",style={"cursor":"pointer","marginLeft":"4px","color":"#888"}),
            html.Span("Show",style={"fontSize":"12px","color":"#555","marginLeft":"12px","marginRight":"4px"}),
            dcc.Dropdown(options=[{"label":"15","value":15},{"label":"25","value":25},{"label":"50","value":50}],
                value=15,clearable=False,style={"width":"60px","fontSize":"12px","marginRight":"4px"}),
            html.Span("Entries",style={"fontSize":"12px","color":"#555"}),
        ],style={"display":"flex","alignItems":"center","padding":"10px 16px",
                 "backgroundColor":"#f5f5f5","borderBottom":"1px solid #ddd"}),
        html.Div(id="sched-table-container",children=[tbl],
            style={"padding":"0 16px","backgroundColor":"white","minHeight":"calc(100vh - 220px)","overflowX":"auto"}),
        html.Span(id="sched-count",children=f"{cnt}",style={"display":"none"}),
    ])


def generated_reports_page():
    cnt, tbl = _build_gen_table()
    return html.Div([
        sub_tabs_bar("generated"),
        html.Div([
            dcc.Input(placeholder="Search...",style={"border":"1px solid #ccc","borderRadius":"3px",
                "padding":"6px 12px","fontSize":"12px","width":"200px"}),
            html.Button("\u2315",style={"border":"1px solid #ccc","backgroundColor":"#4a90d9",
                "color":"white","borderRadius":"3px","padding":"6px 10px","marginLeft":"4px","cursor":"pointer"}),
            html.Button("\u21bb",style={"border":"1px solid #ccc","backgroundColor":"white",
                "borderRadius":"3px","padding":"6px 10px","marginLeft":"4px","cursor":"pointer"}),
            html.Div(style={"flex":"1"}),
            html.Span(id="gen-count",children=f"{cnt} entries",style={"fontSize":"12px","color":"#888","marginRight":"12px"}),
            html.Span("Show",style={"fontSize":"12px","color":"#555","marginRight":"4px"}),
            dcc.Dropdown(options=[{"label":"15","value":15},{"label":"25","value":25}],
                value=15,clearable=False,style={"width":"60px","fontSize":"12px","marginRight":"4px"}),
            html.Span("Entries",style={"fontSize":"12px","color":"#555"}),
        ],style={"display":"flex","alignItems":"center","padding":"10px 16px",
                 "backgroundColor":"#f5f5f5","borderBottom":"1px solid #ddd"}),
        html.Div(id="gen-table-container",children=[tbl],
            style={"padding":"0 16px","backgroundColor":"white","minHeight":"calc(100vh - 220px)"}),
        dcc.Download(id="download-report"),
    ])


def detail_page(report_id,tab=None):
    r = REPORT_BY_ID.get(report_id)
    if not r:
        return html.Div("Report not found.",style={"padding":"40px","fontSize":"16px","color":"#888"})
    data = get_report_data(report_id)
    rid = report_id
    if tab:
        _tn=["Volume","Time to Completion","Usage by Practice","Usage by Vendor","Lifecycle","Edits"]
        _tk=["volume","ttc","practice","vendor","lifecycle","edits"]
        _is={"padding":"8px 14px","fontSize":"13px","border":"1px solid #ddd","borderBottom":"none",
             "borderRadius":"4px 4px 0 0","marginRight":"3px","backgroundColor":"#f5f5f5",
             "color":"#555","textDecoration":"none"}
        _as=dict(_is,backgroundColor="white",fontWeight="bold",color="#333")
        _tbar=html.Div([dcc.Link(n,href=f"/report/{rid}/{k}",style=_as if k==tab else _is) for n,k in zip(_tn,_tk)],
            style={"display":"flex","alignItems":"flex-end","borderBottom":"1px solid #ddd"})
        if tab=="volume": _s=volume_section(data)
        elif tab=="ttc": _s=time_to_completion_section()
        elif tab=="practice": _s=usage_sections().children[0]
        elif tab=="vendor": _s=usage_sections().children[1]
        elif tab=="lifecycle": _s=lifecycle_section()
        elif tab=="edits": _s=edits_section()
        else: _s=volume_section(data)
        _mc=[_tbar,_s]
    else:
        _mc=[volume_section(data,rid=rid),time_to_completion_section(rid=rid),
             usage_sections(rid=rid),lifecycle_section(rid=rid),edits_section(rid=rid)]
    return html.Div([
        sub_tabs_bar(),
        html.Div([
            dcc.Link("Reports",href="/",style={"fontSize":"13px","color":"#555","textDecoration":"none"}),
            html.Span("  \u203a  ",style={"color":"#999","fontSize":"14px"}),
            html.Span(r["name"],style={"fontSize":"13px","color":"#333"}),
        ],style={"padding":"10px 16px","backgroundColor":"#f5f5f5","borderBottom":"1px solid #ddd"}),
        html.Div([
            filter_sidebar_panel(),
            html.Div([
                dcc.Link("\u2190 Back to Main Dashboard",href="/",
                    style={"fontSize":"13px","color":"#4a90d9","textDecoration":"none"}),
                html.H2(r["name"],style={"margin":"6px 0 2px","fontSize":"22px","color":"#333"}),
                html.Div("Data Last Extracted: 08/16/2025 at 12:00am PST",
                    style={"fontSize":"12px","color":"#888","marginBottom":"14px"}),
                *_mc,
            ],style={"flex":"1","padding":"16px 20px","overflowY":"auto","height":"calc(100vh - 165px)"}),
        ],style={"display":"flex","backgroundColor":"#f9f9f9"}),
        export_modal_dialog(),
        schedule_modal_dialog(),
    ])


# ── layout + callbacks ────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Location(id="url",refresh=False),
    header_bar(),
    tab_bar(),
    html.Div(id="page-content"),
],style={"fontFamily":"Arial, Helvetica, sans-serif","margin":"0",
         "minHeight":"100vh","backgroundColor":"#ececec"})


@app.callback(Output("page-content","children"),Input("url","pathname"))
def display_page(pathname):
    if pathname=="/generated":
        return generated_reports_page()
    if pathname=="/scheduled":
        return scheduled_reports_page()
    if pathname and pathname.startswith("/report/"):
        parts=pathname.rstrip("/").split("/")
        try: rid=int(parts[2])
        except (ValueError,IndexError): return main_page()
        tab=parts[3] if len(parts)>3 else None
        return detail_page(rid,tab)
    return main_page()


@app.callback(Output("reports-container","children"),Input("search-reports","value"),
              prevent_initial_call=True)
def filter_reports(q):
    cats = _build_categories(get_all_reports())
    if not q:
        return [category_card(c,r) for c,r in cats.items()]
    ql = q.lower()
    cards = []
    for c,rpts in cats.items():
        m = [r for r in rpts if ql in r["name"].lower()]
        if m:
            cards.append(category_card(c,m))
    return cards or [html.Div("No reports match your search.",
                              style={"padding":"20px","color":"#888","fontSize":"14px"})]


@app.callback(Output("export-modal","style"),
    [Input("btn-schedule-open","n_clicks"),Input("btn-export-close","n_clicks"),
     Input("btn-export-cancel","n_clicks"),Input("btn-export-next","n_clicks")],
    prevent_initial_call=True)
def toggle_export(*_):
    return _OVERLAY_SHOW if ctx.triggered_id == "btn-schedule-open" else _OVERLAY_HIDE


@app.callback(Output("schedule-modal","style"),
    [Input("btn-export-next","n_clicks"),Input("btn-sched-close","n_clicks"),
     Input("btn-sched-cancel","n_clicks"),Input("btn-sched-next","n_clicks")],
    prevent_initial_call=True)
def toggle_schedule(*_):
    return _OVERLAY2_SHOW if ctx.triggered_id == "btn-export-next" else _OVERLAY2_HIDE



@app.callback(Output("url","pathname",allow_duplicate=True),
    Input("btn-sched-next","n_clicks"),
    [State("url","pathname"),State("sched-name","value"),State("sched-recurrence","value"),
     State("sched-hour","value"),State("sched-minute","value"),
     State("sched-starts","date"),State("sched-ends","date"),State("sched-no-end","value")],
    prevent_initial_call=True)
def handle_schedule(n,pathname,sname,recurrence,hour,minute,starts,ends,no_end):
    if not n: return no_update
    try:
        parts=pathname.rstrip("/").split("/")
        rid=int(parts[2])
    except (ValueError,IndexError): return no_update
    rpts=get_all_reports()
    rmap={r["id"]:r for r in rpts}
    r=rmap.get(rid)
    if not r: return no_update
    sname=sname or "iKnowMed_G2_Report_veiw"
    recurrence=recurrence or "daily"
    hour=hour if hour is not None else 18
    minute=minute if minute is not None else 17
    # Build cron: seconds minutes hours day-of-month month day-of-week
    if recurrence=="daily": cron=f"0 {minute} {hour} * * ?"
    elif recurrence=="weekly": cron=f"0 {minute} {hour} ? * 2"
    else: cron=f"0 {minute} {hour} 1 * ?"
    # Update job schedule (clear any existing trigger) and run immediately
    job_status="Active"
    try:
        from databricks.sdk import WorkspaceClient
        from databricks.sdk.service.jobs import JobSettings, CronSchedule
        w=WorkspaceClient()
        w.jobs.update(job_id=int(_JOB_ID),
            new_settings=JobSettings(
                schedule=CronSchedule(quartz_cron_expression=cron,timezone_id="Asia/Kolkata")),
            fields_to_remove=["trigger","continuous"])
        print(f"Job schedule set: {cron} (Asia/Kolkata)")
        run=w.jobs.run_now(job_id=int(_JOB_ID))
        print(f"Job triggered: run_id={run.run_id}")
    except Exception as e:
        print(f"Job trigger failed: {e}")
        job_status="Pending"
    now=datetime.now()
    freq_label=recurrence.capitalize()
    time_label=f"{hour:02d}:{minute:02d} IST"
    starts_label=starts or now.strftime("%m/%d/%Y")
    ends_label="No end date" if (no_end and "no_end" in no_end) else (ends or "")
    gen_ids={1,2,3,4,5,6,7,9,10,17,18,19,20,21,22,23}
    wl_ids={8,11,12,15,16}
    cat="General" if rid in gen_ids else ("Worklist Queue" if rid in wl_ids else "Audit & Specialty")
    _SCHEDULED_REPORTS.append({
        "category":cat,
        "report_title":r["name"],
        "schedule_name":sname,
        "scheduled_by":"sudhir.nakkana",
        "scheduled_time":time_label,
        "frequency":freq_label,
        "updated_on":now.strftime("%m-%d-%Y") + " (sudhir.n...)",
        "last_delivery":now.strftime("%m-%d-%Y %I:%M %p"),
        "starts_on":starts_label,
        "ends_on":ends_label,
        "status":job_status,
        "_highlight":True,
        "_rid":rid,
    })
    return "/scheduled"


@app.callback(Output("url","pathname",allow_duplicate=True),
    Input("btn-generate","n_clicks"),State("url","pathname"),prevent_initial_call=True)
def handle_generate(n,pathname):
    if not n: return no_update
    try:
        parts=pathname.rstrip("/").split("/")
        rid=int(parts[2])
    except (ValueError,IndexError): return no_update
    rpts=get_all_reports()
    rmap={r["id"]:r for r in rpts}
    r=rmap.get(rid)
    if not r: return no_update
    gen_ids={1,2,3,4,5,6,7,9,10,17,18,19,20,21,22,23}
    wl_ids={8,11,12,15,16}
    cat="General" if rid in gen_ids else ("Worklist Queue" if rid in wl_ids else "Audit & Specialty")
    _GENERATED_REPORTS.append({
        "category":cat,"title":r["name"],
        "generated_by":"sudhir.nakkana@fractal.ai",
        "generated_on":datetime.now().strftime("%m-%d-%Y %I:%M %p"),
        "report_type":"Scheduled","schedule_name":"","status":"Generated"})
    return "/generated"


@app.callback(
    [Output("gen-table-container","children"),Output("gen-count","children")],
    Input({"type":"btn-del","index":ALL},"n_clicks"),prevent_initial_call=True)
def delete_generated(n_clicks_list):
    trig=ctx.triggered_id
    if trig and isinstance(trig,dict) and trig["type"]=="btn-del":
        idx=trig["index"]
        real=len(_GENERATED_REPORTS)-1-idx
        if 0<=real<len(_GENERATED_REPORTS):
            _GENERATED_REPORTS.pop(real)
    cnt,tbl=_build_gen_table()
    return [tbl],f"{cnt} entries"


@app.callback(
    Output("download-report","data"),
    Input({"type":"btn-dl","index":ALL},"n_clicks"),prevent_initial_call=True)
def download_report(n_clicks_list):
    trig=ctx.triggered_id
    if not trig or not isinstance(trig,dict) or trig["type"]!="btn-dl":
        return no_update
    if not any(n_clicks_list):
        return no_update
    qr=_query_report_table()
    if qr:
        hdrs,rows=qr
    else:
        hdrs=["Diagnosis","Inference_Group_and_Total_Edits","Original_Value_Edited_Value","vendor","Practice"]
        rows=[["Sample","Sample","Sample","Sample","Sample"]]
    buf=io.StringIO()
    w=csv.writer(buf)
    w.writerow(hdrs)
    for r in rows:
        w.writerow(r)
    zb=io.BytesIO()
    with zipfile.ZipFile(zb,"w",zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("iKnowMed_G2_Report.csv",buf.getvalue())
    return dcc.send_bytes(zb.getvalue(),"iKnowMed_G2_Report.zip")


# --- Scheduled Reports: Delete ---
@app.callback(
    Output("sched-table-container","children"),
    Input({"type":"btn-sched-del","index":ALL},"n_clicks"),prevent_initial_call=True)
def sched_delete(n_clicks_list):
    trig=ctx.triggered_id
    if trig and isinstance(trig,dict) and trig["type"]=="btn-sched-del":
        idx=trig["index"]
        real=len(_SCHEDULED_REPORTS)-1-idx
        if 0<=real<len(_SCHEDULED_REPORTS):
            _SCHEDULED_REPORTS.pop(real)
    _,tbl=_build_sched_table()
    return [tbl]

# --- Scheduled Reports: Generate → adds to Generated Reports and redirects ---
@app.callback(
    Output("url","pathname",allow_duplicate=True),
    Input({"type":"btn-sched-gen","index":ALL},"n_clicks"),prevent_initial_call=True)
def sched_generate(n_clicks_list):
    trig=ctx.triggered_id
    if not trig or not isinstance(trig,dict) or trig["type"]!="btn-sched-gen":
        return no_update
    if not any(n_clicks_list): return no_update
    idx=trig["index"]
    real=len(_SCHEDULED_REPORTS)-1-idx
    if 0<=real<len(_SCHEDULED_REPORTS):
        r=_SCHEDULED_REPORTS[real]
        now=datetime.now()
        _GENERATED_REPORTS.append({
            "category":r.get("category","General"),
            "title":r.get("report_title",""),
            "generated_by":r.get("scheduled_by","sudhir.nakkana"),
            "generated_on":now.strftime("%m-%d-%Y %I:%M %p"),
            "report_type":"Scheduled",
            "schedule_name":r.get("schedule_name",""),
            "status":"Generated",
        })
        return "/generated"
    return no_update

# --- Scheduled Reports: Edit → navigate to report detail ---
@app.callback(
    Output("url","pathname",allow_duplicate=True),
    Input({"type":"btn-sched-edit","index":ALL},"n_clicks"),prevent_initial_call=True)
def sched_edit(n_clicks_list):
    trig=ctx.triggered_id
    if not trig or not isinstance(trig,dict) or trig["type"]!="btn-sched-edit":
        return no_update
    if not any(n_clicks_list): return no_update
    idx=trig["index"]
    real=len(_SCHEDULED_REPORTS)-1-idx
    if 0<=real<len(_SCHEDULED_REPORTS):
        r=_SCHEDULED_REPORTS[real]
        rid=r.get("_rid",7)
        return f"/report/{rid}"
    return no_update


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=False)
