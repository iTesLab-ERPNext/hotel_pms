import frappe
from frappe.model.document import Document


class HotelRoom(Document):
    def validate(self):
        if not self.room_name:
            self.room_name = self.room_number
