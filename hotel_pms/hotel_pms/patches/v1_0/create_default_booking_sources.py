import frappe


def execute():
    sources = ["Direct", "Walk-In", "Booking.com", "Expedia", "Corporate"]
    for s in sources:
        if not frappe.db.exists("Hotel Booking Source", {"source_name": s}):
            frappe.get_doc({"doctype": "Hotel Booking Source", "source_name": s, "commission_pct": 0}).insert()
    frappe.db.commit()
