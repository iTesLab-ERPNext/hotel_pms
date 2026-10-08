import frappe
from frappe.model.document import Document


class HotelReservationRoom(Document):
    def validate(self):
        self.total_guests = (self.adults or 0) + (self.children or 0) + (self.infants or 0)
        self.amount = (self.rate or 0) * (self.nights or 0)
        if self.room and not self.room_type:
            self.room_type = frappe.db.get_value("Hotel Room", self.room, "room_type")
