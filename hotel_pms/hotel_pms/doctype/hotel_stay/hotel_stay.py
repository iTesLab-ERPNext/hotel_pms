import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class HotelStay(Document):
    def on_submit(self):
        pass

    def checkout(self):
        """Perform checkout - called from checkout API."""
        self.status = "Checked Out"
        self.actual_checkout = nowdate()
        self.save()
        frappe.db.set_value("Hotel Room", self.room, "status", "Dirty")
