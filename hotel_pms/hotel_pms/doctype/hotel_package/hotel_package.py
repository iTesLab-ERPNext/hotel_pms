import frappe
from frappe.model.document import Document

class HotelPackage(Document):
    def before_save(self):
        self.calculate_total()

    def calculate_total(self):
        total = 0
        for item in self.items:
            item.amount = (item.quantity or 1) * (item.rate or 0)
            total += item.amount
        self.total_price = total
