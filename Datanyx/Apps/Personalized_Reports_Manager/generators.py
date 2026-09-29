"""Report data generation functions for generic report archetypes."""
from config import (
    REPORT_CONFIGS, CATEGORY_COLUMNS, CATEGORY_STATUSES, KPI_COLORS,
    NAMES_POOL, FIRST_NAMES, MEDICATIONS, PROVIDERS
)


def _gen_name(rng):
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(NAMES_POOL)}"


def _gen_dates(rng, date_range='all'):
    """Generate date labels based on filter."""
    if date_range == 'prior_cal_week':
        return [f"7/{d}" for d in range(8, 15)]
    elif date_range == 'prior_work_week':
        return [f"7/{d}" for d in range(8, 13)]
    elif date_range == 'prev_cal_year':
        return [f"2024-{m:02d}" for m in range(1, 13)]
    elif date_range == 'prior_cal_month':
        return [f"6/{d}" for d in range(1, 31)]
    return [f"7/{d}" for d in range(4, 15)]


def generate_generic_report(report, report_id, filters=None):
    """Generate deterministic synthetic report data based on archetype and category."""
    import random as _rng
    rng = _rng.Random(report_id * 37)

    config = REPORT_CONFIGS.get(report_id, {"archetype": "table_list"})
    archetype = config["archetype"]
    category = report.get("category", "General")
    columns = CATEGORY_COLUMNS.get(category, ["Item", "Value", "Date", "Status", "Notes"])
    statuses = CATEGORY_STATUSES.get(category, ["Active", "Pending", "Completed"])

    date_range = (filters or {}).get('mapping_date', 'all')
    active_statuses = (filters or {}).get('status', [])

    dates = _gen_dates(rng, date_range)

    # If status filter is active, limit statuses
    status_map = {'received': 'Completed', 'saved': 'Pending'}
    if active_statuses:
        filtered = [status_map.get(s, s.capitalize()) for s in active_statuses if status_map.get(s, s.capitalize()) in statuses]
        if filtered:
            statuses = filtered

    result = {
        'report': report,
        'in_progress': False,
        'report_type': f'generic_{archetype}',
        'archetype': archetype,
        'category': category,
    }

    def _gen_row():
        row = []
        for col in columns:
            if col == "Status":
                row.append(rng.choice(statuses))
            elif "Date" in col or col == "Last Sync":
                row.append(f"7/{rng.randint(1, 15)}/2025")
            elif "MRN" in col:
                row.append(f"MRN{rng.randint(10000, 99999)}")
            elif "Time" in col or "Count" in col or "Records" in col:
                row.append(str(rng.randint(1, 100)))
            elif "Patient" in col or "Name" in col:
                row.append(_gen_name(rng))
            elif "Provider" in col or "Auditor" in col or "User" in col or "Assigned" in col:
                row.append(rng.choice(PROVIDERS))
            elif "Medication" in col:
                row.append(rng.choice(MEDICATIONS))
            elif "Priority" in col:
                row.append(rng.choice(["High", "Medium", "Low"]))
            elif "Compliant" in col and "Non" not in col:
                row.append(str(rng.randint(80, 200)))
            elif "Non-Compliant" in col:
                row.append(str(rng.randint(1, 30)))
            elif "Dosage" in col:
                row.append(f"{rng.randint(1, 500)}mg")
            else:
                row.append(f"Item {rng.randint(1, 999)}")
        return row

    if archetype == "dashboard":
        kpi_labels = config.get("kpi_labels", ["Total", "Completed", "Pending", "Rate"])
        kpi_vals = [rng.randint(50, 2000) for _ in kpi_labels]
        if len(kpi_vals) >= 4 and "Rate" in kpi_labels[-1]:
            kpi_vals[-1] = round(kpi_vals[1] / max(kpi_vals[0], 1) * 100)
        result['kpi_cards'] = [
            {"label": kpi_labels[i], "value": kpi_vals[i], "color": KPI_COLORS[i % len(KPI_COLORS)]}
            for i in range(len(kpi_labels))
        ]
        trend_a = [rng.randint(10, 100) for _ in dates]
        trend_b = [rng.randint(5, 80) for _ in dates]
        result['charts'] = [
            {"title": "Volume Trend", "type": "line", "x": dates, "series": [
                {"name": "Total", "y": trend_a, "color": "#4a90d9"},
                {"name": "Processed", "y": trend_b, "color": "#27ae60"}]},
            {"title": "Status Distribution", "type": "bar", "x": statuses, "series": [
                {"name": "Count", "y": [rng.randint(10, 80) for _ in statuses], "color": "#4a90d9"}]},
            {"title": "Category Breakdown", "type": "pie", "labels": statuses,
             "values": [rng.randint(10, 80) for _ in statuses]},
        ]
        table_rows = [_gen_row() for _ in range(rng.randint(8, 15))]
        result['table_data'] = {"columns": columns, "rows": table_rows}

    elif archetype == "table_list":
        total = rng.randint(100, 2000)
        result['kpi_cards'] = [
            {"label": "Total Records", "value": total, "color": "#4a90d9"},
            {"label": "Active", "value": rng.randint(50, max(total, 51)), "color": "#27ae60"},
            {"label": "Pending", "value": rng.randint(10, 200), "color": "#e74c3c"},
        ]
        result['charts'] = [
            {"title": "Records by Status", "type": "bar", "x": statuses, "series": [
                {"name": "Count", "y": [rng.randint(10, 100) for _ in statuses], "color": "#4a90d9"}]},
            {"title": "Status Overview", "type": "pie", "labels": statuses,
             "values": [rng.randint(10, 80) for _ in statuses]},
        ]
        table_rows = [_gen_row() for _ in range(min(total, 20))]
        result['table_data'] = {"columns": columns, "rows": table_rows}

    elif archetype == "summary":
        kpi_labels = config.get("kpi_labels", ["Total", "Completed", "Pending"])
        kpi_vals = [rng.randint(50, 2000) for _ in kpi_labels]
        if len(kpi_vals) >= 4 and "Rate" in kpi_labels[-1]:
            kpi_vals[-1] = round(kpi_vals[1] / max(kpi_vals[0], 1) * 100)
        result['kpi_cards'] = [
            {"label": kpi_labels[i], "value": kpi_vals[i], "color": KPI_COLORS[i % len(KPI_COLORS)]}
            for i in range(len(kpi_labels))
        ]
        result['charts'] = [
            {"title": "Overview", "type": "pie", "labels": statuses,
             "values": [rng.randint(10, 80) for _ in statuses]},
            {"title": "Monthly Trend", "type": "bar", "x": dates, "series": [
                {"name": "Count", "y": [rng.randint(10, 100) for _ in dates], "color": "#4a90d9"}]},
        ]
        table_rows = [_gen_row() for _ in range(rng.randint(5, 10))]
        result['table_data'] = {"columns": columns, "rows": table_rows}

    return result