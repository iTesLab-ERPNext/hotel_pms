import frappe
from frappe.model.document import Document
from hotel_pms.hotel import lifecycle


class HotelStay(Document):
    @frappe.whitelist()
    def do_check_out(self):
        return lifecycle.check_out(self.name)

    @frappe.whitelist()
    def do_move_room(self, new_room, reason=None, new_rate=None):
        new_rate = frappe.parse_json(new_rate) if isinstance(new_rate, str) else new_rate
        return lifecycle.move_room(self.name, new_room, reason, new_rate)

    def on_cancel(self):
        # If manually cancelled, free the room
        if self.room and self.status == "Active":
            frappe.db.set_value("Hotel Room", self.room, "status", "Available")
