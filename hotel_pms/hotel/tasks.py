"""
hotel_pms.hotel.tasks
~~~~~~~~~~~~~~~~~~~~~~
Scheduled background tasks wired in hooks.py under scheduler_events.
"""
import frappe
from frappe.utils import nowdate, now_datetime


def daily_auto_checkout() -> None:
    """Mark overdue active stays as 'Late Checkout' so staff can follow up."""
    today = nowdate()
    overdue = frappe.get_all(
        "Hotel Stay",
        filters={"status": "Active", "expected_checkout": ["<", today]},
        fields=["name", "room", "customer"])

    for stay in overdue:
        frappe.db.set_value("Hotel Stay", stay.name, "status", "Late Checkout")
        frappe.logger().warning(
            f"Hotel PMS: stay {stay.name} for room {stay.room} is overdue")


def daily_flag_no_shows() -> None:
    """Flag confirmed reservations whose arrival date has passed as No Show."""
    today = nowdate()
    overdue = frappe.get_all(
        "Hotel Reservation",
        filters={"status": "Confirmed", "arrival_date": ["<", today]},
        fields=["name"])

    for res in overdue:
        frappe.db.set_value("Hotel Reservation", res.name, "status", "No Show")
        frappe.logger().info(f"Hotel PMS: reservation {res.name} marked No Show")

    if overdue:
        frappe.db.commit()
