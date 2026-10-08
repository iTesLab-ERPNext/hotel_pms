import frappe
from frappe.utils import nowdate


def execute(filters=None):
    filters = filters or {}
    date = filters.get("date") or nowdate()

    columns = [
        {"label": "Type", "fieldname": "type", "fieldtype": "Data", "width": 100},
        {"label": "Guest", "fieldname": "guest_name", "fieldtype": "Data", "width": 160},
        {"label": "Room", "fieldname": "room", "fieldtype": "Link", "options": "Hotel Room", "width": 90},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": "Nights", "fieldname": "nights", "fieldtype": "Int", "width": 70},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": "Source", "fieldname": "source", "fieldtype": "Data", "width": 120},
    ]

    arrivals = frappe.db.sql(
        """
        SELECT 'Arrival' AS type, r.guest_name, '' AS room, r.arrival_date AS date,
               r.number_of_nights AS nights, r.status,
               COALESCE(bs.source_name, r.booking_source) AS source
        FROM `tabHotel Reservation` r
        LEFT JOIN `tabHotel Booking Source` bs ON bs.name = r.booking_source
        WHERE r.arrival_date = %s AND r.status IN ('Confirmed', 'Pending')
        """,
        date,
        as_dict=True,
    )

    departures = frappe.db.sql(
        """
        SELECT 'Departure' AS type, hs.guest_name, hs.room, hs.expected_checkout AS date,
               DATEDIFF(hs.expected_checkout, hs.checkin_date) AS nights,
               hs.status, '' AS source
        FROM `tabHotel Stay` hs
        WHERE hs.expected_checkout = %s AND hs.status = 'Checked In'
        """,
        date,
        as_dict=True,
    )

    return columns, list(arrivals) + list(departures)
