import frappe
from frappe.model.document import Document


class HotelCustomer(Document):
    def validate(self):
        self.full_name = " ".join(filter(None, [self.first_name, self.last_name]))
