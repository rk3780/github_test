"""Report catalog and configuration constants."""

# ── Report Catalog (source: iknowmed-reports hardcoded list) ────────────────────
REPORT_CATALOG = [
    {"id": 1,  "name": "Supportive Care Interventions Report",               "category": "General"},
    {"id": 2,  "name": "Decision Support Interventions Feedback Report",      "category": "General"},
    {"id": 3,  "name": "Patient Charts Merged Report",                        "category": "General"},
    {"id": 4,  "name": "Depression Screening Needed and Completed Report",    "category": "General"},
    {"id": 17, "name": "Visit List Report",                                   "category": "General"},
    {"id": 18, "name": "Charge Capture",                                      "category": "General"},
    {"id": 19, "name": "Patient List",                                        "category": "General"},
    {"id": 20, "name": "Clinical Profile Chart Alert",                        "category": "General"},
    {"id": 21, "name": "Order History",                                       "category": "General"},
    {"id": 22, "name": "Diagnosis",                                           "category": "General"},
    {"id": 26, "name": "Unfinished Charting",                                 "category": "General"},
    {"id": 8,  "name": "Outbound Fax Worklist Queue Report",                  "category": "Worklist Queues"},
    {"id": 11, "name": "Ins Auth Fin Counseling Worklist Queue Report",       "category": "Worklist Queues"},
    {"id": 12, "name": "Orders Queue Worklist Queue Report",                  "category": "Worklist Queues"},
    {"id": 15, "name": "Attach Documents Worklist Queue Productivity Report", "category": "Worklist Queues"},
    {"id": 16, "name": "Attach Documents Worklist Queue Audit Report",        "category": "Worklist Queues"},
    {"id": 6,  "name": "Medication Administration Record with Admix Report",  "category": "Medication & Orders"},
    {"id": 9,  "name": "Trending Pain Scores Report",                         "category": "Medication & Orders"},
    {"id": 10, "name": "Pain Scale and PDMP Evaluation Report",               "category": "Medication & Orders"},
    {"id": 13, "name": "Regimen Orders Report",                               "category": "Medication & Orders"},
    {"id": 25, "name": "Precision Medicine Orders & Results",                  "category": "Medication & Orders"},
    {"id": 14, "name": "Prescription Audit Report",                           "category": "Audit Reports"},
    {"id": 5,  "name": "Task & Time Cumulative Dashboard",                    "category": "Task & Time"},
    {"id": 23, "name": "Task and Time Capture Report",                        "category": "Task & Time"},
    {"id": 7,  "name": "iKnowMed G1 Report",                                 "category": "Integrations"},
    {"id": 24, "name": "Genospace iKM Integration",                           "category": "Integrations"},
]

CATEGORY_ORDER = ["General", "Worklist Queues", "Medication & Orders", "Audit Reports", "Task & Time", "Integrations"]

CATEGORY_ICONS = {
    "General": "📋",
    "Worklist Queues": "📥",
    "Medication & Orders": "💊",
    "Audit Reports": "🔍",
    "Task & Time": "⏱️",
    "Integrations": "🔗",
}

# ── Generic Report Configurations (all 25 reports) ────────────────────────────
# archetype: "dashboard" = KPI cards + multiple charts + table
#            "table_list" = summary stats + 1 chart + paginated table
#            "summary" = KPI cards + pie + bar + small table
REPORT_CONFIGS = {
    1:  {"archetype": "dashboard", "kpi_labels": ["Total Interventions", "Completed", "Pending", "Completion Rate"]},
    2:  {"archetype": "dashboard", "kpi_labels": ["Total Feedback Items", "Positive", "Needs Action", "Action Rate"]},
    3:  {"archetype": "table_list"},
    5:  {"archetype": "dashboard", "kpi_labels": ["Total Tasks", "Total Time (hrs)", "Avg Time/Task", "Active Users"]},
    6:  {"archetype": "table_list"},
    8:  {"archetype": "table_list"},
    9:  {"archetype": "dashboard", "kpi_labels": ["Total Assessments", "Avg Pain Score", "Improved", "Worsened"]},
    10: {"archetype": "summary", "kpi_labels": ["Total Evaluations", "PDMP Checked", "Not Checked"]},
    11: {"archetype": "table_list"},
    12: {"archetype": "table_list"},
    13: {"archetype": "table_list"},
    14: {"archetype": "summary", "kpi_labels": ["Total Prescriptions", "Audited", "Flagged", "Flag Rate"]},
    15: {"archetype": "table_list"},
    16: {"archetype": "table_list"},
    17: {"archetype": "table_list"},
    18: {"archetype": "summary", "kpi_labels": ["Total Charges", "Captured", "Pending", "Capture Rate"]},
    19: {"archetype": "table_list"},
    20: {"archetype": "table_list"},
    21: {"archetype": "table_list"},
    22: {"archetype": "table_list"},
    23: {"archetype": "dashboard", "kpi_labels": ["Total Captures", "Total Time (hrs)", "Avg Time (min)", "Categories"]},
    24: {"archetype": "dashboard", "kpi_labels": ["Records Sent", "Records Received", "Match Rate", "Pending Sync"]},
    25: {"archetype": "table_list"},
    26: {"archetype": "table_list"},
}

CATEGORY_COLUMNS = {
    "General": ["Patient Name", "MRN", "Date", "Status", "Provider"],
    "Worklist Queues": ["Queue Item", "Priority", "Assigned To", "Status", "Created Date"],
    "Medication & Orders": ["Medication", "Order Date", "Patient", "Dosage", "Status"],
    "Audit Reports": ["Audit Item", "Compliant", "Non-Compliant", "Review Date", "Auditor"],
    "Task & Time": ["Task", "Time Spent (min)", "User", "Date", "Category"],
    "Integrations": ["Source", "Records Sent", "Records Received", "Status", "Last Sync"],
}

CATEGORY_STATUSES = {
    "General": ["Completed", "Pending", "In Progress", "Cancelled"],
    "Worklist Queues": ["Open", "In Progress", "Completed", "Escalated"],
    "Medication & Orders": ["Active", "Discontinued", "On Hold", "Completed"],
    "Audit Reports": ["Compliant", "Non-Compliant", "Under Review"],
    "Task & Time": ["Started", "Completed", "Paused", "Overdue"],
    "Integrations": ["Synced", "Failed", "Pending", "In Progress"],
}

KPI_COLORS = ["#4a90d9", "#27ae60", "#e74c3c", "#8e44ad", "#f39c12", "#1abc9c"]

NAMES_POOL = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
MEDICATIONS = ["Cisplatin", "Carboplatin", "Paclitaxel", "Doxorubicin", "Cyclophosphamide", "Methotrexate", "Fluorouracil", "Gemcitabine", "Vinblastine", "Etoposide"]
PROVIDERS = ["Dr. Chen", "Dr. Patel", "Dr. Rodriguez", "Dr. Kim", "Dr. Johnson", "Dr. Williams", "Dr. Garcia", "Dr. Brown"]