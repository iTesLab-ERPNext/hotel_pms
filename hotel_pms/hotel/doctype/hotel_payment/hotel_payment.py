import frappe
from frappe import _
from frappe.model.document import Document


class HotelPayment(Document):
    def validate(self):
        if not self.amount or self.amount <= 0:
            frappe.throw(_("Payment amount must be greater than zero"))

    def on_submit(self):
        if self.folio:
            self._update_folio_balance()

    def on_cancel(self):
        if self.folio:
            self._update_folio_balance()

    def _update_folio_balance(self):
        folio = frappe.get_doc("Hotel Folio", self.folio)
        total_charges = sum((item.amount or 0) for item in (folio.items or []))
        total_payments = frappe.db.sql("""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM `tabHotel Payment`
            WHERE folio = %s AND docstatus = 1
        """, self.folio, as_dict=True)[0].total or 0

        balance = total_charges - total_payments
        status = "Open"
        if total_payments >= total_charges and total_charges > 0:
            status = "Paid"
        elif total_payments > 0:
            status = "Partially Paid"

        frappe.db.set_value("Hotel Folio", self.folio, {
            "total_charges": total_charges,
            "total_payments": total_payments,
            "balance": balance,
            "status": status
        })
