import frappe
from frappe.model.document import Document


class HotelPackageItem(Document):
    def validate(self):
        self.amount = (self.quantity or 1) * (self.rate or 0)
