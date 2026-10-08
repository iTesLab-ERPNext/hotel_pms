import frappe
from frappe.model.document import Document

class HotelRoom(Document):
    def before_save(self):
        if not self.rate and self.room_type:
            self.rate = frappe.get_value("Hotel Room Type", self.room_type, "base_rate") or 0
