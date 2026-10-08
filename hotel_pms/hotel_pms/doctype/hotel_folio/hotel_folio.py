import frappe
from frappe.model.document import Document
from frappe.utils import flt


class HotelFolio(Document):
    def before_save(self):
        self.total_charges = sum(flt(i.amount) for i in (self.items or []))
