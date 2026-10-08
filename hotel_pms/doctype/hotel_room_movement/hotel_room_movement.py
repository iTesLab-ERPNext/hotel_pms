import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class HotelRoomMovement(Document):
    def validate(self):
        if self.movement_type == "Room Transfer" and not self.to_room:
            frappe.throw(_("To Room is required for a Room Transfer"))
        if not self.movement_date:
            self.movement_date = now_datetime()
