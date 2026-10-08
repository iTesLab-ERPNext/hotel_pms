import frappe
from frappe.model.document import Document


class HotelFamilyType(Document):
    def validate(self):
        if self.minimum_adults and self.maximum_adults:
            if self.minimum_adults > self.maximum_adults:
                frappe.throw("Minimum Adults cannot exceed Maximum Adults")
        if self.maximum_guests:
            total_max = (self.maximum_adults or 0) + (self.maximum_children or 0)
            if total_max > self.maximum_guests:
                frappe.throw("Maximum Adults + Maximum Children exceeds Maximum Guests")
