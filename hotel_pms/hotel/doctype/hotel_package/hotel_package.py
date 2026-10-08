import frappe
from frappe.model.document import Document


class HotelPackage(Document):
    def validate(self):
        for item in (self.items or []):
            item.amount = (item.quantity or 1) * (item.rate or 0)
