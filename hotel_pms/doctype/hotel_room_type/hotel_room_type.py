import frappe
from frappe.model.document import Document


class HotelRoomType(Document):
    def validate(self):
        if self.capacity_adults and self.capacity_children:
            if not self.maximum_occupancy:
                self.maximum_occupancy = self.capacity_adults + self.capacity_children
        if self.maximum_occupancy and self.capacity_adults:
            if self.maximum_occupancy < self.capacity_adults:
                frappe.throw("Maximum Occupancy cannot be less than Capacity Adults")
        if self.base_price and self.base_price < 0:
            frappe.throw("Base Price cannot be negative")
