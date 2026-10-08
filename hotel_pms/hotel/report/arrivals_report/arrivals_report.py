"""Arrivals Report — guests arriving on or around a given date."""
import frappe
from frappe.utils import nowdate
from hotel_pms.hotel.report_utils import col, summary


def execute(filters=None):
    filters = filters or {}
    date = filters.get("date") or nowdate()
    columns = _columns()
    rows = _data(date, filters)
    report_summary = [
        summary(len(rows), "Total Arrivals", "Int"),
    ]
    return columns, rows, None, None, report_summary


def _columns():
    return [
        col("reservation",      "Reservation",    "Link",  options="Hotel Reservation", width=130),
        col("customer_name",    "Guest",          "Data",  width=160),
        col("arrival_date",     "Arrival",        "Date",  width=100),
        col("departure_date",   "Departure",      "Date",  width=100),
        col("number_of_nights", "Nights",         "Int",   width=70),
        col("rooms",            "Rooms",          "Data",  width=120),
        col("total_adults",     "Adults",         "Int",   width=70),
        col("total_children",   "Children",       "Int",   width=80),
        col("status",           "Status",         "Data",  width=110),
        col("package",          "Package",        "Link",  options="Hotel Package", width=120),
    ]


def _data(date, filters):
    conditions = "r.arrival_date = %(date)s"
    args = {"date": date}

    if filters.get("status"):
        conditions += " AND r.status = %(status)s"
        args["status"] = filters["status"]
    else:
        conditions += " AND r.status IN ('Confirmed', 'Checked In')"

    rows = frappe.db.sql("""
        SELECT r.name as reservation, hc.full_name as customer_name,
               r.arrival_date, r.departure_date, r.number_of_nights,
               r.total_adults, r.total_children, r.status, r.package
        FROM `tabHotel Reservation` r
        LEFT JOIN `tabHotel Customer` hc ON hc.name = r.customer
        WHERE {conditions}
        ORDER BY r.name
    """.format(conditions=conditions), args, as_dict=True)

    # Attach room numbers
    for row in rows:
        room_nos = frappe.db.sql("""
            SELECT GROUP_CONCAT(hr.room_number SEPARATOR ', ')
            FROM `tabHotel Reservation Room` rr
            JOIN `tabHotel Room` hr ON hr.name = rr.room
            WHERE rr.parent = %s
        """, row.reservation)[0][0]
        row["rooms"] = room_nos or ""

    return rows
