import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

class HotelHousekeeping(Document):
    def on_update(self):
        self.sync_room_status()

    def sync_room_status(self):
        status_map = {
            "Dirty": "Cleaning",
            "Cleaning": "Cleaning",
            "Clean": "Available",
            "Inspected": "Available",
            "Maintenance": "Maintenance"
        }
        room_status = status_map.get(self.status)
        if room_status and self.room:
            frappe.db.set_value("Hotel Room", self.room, "status", room_status)
        if self.status in ("Clean", "Inspected") and not self.completed_at:
            self.db_set("completed_at", now_datetime())
