"""Set initial status for any Hotel Room missing a status."""
import frappe


def execute():
    frappe.db.sql(
        "UPDATE `tabHotel Room` SET status='Available', housekeeping_status='Clean' WHERE status IS NULL OR status=''"
    )
    frappe.db.commit()
