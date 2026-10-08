import frappe
from frappe.model.document import Document

class HotelFolio(Document):
    def validate(self):
        self.calculate_totals()

    def calculate_totals(self):
        total = 0
        for item in self.items:
            item.amount = (item.quantity or 1) * (item.rate or 0)
            total += item.amount
        self.total_charges = total

        payments = frappe.db.sql("""
            SELECT COALESCE(SUM(amount), 0) as paid
            FROM `tabHotel Payment`
            WHERE folio = %s AND docstatus = 1
        """, self.name)
        self.total_payments = payments[0][0] if payments else 0
        self.balance = self.total_charges - self.total_payments

    def update_payment_totals(self):
        self.calculate_totals()
        self.save(ignore_permissions=True)
