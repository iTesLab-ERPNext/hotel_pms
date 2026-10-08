import frappe
from frappe import _
from frappe.model.document import Document


class HotelFolio(Document):
    def validate(self):
        self.calculate_totals()

    def calculate_totals(self):
        room_charges = extra_charges = 0.0
        for item in self.items or []:
            amt = float(item.amount or 0)
            if item.charge_type == "Room":
                room_charges += amt
            else:
                extra_charges += amt
        self.room_charges   = room_charges
        self.extra_charges  = extra_charges
        self.total_charges  = room_charges + extra_charges

        # total payments from linked payment allocations
        payments = frappe.db.sql(
            "SELECT COALESCE(SUM(amount),0) FROM `tabHotel Payment Allocation` WHERE folio=%s AND docstatus!=2",
            self.name
        )
        self.total_payments = float(payments[0][0]) if payments else 0.0
        self.balance_due    = self.total_charges - self.total_payments

    def add_charge(self, charge_type, description, amount, service=None, reference=None):
        """Add a line item to the folio."""
        self.append("items", {
            "charge_type": charge_type,
            "description": description,
            "amount": amount,
            "service": service,
            "reference": reference,
            "date": frappe.utils.today(),
        })
        self.calculate_totals()
        self.save(ignore_permissions=True)
