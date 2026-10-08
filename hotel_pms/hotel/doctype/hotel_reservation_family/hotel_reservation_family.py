import frappe
from frappe.model.document import Document


class HotelReservationFamily(Document):
    def validate(self):
        self.total_guests = (self.adults or 0) + (self.children or 0) + (self.infants or 0)
