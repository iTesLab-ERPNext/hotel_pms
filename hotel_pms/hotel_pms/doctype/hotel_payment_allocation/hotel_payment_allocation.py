import frappe
from frappe.model.document import Document


class HotelPaymentAllocation(Document):
    def on_submit(self):
        """Refresh folio payment total after submission."""
        pass

    def on_cancel(self):
        """Refresh folio totals after cancellation."""
        from hotel_pms.hotel_pms.api.folio import _recalc_totals
        folio = frappe.get_doc("Hotel Folio", self.folio)
        _recalc_totals(folio)
        folio.save()
