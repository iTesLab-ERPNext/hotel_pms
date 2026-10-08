import frappe
from frappe import _

@frappe.whitelist()
def get_reservation(reservation):
    res = frappe.get_doc("Hotel Reservation", reservation)
    return res.as_dict()

@frappe.whitelist()
def confirm_reservation(reservation):
    res = frappe.get_doc("Hotel Reservation", reservation)
    if res.status != "Draft":
        frappe.throw(_("Only Draft reservations can be confirmed"))
    res.submit()
    return {"success": True, "status": res.status}
