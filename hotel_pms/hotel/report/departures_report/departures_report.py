import frappe
from frappe.utils import nowdate


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Reservation", "fieldname": "reservation", "fieldtype": "Link", "options": "Hotel Reservation", "width": 130},
        {"label": "Stay", "fieldname": "stay", "fieldtype": "Link", "options": "Hotel Stay", "width": 110},
        {"label": "Customer", "fieldname": "customer_name", "fieldtype": "Data", "width": 160},
        {"label": "Phone", "fieldname": "phone", "fieldtype": "Data", "width": 120},
        {"label": "Room", "fieldname": "room", "fieldtype": "Link", "options": "Hotel Room", "width": 100},
        {"label": "Check-in Date", "fieldname": "checkin_date", "fieldtype": "Datetime", "width": 140},
        {"label": "Expected Checkout", "fieldname": "expected_checkout", "fieldtype": "Date", "width": 130},
        {"label": "Folio", "fieldname": "folio", "fieldtype": "Link", "options": "Hotel Folio", "width": 110},
        {"label": "Total Charges", "fieldname": "total_charges", "fieldtype": "Currency", "width": 120},
        {"label": "Total Payments", "fieldname": "total_payments", "fieldtype": "Currency", "width": 120},
        {"label": "Balance", "fieldname": "balance", "fieldtype": "Currency", "width": 100},
        {"label": "Folio Status", "fieldname": "folio_status", "fieldtype": "Data", "width": 110},
    ]


def get_data(filters):
    date = filters.get("date") or nowdate()

    stays = frappe.db.sql("""
        SELECT
            s.name as stay,
            s.reservation,
            s.room,
            s.checkin_date,
            s.expected_checkout,
            hc.full_name as customer_name,
            hc.phone
        FROM `tabHotel Stay` s
        LEFT JOIN `tabHotel Customer` hc ON hc.name = s.customer
        WHERE s.status = 'Active'
          AND s.expected_checkout = %(date)s
        ORDER BY s.room
    """, {"date": date}, as_dict=True)

    for stay in stays:
        folio = frappe.db.get_value("Hotel Folio",
            {"stay": stay.stay},
            ["name", "total_charges", "total_payments", "balance", "status"],
            as_dict=True)
        if folio:
            stay["folio"] = folio.name
            stay["total_charges"] = folio.total_charges
            stay["total_payments"] = folio.total_payments
            stay["balance"] = folio.balance
            stay["folio_status"] = folio.status
        else:
            stay["folio"] = None
            stay["total_charges"] = 0
            stay["total_payments"] = 0
            stay["balance"] = 0
            stay["folio_status"] = "No Folio"

    return stays
