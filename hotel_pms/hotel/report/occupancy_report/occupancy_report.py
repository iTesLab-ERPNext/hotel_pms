"""Occupancy Report — daily occupancy rates for a date range."""
import frappe
from datetime import timedelta
from hotel_pms.hotel.report_utils import col, summary, indicator_for_occupancy, normalize_dates


def execute(filters=None):
    filters = filters or {}
    from_date, to_date = normalize_dates(filters, default_days=30)

    columns = _columns()
    rows, report_summary = _data(from_date, to_date)
    return columns, rows, None, None, report_summary


def _columns():
    return [
        col("date",          "Date",         "Date",    width=110),
        col("total_rooms",   "Total Rooms",  "Int",     width=110),
        col("occupied",      "Occupied",     "Int",     width=100),
        col("reserved",      "Reserved",     "Int",     width=100),
        col("available",     "Available",    "Int",     width=100),
        col("maintenance",   "Maintenance",  "Int",     width=110),
        col("occupancy_pct", "Occupancy %",  "Percent", width=120),
    ]


def _data(from_date, to_date):
    total_rooms = frappe.db.count("Hotel Room", {"active": 1})
    if not total_rooms:
        return [], []

    rows = []
    current = from_date
    total_occ = 0
    days = 0

    while current <= to_date:
        date_str = str(current)

        occupied = frappe.db.sql("""
            SELECT COUNT(DISTINCT room) FROM `tabHotel Stay`
            WHERE status = 'Active'
              AND DATE(checkin_date) <= %s
              AND (expected_checkout > %s OR expected_checkout IS NULL)
        """, (date_str, date_str))[0][0] or 0

        reserved = frappe.db.sql("""
            SELECT COUNT(DISTINCT rr.room)
            FROM `tabHotel Reservation Room` rr
            JOIN `tabHotel Reservation` r ON r.name = rr.parent
            WHERE r.status = 'Confirmed'
              AND r.arrival_date <= %s AND r.departure_date > %s
        """, (date_str, date_str))[0][0] or 0

        maintenance = frappe.db.count(
            "Hotel Room", {"status": ["in", ["Maintenance", "Blocked", "Out of Service"]]})

        available    = max(0, total_rooms - occupied - reserved - maintenance)
        occupancy_pct = round((occupied / total_rooms) * 100, 1) if total_rooms else 0

        rows.append({
            "date":          current,
            "total_rooms":   total_rooms,
            "occupied":      occupied,
            "reserved":      reserved,
            "available":     available,
            "maintenance":   maintenance,
            "occupancy_pct": occupancy_pct,
        })

        total_occ += occupancy_pct
        days += 1
        current += timedelta(days=1)

    avg_occ = round(total_occ / days, 1) if days else 0
    report_summary = [
        summary(avg_occ,     "Avg Occupancy %", "Percent",
                indicator_for_occupancy(avg_occ)),
        summary(total_rooms, "Total Rooms",     "Int"),
    ]
    return rows, report_summary
