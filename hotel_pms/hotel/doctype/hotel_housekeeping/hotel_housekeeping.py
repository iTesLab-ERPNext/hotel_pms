import frappe
from frappe.model.document import Document


class HotelHousekeeping(Document):
    def on_submit(self):
        frappe.db.set_value("Hotel Room", self.room, "housekeeping_status", self.new_status)
        if self.new_status in ("Clean", "Inspected"):
            current_status = frappe.db.get_value("Hotel Room", self.room, "status")
            if current_status == "Cleaning":
                frappe.db.set_value("Hotel Room", self.room, "status", "Available")
