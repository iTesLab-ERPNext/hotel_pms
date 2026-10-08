import frappe
from frappe.model.document import Document

class HotelRoom(Document):
    def validate(self):
        if self.room_type:
            rt = frappe.get_doc("Hotel Room Type", self.room_type)
            if not self.capacity:
                self.capacity = rt.capacity_adults

    def set_status(self, status):
        self.status = status
        self.save(ignore_permissions=True)
