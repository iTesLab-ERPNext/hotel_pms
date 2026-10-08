import frappe
from frappe.utils import today


def execute(filters=None):
    filters = filters or {}
    date = filters.get("date") or today()

    columns = [
        {"label": "Type",         "fieldname": "movement_type","fieldtype": "Data",    "width": 90},
        {"label": "Reservation",  "fieldname": "reservation",  "fieldtype": "Link",    "options": "Hotel Reservation","width": 130},
        {"label": "Guest",        "fieldname": "customer_name","fieldtype": "Data",    "width": 160},
        {"label": "Room",         "fieldname": "room",         "fieldtype": "Link",    "options": "Hotel Room","width": 80},
        {"label": "Arrival",      "fieldname": "arrival_date", "fieldtype": "Date",    "width": 100},
        {"label": "Departure",    "fieldname": "departure_date","fieldtype": "Date",   "width": 100},
        {"label": "Nights",       "fieldname": "nights",       "fieldtype": "Int",     "width": 70},
        {"label": "Guests",       "fieldname": "guests",       "fieldtype": "Int",     "width": 70},
        {"label": "Status",       "fieldname": "status",       "fieldtype": "Data",    "width": 120},
    ]

    arrivals = frappe.db.sql(
        """
        SELECT 'Arrival' AS movement_type,
               res.name AS reservation, res.customer_name,
               rr.room,
               DATE(res.arrival_date) AS arrival_date,
               DATE(res.departure_date) AS departure_date,
               res.number_of_nights AS nights,
               res.total_guests AS guests,
               res.reservation_status AS status
        FROM `tabHotel Reservation` res
        LEFT JOIN `tabHotel Reservation Room` rr ON rr.parent = res.name
        WHERE DATE(res.arrival_date) = %s
          AND res.reservation_status IN ('Confirmed','Deposit Paid','Checked In')
        """,
        date,
        as_dict=True,
    )

    departures = frappe.db.sql(
        """
        SELECT 'Departure' AS movement_type,
               stay.reservation AS reservation, stay.guest_name AS customer_name,
               stay.room,
               DATE(stay.checkin_date) AS arrival_date,
               DATE(stay.expected_checkout) AS departure_date,
               stay.number_of_nights AS nights,
               stay.number_of_guests AS guests,
               stay.stay_status AS status
        FROM `tabHotel Stay` stay
        WHERE DATE(stay.expected_checkout) = %s
          AND stay.stay_status IN ('In House','Extended')
        """,
        date,
        as_dict=True,
    )

    data = list(arrivals) + list(departures)
    data.sort(key=lambda x: (x["movement_type"], str(x.get("arrival_date") or "")))
    return columns, data
