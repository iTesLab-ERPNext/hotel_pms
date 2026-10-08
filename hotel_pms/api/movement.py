import frappe
from frappe import _

@frappe.whitelist()
def move_room(stay, new_room, reason=None, new_rate=None, notes=None):
    """Move a guest to a different room."""
    stay_doc = frappe.get_doc("Hotel Stay", stay)
    if stay_doc.status != "Active":
        frappe.throw(_("Can only move room for an Active stay"))

    old_room = stay_doc.room

    # Check new room availability
    room_status = frappe.db.get_value("Hotel Room", new_room, "status")
    if room_status != "Available":
        frappe.throw(_("Room {0} is not available (Status: {1})").format(new_room, room_status))

    old_rate = None
    if stay_doc.reservation:
        res = frappe.get_doc("Hotel Reservation", stay_doc.reservation)
        for r in res.rooms:
            if r.room == old_room:
                old_rate = r.rate

    movement = frappe.get_doc({
        "doctype": "Hotel Room Movement",
        "stay": stay,
        "customer": stay_doc.customer,
        "old_room": old_room,
        "new_room": new_room,
        "reason": reason,
        "old_rate": old_rate,
        "new_rate": new_rate,
        "notes": notes
    })
    movement.insert(ignore_permissions=True)
    movement.submit()

    return {"success": True, "movement": movement.name}
