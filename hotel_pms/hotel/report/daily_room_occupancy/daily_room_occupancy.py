"""
Daily Room Occupancy
--------------------
Shows occupied / available / reserved rooms for each day in a date range,
with an average-occupancy summary bar.
"""
import frappe
from datetime import timedelta
from hotel_pms.hotel.report_utils import col, summary, indicator_for_occupancy, normalize_dates


def execute(filters=None):
    filters = filters or {}
    from_date, to_date = normalize_dates(filters, default_days=30)
    room_type = filters.get("room_type")

    columns = _columns()
    rows, report_summary = _data(from_date, to_date, room_type)
    return columns, rows, None, None, report_summary


def _columns():
    return [
        col("date",          "Date",          "Date",    width=120),
        col("day_of_week",   "Day",           "Data",    width=90),
        col("total_rooms",   "Total Rooms",   "Int",     width=110),
        col("occupied",      "Occupied",      "Int",     width=100),
        col("reserved",      "Reserved",      "Int",     width=100),
        col("available",     "Available",     "Int",     width=100),
        col("maintenance",   "Out of Service","Int",     width=120),
        col("occupancy_pct", "Occupancy %",   "Percent", width=120),
        col("arrivals",      "Arrivals",      "Int",     width=90),
        col("departures",    "Departures",    "Int",     width=100),
        col("revenue",       "Room Revenue",  "Currency",width=130),
    ]


def _data(from_date, to_date, room_type=None):
    room_filter = {"active": 1}
    if room_type:
        room_filter["room_type"] = room_type
    total_rooms = frappe.db.count("Hotel Room", room_filter)
    if not total_rooms:
        return [], []

    rows = []
    current = from_date
    total_occ = 0
    days = 0
    grand_rev = 0.0

    DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    while current <= to_date:
        date_str = str(current)

        # Occupied rooms (active stays)
        occupied = frappe.db.sql("""
            SELECT COUNT(DISTINCT hs.room)
            FROM `tabHotel Stay` hs
            WHERE hs.status = 'Active'
              AND DATE(hs.checkin_date) <= %s
              AND (hs.expected_checkout > %s OR hs.expected_checkout IS NULL)
        """, (date_str, date_str))[0][0] or 0

        # Confirmed reservations (not yet checked in)
        reserved = frappe.db.sql("""
            SELECT COUNT(DISTINCT rr.room)
            FROM `tabHotel Reservation Room` rr
            JOIN `tabHotel Reservation` r ON r.name = rr.parent
            WHERE r.status = 'Confirmed'
              AND r.arrival_date <= %s AND r.departure_date > %s
        """, (date_str, date_str))[0][0] or 0

        # Out of service
        maintenance = frappe.db.count(
            "Hotel Room",
            {"status": ["in", ["Maintenance", "Blocked", "Out of Service"]]})

        # Arrivals
        arrivals = frappe.db.count(
            "Hotel Reservation",
            {"arrival_date": date_str, "status": ["in", ["Confirmed", "Checked In"]]})

        # Departures
        departures = frappe.db.count(
            "Hotel Reservation",
            {"departure_date": date_str, "status": ["in", ["Checked In", "Completed"]]})

        # Room revenue
        rev = frappe.db.sql("""
            SELECT COALESCE(SUM(fi.amount), 0)
            FROM `tabHotel Folio Item` fi
            WHERE fi.charge_type = 'Room' AND fi.date = %s
        """, date_str)[0][0] or 0

        available     = max(0, total_rooms - occupied - reserved - maintenance)
        occupancy_pct = round((occupied / total_rooms) * 100, 1) if total_rooms else 0
        total_occ    += occupancy_pct
        grand_rev    += float(rev)
        days         += 1

        rows.append({
            "date":          current,
            "day_of_week":   DAYS[current.weekday()],
            "total_rooms":   total_rooms,
            "occupied":      occupied,
            "reserved":      reserved,
            "available":     available,
            "maintenance":   maintenance,
            "occupancy_pct": occupancy_pct,
            "arrivals":      arrivals,
            "departures":    departures,
            "revenue":       float(rev),
        })
        current += timedelta(days=1)

    avg_occ = round(total_occ / days, 1) if days else 0
    report_summary = [
        summary(avg_occ,      "Avg Occupancy %", "Percent",
                indicator_for_occupancy(avg_occ)),
        summary(total_rooms,  "Total Rooms",     "Int",     "Blue"),
        summary(grand_rev,    "Room Revenue",    "Currency","Green" if grand_rev else "Grey"),
    ]
    return rows, report_summary
