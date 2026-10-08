"""Departures Report — guests expected to check out on a given date."""
import frappe
from frappe.utils import nowdate
from hotel_pms.hotel.report_utils import col, summary


def execute(filters=None):
    filters = filters or {}
    date = filters.get("date") or nowdate()
    columns = _columns()
    rows = _data(date, filters)
    report_summary = [
        summary(len(rows), "Total Departures", "Int"),
    ]
    return columns, rows, None, None, report_summary


def _columns():
    return [
        col("stay",          "Stay",        "Link",  options="Hotel Stay",        width=130),
        col("reservation",   "Reservation", "Link",  options="Hotel Reservation", width=130),
        col("customer_name", "Guest",       "Data",  width=160),
        col("room",          "Room",        "Link",  options="Hotel Room",        width=100),
        col("room_type",     "Room Type",   "Data",  width=110),
        col("checkin_date",  "Checked In",  "Datetime", width=140),
        col("status",        "Stay Status", "Data",  width=110),
        col("folio_balance", "Balance",     "Currency", width=110),
    ]


def _data(date, filters):
    conditions = "r.departure_date = %(date)s"
    args = {"date": date}

    if filters.get("status"):
        conditions += " AND s.status = %(status)s"
        args["status"] = filters["status"]
    else:
        conditions += " AND s.status IN ('Active', 'Checked Out')"

    return frappe.db.sql("""
        SELECT s.name as stay, s.reservation,
               hc.full_name as customer_name,
               s.room, hr.room_type,
               s.checkin_date, s.status,
               COALESCE(f.balance, 0) as folio_balance
        FROM `tabHotel Stay` s
        JOIN `tabHotel Reservation` r ON r.name = s.reservation
        LEFT JOIN `tabHotel Customer` hc ON hc.name = s.customer
        LEFT JOIN `tabHotel Room` hr ON hr.name = s.room
        LEFT JOIN `tabHotel Folio` f ON f.stay = s.name
        WHERE {conditions}
        ORDER BY s.name
    """.format(conditions=conditions), args, as_dict=True)
