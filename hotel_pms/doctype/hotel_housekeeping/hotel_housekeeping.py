import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class HotelHousekeeping(Document):
    def validate(self):
        if self.task_status == "In Progress" and not self.started_at:
            self.started_at = now_datetime()
        if self.task_status in ("Done", "Inspected") and not self.completed_at:
            self.completed_at = now_datetime()

    def on_update(self):
        """Sync room housekeeping_status when task is completed/inspected."""
        if self.task_status == "Done":
            frappe.db.set_value("Hotel Room", self.room, "housekeeping_status", "Clean")
        elif self.task_status == "Inspected":
            frappe.db.set_value("Hotel Room", self.room, "housekeeping_status", "Inspected")
        elif self.task_status == "In Progress":
            frappe.db.set_value("Hotel Room", self.room, "housekeeping_status", "Cleaning")
