"""Revenue Report — daily revenue breakdown for a date range."""
import frappe
from datetime import timedelta
from hotel_pms.hotel.report_utils import col, summary, normalize_dates


def execute(filters=None):
    filters = filters or {}
    from_date, to_date = normalize_dates(filters, default_days=30)
    columns = _columns()
    rows, report_summary = _data(from_date, to_date)
    return columns, rows, None, None, report_summary


def _columns():
    return [
        col("date",          "Date",            "Date",     width=110),
        col("room_revenue",  "Room Revenue",    "Currency", width=130),
        col("service_rev",   "Service Revenue", "Currency", width=140),
        col("total_revenue", "Total Revenue",   "Currency", width=130),
        col("payments",      "Payments",        "Currency", width=120),
        col("outstanding",   "Outstanding",     "Currency", width=120),
    ]


def _data(from_date, to_date):
    rows = []
    current = from_date
    grand_total = 0

    while current <= to_date:
        date_str = str(current)

        room_rev = frappe.db.sql("""
            SELECT COALESCE(SUM(fi.amount), 0)
            FROM `tabHotel Folio Item` fi
            JOIN `tabHotel Folio` f ON f.name = fi.parent
            WHERE fi.charge_type = 'Room' AND fi.date = %s
        """, date_str)[0][0] or 0

        service_rev = frappe.db.sql("""
            SELECT COALESCE(SUM(fi.amount), 0)
            FROM `tabHotel Folio Item` fi
            JOIN `tabHotel Folio` f ON f.name = fi.parent
            WHERE fi.charge_type != 'Room' AND fi.date = %s
        """, date_str)[0][0] or 0

        payments = frappe.db.sql("""
            SELECT COALESCE(SUM(amount), 0)
            FROM `tabHotel Payment`
            WHERE payment_date = %s AND docstatus != 2
        """, date_str)[0][0] or 0

        total_rev  = float(room_rev) + float(service_rev)
        outstanding = total_rev - float(payments)
        grand_total += total_rev

        rows.append({
            "date":          current,
            "room_revenue":  float(room_rev),
            "service_rev":   float(service_rev),
            "total_revenue": total_rev,
            "payments":      float(payments),
            "outstanding":   outstanding,
        })
        current += timedelta(days=1)

    report_summary = [
        summary(grand_total, "Total Revenue", "Currency",
                "Green" if grand_total > 0 else "Grey"),
    ]
    return rows, report_summary
