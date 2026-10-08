import frappe
from frappe import _
from frappe.model.document import Document


class HotelPaymentAllocation(Document):
    def validate(self):
        if float(self.amount or 0) <= 0:
            frappe.throw(_("Payment amount must be greater than zero"))

    def on_submit(self):
        self._update_folio()

    def on_cancel(self):
        self._update_folio()

    def _update_folio(self):
        if self.folio:
            try:
                folio = frappe.get_doc("Hotel Folio", self.folio)
                folio.calculate_totals()
                folio.save(ignore_permissions=True)
            except frappe.DoesNotExistError:
                pass
