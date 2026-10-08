import frappe
from frappe import _
from frappe.model.document import Document


class HotelSeason(Document):
    def validate(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            frappe.throw(_("End Date must be after Start Date"))
