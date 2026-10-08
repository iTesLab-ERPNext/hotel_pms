import frappe
from frappe.utils import nowdate


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Reservation", "fieldname": "name", "fieldtype": "Link", "options": "Hotel Reservation", "width": 130},
        {"label": "Customer", "fieldname": "customer_name", "fieldtype": "Data", "width": 160},
        {"label": "Phone", "fieldname": "phone", "fieldtype": "Data", "width": 120},
        {"label": "Arrival Date", "fieldname": "arrival_date", "fieldtype": "Date", "width": 110},
        {"label": "Departure Date", "fieldname": "departure_date", "fieldtype": "Date", "width": 110},
        {"label": "Nights", "fieldname": "number_of_nights", "fieldtype": "Int", "width": 70},
        {"label": "Adults", "fieldname": "total_adults", "fieldtype": "Int", "width": 70},
        {"label": "Children", "fieldname": "total_children", "fieldtype": "Int", "width": 80},
        {"label": "Rooms", "fieldname": "rooms_list", "fieldtype": "Data", "width": 140},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 110},
        {"label": "Package", "fieldname": "package", "fieldtype": "Link", "options": "Hotel Package", "width": 120},
        {"label": "Notes", "fieldname": "notes", "fieldtype": "Data", "width": 200},
    ]


def get_data(filters):
    date = filters.get("date") or nowdate()

    reservations = frappe.db.sql("""
        SELECT
            r.name,
            hc.full_name as customer_name,
            hc.phone,
            r.arrival_date,
            r.departure_date,
            r.number_of_nights,
            r.total_adults,
            r.total_children,
            r.status,
            r.package,
            r.notes
        FROM `tabHotel Reservation` r
        LEFT JOIN `tabHotel Customer` hc ON hc.name = r.customer
        WHERE r.arrival_date = %(date)s
          AND r.status IN ('Confirmed', 'Checked In', 'Draft')
        ORDER BY r.arrival_date, r.name
    """, {"date": date}, as_dict=True)

    # Get room lists
    for res in reservations:
        rooms = frappe.db.sql("""
            SELECT room FROM `tabHotel Reservation Room` WHERE parent = %s
        """, res.name, as_dict=True)
        res["rooms_list"] = ", ".join(r.room for r in rooms)

    return reservations
