import frappe
from frappe.model.document import Document
from hotel_pms.hotel import lifecycle


class HotelReservation(Document):
    def validate(self):
        lifecycle.validate_reservation(self)

    @frappe.whitelist()
    def do_check_in(self):
        return lifecycle.check_in(self.name)

    @frappe.whitelist()
    def cancel_reservation(self, reason=None):
        if self.status in ("Checked In",):
            frappe.throw(frappe._("Cannot cancel a reservation that is already checked in"))
        frappe.db.set_value("Hotel Reservation", self.name, "status", "Cancelled")
        return {"message": frappe._("Reservation cancelled")}

    @frappe.whitelist()
    def mark_no_show(self):
        if self.status not in ("Confirmed", "Draft"):
            frappe.throw(frappe._("Only Confirmed or Draft reservations can be marked as No Show"))
        frappe.db.set_value("Hotel Reservation", self.name, "status", "No Show")
        return {"message": frappe._("Marked as No Show")}
