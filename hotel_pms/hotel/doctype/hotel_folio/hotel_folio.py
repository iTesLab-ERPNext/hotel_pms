import frappe
from frappe.model.document import Document


class HotelFolio(Document):
    def validate(self):
        self.calculate_totals()

    def calculate_totals(self):
        self.total_charges = sum((item.amount or 0) for item in (self.items or []))
        total_payments = frappe.db.sql("""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM `tabHotel Payment`
            WHERE folio = %s
        """, self.name, as_dict=True)
        self.total_payments = total_payments[0].total if total_payments else 0
        self.balance = self.total_charges - self.total_payments

        if self.total_payments >= self.total_charges and self.total_charges > 0:
            self.status = "Paid"
        elif self.total_payments > 0:
            self.status = "Partially Paid"
        elif self.status not in ("Closed",):
            self.status = "Open"
