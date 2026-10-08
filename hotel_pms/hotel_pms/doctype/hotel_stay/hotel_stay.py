import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

class HotelStay(Document):
    def validate(self):
        if not self.checkin_date:
            self.checkin_date = now_datetime()

    def checkout(self):
        self.status = "Checked Out"
        self.actual_checkout = now_datetime()
        self.save(ignore_permissions=True)
        frappe.db.set_value("Hotel Room", self.room, "status", "Cleaning")
        if self.reservation:
            frappe.db.set_value("Hotel Reservation", self.reservation, "status", "Checked Out")
        # Create housekeeping task
        create_housekeeping(self.room)

def create_housekeeping(room):
    if not frappe.db.exists("Hotel Housekeeping", {"room": room, "status": ["in", ["Dirty","Cleaning"]]}):
        hk = frappe.get_doc({
            "doctype": "Hotel Housekeeping",
            "room": room,
            "status": "Dirty",
            "date": frappe.utils.today()
        })
        hk.insert(ignore_permissions=True)
