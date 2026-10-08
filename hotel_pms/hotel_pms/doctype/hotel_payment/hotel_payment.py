import frappe
from frappe.model.document import Document

class HotelPayment(Document):
    def validate(self):
        if (self.amount or 0) <= 0:
            frappe.throw("Payment amount must be greater than zero")

    def on_submit(self):
        # Update folio totals
        if self.folio:
            folio = frappe.get_doc("Hotel Folio", self.folio)
            folio.update_payment_totals()

        # Update reservation advance payment
        if self.reservation and self.payment_type == "Advance Payment":
            res = frappe.get_doc("Hotel Reservation", self.reservation)
            res.advance_payment = (res.advance_payment or 0) + self.amount
            res.balance = res.total_amount - res.advance_payment
            res.save(ignore_permissions=True)

    def on_cancel(self):
        if self.folio:
            folio = frappe.get_doc("Hotel Folio", self.folio)
            folio.update_payment_totals()
