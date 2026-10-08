import frappe
from frappe import _
from frappe.model.document import Document


VALID_STATUS_TRANSITIONS = {
    "Available":    ["Reserved", "Occupied", "Maintenance", "Out of Service", "Blocked"],
    "Reserved":     ["Available", "Occupied", "Maintenance", "Out of Service"],
    "Occupied":     ["Dirty", "Maintenance"],
    "Dirty":        ["Cleaning", "Available", "Out of Service"],
    "Cleaning":     ["Clean", "Dirty"],
    "Maintenance":  ["Available", "Out of Service"],
    "Out of Service":["Available", "Maintenance"],
    "Blocked":      ["Available"],
}

HOUSEKEEPING_MAP = {
    "Clean":        "Clean",
    "Dirty":        "Dirty",
    "Cleaning":     "Cleaning",
    "Inspected":    "Clean",
    "Out of Service":"Out of Service",
}


class HotelRoom(Document):
    def validate(self):
        if not self.room_name:
            self.room_name = f"Room {self.room_number}"

    def before_save(self):
        old = self.get_doc_before_save()
        if old and old.status != self.status:
            allowed = VALID_STATUS_TRANSITIONS.get(old.status, [])
            if self.status not in allowed:
                frappe.throw(
                    _("Cannot change room status from {0} to {1}").format(old.status, self.status)
                )

    def set_occupied(self, guest_name=None, reservation=None):
        self.status = "Occupied"
        self.housekeeping_status = "Dirty"
        if guest_name:
            self.current_guest = guest_name
        if reservation:
            self.current_reservation = reservation
        self.save(ignore_permissions=True)

    def set_available(self):
        self.status = "Available"
        self.current_guest = None
        self.current_reservation = None
        self.save(ignore_permissions=True)

    def set_dirty(self):
        self.status = "Dirty"
        self.housekeeping_status = "Dirty"
        self.current_guest = None
        self.current_reservation = None
        self.save(ignore_permissions=True)
