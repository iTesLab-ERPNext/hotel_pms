import frappe
from frappe.utils import nowdate, add_days


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Reservation", "fieldname": "name", "fieldtype": "Link", "options": "Hotel Reservation", "width": 130},
        {"label": "Customer", "fieldname": "customer_name", "fieldtype": "Data", "width": 160},
        {"label": "Booking Date", "fieldname": "booking_date", "fieldtype": "Date", "width": 110},
        {"label": "Arrival", "fieldname": "arrival_date", "fieldtype": "Date", "width": 100},
        {"label": "Departure", "fieldname": "departure_date", "fieldtype": "Date", "width": 100},
        {"label": "Nights", "fieldname": "number_of_nights", "fieldtype": "Int", "width": 70},
        {"label": "Adults", "fieldname": "total_adults", "fieldtype": "Int", "width": 70},
        {"label": "Children", "fieldname": "total_children", "fieldtype": "Int", "width": 80},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 110},
        {"label": "Package", "fieldname": "package", "fieldtype": "Link", "options": "Hotel Package", "width": 120},
    ]


def get_data(filters):
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
        SELECT
            r.name,
            hc.full_name as customer_name,
            r.booking_date,
            r.arrival_date,
            r.departure_date,
            r.number_of_nights,
            r.total_adults,
            r.total_children,
            r.status,
            r.package
        FROM `tabHotel Reservation` r
        LEFT JOIN `tabHotel Customer` hc ON hc.name = r.customer
        WHERE 1=1 {conditions}
        ORDER BY r.arrival_date DESC
    """.format(conditions=conditions), args, as_dict=True)
