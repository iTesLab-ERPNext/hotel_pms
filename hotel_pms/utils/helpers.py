import frappe
from frappe.utils import today, add_days


def get_dashboard_data():
    """Return dashboard KPIs."""
    t = today()

    data = {
        "today_arrivals": frappe.db.count("Hotel Reservation", {
            "arrival_date": t, "status": ["in", ["Confirmed", "Checked In"]]
        }),
        "today_departures": frappe.db.count("Hotel Stay", {
            "expected_checkout": t, "status": "Active"
        }),
        "available_rooms": frappe.db.count("Hotel Room", {"status": "Available", "active": 1}),
        "occupied_rooms": frappe.db.count("Hotel Room", {"status": "Occupied", "active": 1}),
        "reserved_rooms": frappe.db.count("Hotel Room", {"status": "Reserved", "active": 1}),
        "cleaning_rooms": frappe.db.count("Hotel Room", {"status": "Cleaning", "active": 1}),
        "active_stays": frappe.db.count("Hotel Stay", {"status": "Active"}),
        "total_reservations": frappe.db.count("Hotel Reservation", {"status": ["not in", ["Cancelled"]]}),
        "outstanding_payments": _get_outstanding_balance(),
    }
    return data


def _get_outstanding_balance():
    result = frappe.db.sql("""
        SELECT COALESCE(SUM(balance), 0)
        FROM `tabHotel Folio`
        WHERE status = 'Open'
    """)
    return result[0][0] if result else 0
