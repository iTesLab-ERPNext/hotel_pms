import frappe
from frappe.model.document import Document
from hotel_pms.hotel import lifecycle


class HotelFolio(Document):
    def validate(self):
        self._recalculate()

    def _recalculate(self):
        total = sum((item.amount or 0) for item in (self.items or []))
        self.total_charges = total

    @frappe.whitelist()
    def add_charge(self, charge_type, description, quantity, rate,
                   date=None, service=None, room=None):
        return lifecycle.add_folio_charge(
            self.name, charge_type, description, quantity, rate, date, service, room)

    @frappe.whitelist()
    def refresh_balance(self):
        lifecycle.update_folio_balance(self.name)
        return {"message": frappe._("Balance refreshed")}
