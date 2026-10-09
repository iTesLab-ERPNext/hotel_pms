"""
Arrivals and Departures
-----------------------
Combined front-desk view of today's (or any date's) guest movements.
Rows are colour-coded by type: Arrival (blue) / Departure (orange).
"""
import frappe
from frappe.utils import nowdate
from hotel_pms.hotel.report_utils import col, summary


def execute(filters=None):
    filters = filters or {}
    date    = filters.get("date")   or nowdate()
    only    = filters.get("type")   or ""  # "Arrivals" | "Departures" | ""
    status  = filters.get("status") or ""

    columns = _columns()
    rows    = []

    if only in ("", "Arrivals"):
        rows += _arrivals(date, status)
    if only in ("", "Departures"):
        rows += _departures(date, status)

    # Sort: type desc (Arrivals first), then name
    rows.sort(key=lambda r: (0 if r["type"] == "Arrival" else 1, r["guest_name"] or ""))

    arrivals_cnt   = sum(1 for r in rows if r["type"] == "Arrival")
    departures_cnt = sum(1 for r in rows if r["type"] == "Departure")

    report_summary = [
        summary(arrivals_cnt,   "Arrivals",   "Int", "Blue"),
        summary(departures_cnt, "Departures", "Int", "Orange"),
        summary(arrivals_cnt + departures_cnt, "Total Movements", "Int"),
    ]
    return columns, rows, None, None, report_summary


def _columns():
    return [
        col("type",              "Type",        "Data",  width=100),
        col("reservation",       "Reservation", "Link",  options="Hotel Reservation", width=130),
        col("guest_name",        "Guest",       "Data",  width=170),
        col("rooms",             "Room(s)",     "Data",  width=120),
        col("room_type",         "Room Type",   "Data",  width=120),
        col("arrival_date",      "Arrival",     "Date",  width=100),
        col("departure_date",    "Departure",   "Date",  width=100),
        col("number_of_nights",  "Nights",      "Int",   width=65),
        col("total_adults",      "Adults",      "Int",   width=65),
        col("total_children",    "Children",    "Int",   width=75),
        col("status",            "Res. Status", "Data",  width=110),
        col("folio_balance",     "Balance",     "Currency", width=110),
    ]


def _arrivals(date, status):
    st_filter = "AND r.status = %(status)s" if status else \
                "AND r.status IN ('Confirmed', 'Checked In')"
    rows = frappe.db.sql("""
        SELECT r.name AS reservation, hc.full_name AS guest_name,
               r.arrival_date, r.departure_date, r.number_of_nights,
               r.total_adults, r.total_children, r.status
        FROM `tabHotel Reservation` r
        LEFT JOIN `tabHotel Customer` hc ON hc.name = r.customer
        WHERE r.arrival_date = %(date)s {st}
        ORDER BY r.name
    """.format(st=st_filter), {"date": date, "status": status}, as_dict=True)

    for row in rows:
        row["type"] = "Arrival"
        _enrich_reservation(row)
    return rows


def _departures(date, status):
    st_filter = "AND r.status = %(status)s" if status else \
                "AND r.status IN ('Checked In', 'Completed')"
    rows = frappe.db.sql("""
        SELECT r.name AS reservation, hc.full_name AS guest_name,
               r.arrival_date, r.departure_date, r.number_of_nights,
               r.total_adults, r.total_children, r.status
        FROM `tabHotel Reservation` r
        LEFT JOIN `tabHotel Customer` hc ON hc.name = r.customer
        WHERE r.departure_date = %(date)s {st}
        ORDER BY r.name
    """.format(st=st_filter), {"date": date, "status": status}, as_dict=True)

    for row in rows:
        row["type"] = "Departure"
        _enrich_reservation(row)
    return rows


def _enrich_reservation(row):
    res = row["reservation"]

    # Room numbers + room type
    room_info = frappe.db.sql("""
        SELECT GROUP_CONCAT(hr.room_number SEPARATOR ', ') AS rooms,
               GROUP_CONCAT(DISTINCT hrt.room_type SEPARATOR ', ') AS room_type
        FROM `tabHotel Reservation Room` rr
        JOIN `tabHotel Room` hr ON hr.name = rr.room
        LEFT JOIN `tabHotel Room Type` hrt ON hrt.name = hr.room_type
        WHERE rr.parent = %s
    """, res, as_dict=True)
    row["rooms"]     = (room_info[0].rooms     if room_info else "") or ""
    row["room_type"] = (room_info[0].room_type if room_info else "") or ""

    # Folio balance
    balance = frappe.db.sql("""
        SELECT COALESCE(SUM(f.balance), 0)
        FROM `tabHotel Folio` f
        WHERE f.reservation = %s
    """, res)[0][0] or 0
    row["folio_balance"] = float(balance)
