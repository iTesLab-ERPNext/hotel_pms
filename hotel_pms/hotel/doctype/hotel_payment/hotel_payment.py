import frappe
from frappe.model.document import Document
from hotel_pms.hotel import lifecycle


class HotelPayment(Document):
    def after_insert(self):
        if self.folio:
            lifecycle.update_folio_balance(self.folio)

    def on_trash(self):
        if self.folio:
            lifecycle.update_folio_balance(self.folio)
