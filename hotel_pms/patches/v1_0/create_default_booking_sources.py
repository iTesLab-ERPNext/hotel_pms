"""Create default booking sources if none exist."""
import frappe


def execute():
    defaults = ["Walk-in", "Phone", "Email", "Website", "Travel Agent", "GDS"]
    for src in defaults:
        if not frappe.db.exists("Hotel Booking Source", src):
            doc = frappe.new_doc("Hotel Booking Source")
            doc.source_name = src
            doc.active = 1
            doc.insert(ignore_permissions=True)
    frappe.db.commit()
