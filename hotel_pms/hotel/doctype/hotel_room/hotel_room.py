import frappe
from frappe.model.document import Document
from hotel_pms.hotel import lifecycle


class HotelRoom(Document):
    def validate(self):
        if not self.room_number:
            frappe.throw(frappe._("Room number is required"))

    @frappe.whitelist()
    def update_housekeeping(self, new_status, notes=None):
        return lifecycle.update_housekeeping_status(self.name, new_status, notes)

    @frappe.whitelist()
    def set_maintenance(self, notes=None):
        frappe.db.set_value("Hotel Room", self.name, "status", "Maintenance")
        return {"message": frappe._("Room set to Maintenance")}

    @frappe.whitelist()
    def set_available(self):
        frappe.db.set_value("Hotel Room", self.name, "status", "Available")
        return {"message": frappe._("Room set to Available")}
