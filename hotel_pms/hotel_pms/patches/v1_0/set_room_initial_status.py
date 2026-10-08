import frappe


def execute():
    frappe.db.sql(
        "UPDATE `tabHotel Room` SET status='Available' WHERE status IS NULL OR status=''"
    )
    frappe.db.commit()
