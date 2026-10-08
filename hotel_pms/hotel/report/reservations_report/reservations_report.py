"""Reservations Report — filterable list of all reservations."""
import frappe
from hotel_pms.hotel.report_utils import col, summary


def execute(filters=None):
    filters = filters or {}
    columns = _columns()
    rows = _data(filters)
    report_summary = [
        summary(len(rows), "Total Reservations", "Int"),
    ]
    return columns, rows, None, None, report_summary


def _columns():
    return [
        col("name",             "Reservation",  "Link",    options="Hotel Reservation", width=130),
        col("customer_name",    "Customer",     "Data",    width=160),
        col("booking_date",     "Booking Date", "Date",    width=110),
        col("arrival_date",     "Arrival",      "Date",    width=100),
        col("departure_date",   "Departure",    "Date",    width=100),
        col("number_of_nights", "Nights",       "Int",     width=70),
        col("total_adults",     "Adults",       "Int",     width=70),
        col("total_children",   "Children",     "Int",     width=80),
        col("status",           "Status",       "Data",    width=110),
        col("package",          "Package",      "Link",    options="Hotel Package", width=120),
    ]


def _data(filters):
    conditions = ""
    args = {}

    if filters.get("status"):
        conditions += " AND r.status = %(status)s"
        args["status"] = filters["status"]
    if filters.get("from_date"):
        conditions += " AND r.arrival_date >= %(from_date)s"
        args["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions += " AND r.arrival_date <= %(to_date)s"
        args["to_date"] = filters["to_date"]
    if filters.get("customer"):
        conditions += " AND r.customer = %(customer)s"
        args["customer"] = filters["customer"]

    return frappe.db.sql("""
        SELECT r.name, hc.full_name as customer_name,
               r.booking_date, r.arrival_date, r.departure_date,
               r.number_of_nights, r.total_adults, r.total_children,
               r.status, r.package
        FROM `tabHotel Reservation` r
        LEFT JOIN `tabHotel Customer` hc ON hc.name = r.customer
        WHERE 1=1 {conditions}
        ORDER BY r.arrival_date DESC
    """.format(conditions=conditions), args, as_dict=True)
