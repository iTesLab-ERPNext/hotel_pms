import frappe
from frappe.utils import nowdate, now_datetime


@frappe.whitelist()
def checkin_from_reservation(reservation_name, room=None):
    """Create Hotel Stay + Hotel Folio from a confirmed reservation."""
    reservation = frappe.get_doc("Hotel Reservation", reservation_name)

    if reservation.status not in ("Confirmed", "Pending"):
        frappe.throw(f"Reservation must be Confirmed or Pending, not {reservation.status}")

    # Pick first room from reservation rooms if not specified
    if not room and reservation.rooms:
        room = reservation.rooms[0].room

    if not room:
        frappe.throw("No room assigned to this reservation")

    # Create stay
    stay = frappe.new_doc("Hotel Stay")
    stay.reservation = reservation_name
    stay.guest_name = reservation.guest_name
    stay.room = room
    stay.checkin_date = nowdate()
    stay.expected_checkout = reservation.departure_date
    stay.rate_per_night = frappe.get_value("Hotel Room", room, "rate") or 0
    stay.status = "Checked In"
    stay.insert()

    # Create folio
    folio = frappe.new_doc("Hotel Folio")
    folio.stay = stay.name
    folio.guest_name = reservation.guest_name
    folio.room = room
    folio.opening_date = nowdate()
    folio.status = "Open"
    folio.insert()

    # Mark room occupied
    frappe.db.set_value("Hotel Room", room, "status", "Occupied")

    # Update reservation
    frappe.db.set_value("Hotel Reservation", reservation_name, "status", "Checked In")

    frappe.db.commit()
    return {"stay": stay.name, "folio": folio.name}


@frappe.whitelist()
def walkin_checkin(guest_name, room, nights=1, rate_per_night=None):
    """Walk-in check-in without a prior reservation."""
    from frappe.utils import add_days

    if frappe.get_value("Hotel Room", room, "status") == "Occupied":
        frappe.throw(f"Room {room} is already occupied")

    if not rate_per_night:
        rate_per_night = frappe.get_value("Hotel Room", room, "rate") or 0

    stay = frappe.new_doc("Hotel Stay")
    stay.guest_name = guest_name
    stay.room = room
    stay.checkin_date = nowdate()
    stay.expected_checkout = add_days(nowdate(), int(nights))
    stay.rate_per_night = rate_per_night
    stay.status = "Checked In"
    stay.insert()

    folio = frappe.new_doc("Hotel Folio")
    folio.stay = stay.name
    folio.guest_name = guest_name
    folio.room = room
    folio.opening_date = nowdate()
    folio.status = "Open"
    folio.insert()

    frappe.db.set_value("Hotel Room", room, "status", "Occupied")
    frappe.db.commit()
    return {"stay": stay.name, "folio": folio.name}
