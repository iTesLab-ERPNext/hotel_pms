"""
hotel_pms.hotel.report_utils
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Shared helpers for all Hotel PMS Script Reports.
Mirrors kpi/report_utils.py from the LMD reference app.
"""
from frappe.utils import getdate, nowdate, add_days


# ── Column builder ─────────────────────────────────────────────────────────────

def col(fieldname: str, label: str, fieldtype: str = "Data",
        options: str = None, width: int = 120, **kw) -> dict:
    """Build a column descriptor for a Frappe Script Report."""
    d = {
        "fieldname": fieldname,
        "label": label,
        "fieldtype": fieldtype,
        "width": width,
    }
    if options:
        d["options"] = options
    d.update(kw)
    return d


# ── Summary item builder ───────────────────────────────────────────────────────

def summary(value, label: str, datatype: str = "Float",
            indicator: str = None) -> dict:
    """Build a report_summary item for the report summary bar."""
    d = {"value": value, "label": label, "datatype": datatype}
    if indicator:
        d["indicator"] = indicator
    return d


# ── Indicator helpers ──────────────────────────────────────────────────────────

def indicator_for_occupancy(pct, good: float = 70, warn: float = 40) -> str:
    """Return a colour indicator string based on occupancy percentage."""
    if pct >= good:
        return "Green"
    if pct >= warn:
        return "Orange"
    return "Red"


# ── Date range normalisation ───────────────────────────────────────────────────

def normalize_dates(filters: dict, default_days: int = 30) -> tuple:
    """Return (from_date, to_date) as date objects from a filters dict."""
    from_date = getdate(filters.get("from_date") or add_days(nowdate(), -default_days))
    to_date   = getdate(filters.get("to_date")   or nowdate())
    return from_date, to_date
