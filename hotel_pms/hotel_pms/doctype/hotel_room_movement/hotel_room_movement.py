import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

class HotelRoomMovement(Document):
    def validate(self):
        if self.old_room == self.new_room:
            frappe.throw("Old Room and New Room cannot be the same")

        # Check new room is available
        room_status = frappe.db.get_value("Hotel Room", self.new_room, "status")
        if room_status not in ("Available",):
            frappe.throw(f"Room {self.new_room} is not available (Status: {room_status})")

    def on_submit(self):
        # Release old room
        frappe.db.set_value("Hotel Room", self.old_room, "status", "Available")
        # Occupy new room
        frappe.db.set_value("Hotel Room", self.new_room, "status", "Occupied")
        # Update stay
        frappe.db.set_value("Hotel Stay", self.stay, "room", self.new_room)
        # Update reservation room if exists
        stay = frappe.get_doc("Hotel Stay", self.stay)
        if stay.reservation:
            res = frappe.get_doc("Hotel Reservation", stay.reservation)
            for r in res.rooms:
                if r.room == self.old_room:
                    r.room = self.new_room
                    if self.new_rate:
                        r.rate = self.new_rate
            res.save(ignore_permissions=True)
        # Update folio
        if stay.reservation:
            folios = frappe.get_all("Hotel Folio", filters={"stay": self.stay}, pluck="name")
            for folio_name in folios:
                frappe.db.set_value("Hotel Folio", folio_name, "room", self.new_room)
