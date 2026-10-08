import frappe
from frappe.model.document import Document


class HotelStay(Document):
    def validate(self):
        if self.checkin_date and self.expected_checkout:
            pass  # basic validation done in API

    def on_submit(self):
        pass

    def on_cancel(self):
        if self.room and self.status == "Active":
            frappe.db.set_value("Hotel Room", self.room, "status", "Available")
