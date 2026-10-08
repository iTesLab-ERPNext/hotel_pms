import frappe
from frappe import _
from frappe.utils import now_datetime, today


@frappe.whitelist()
def checkin_from_reservation(reservation_name, room=None):
    """
    Walk-through check-in from a confirmed reservation.
    Creates Hotel Stay + Hotel Folio and links them.
    """
    res = frappe.get_doc("Hotel Reservation", reservation_name)

    if res.reservation_status not in ("Confirmed", "Deposit Paid"):
        frappe.throw(_(f"Reservation must be Confirmed or Deposit Paid to check in (current: {res.reservation_status})"))

    # Determine room
    if not room:
        if res.rooms:
            room = res.rooms[0].room
        else:
            frappe.throw(_("No room assigned on reservation"))

    room_doc = frappe.get_doc("Hotel Room", room)
    if room_doc.status not in ("Available", "Dirty", "Clean", "Inspected"):
        frappe.throw(_(f"Room {room} is not available for check-in (status: {room_doc.status})"))

    # Create Folio
    folio = frappe.new_doc("Hotel Folio")
    folio.reservation = reservation_name
    folio.customer = res.customer
    folio.room = room
    folio.folio_status = "Open"
    folio.insert(ignore_permissions=True)

    # Create Stay
    stay = frappe.new_doc("Hotel Stay")
    stay.guest = res.customer
    stay.reservation = reservation_name
    stay.room = room
    stay.stay_status = "In House"
    stay.folio = folio.name
    stay.checkin_date = now_datetime()
    stay.expected_checkout = res.departure_date
    stay.number_of_guests = res.total_guests or 1
    stay.insert(ignore_permissions=True)

    # Link folio to stay
    folio.stay = stay.name
    folio.save(ignore_permissions=True)

    # Mark room occupied
    room_doc.status = "Occupied"
    room_doc.current_guest = res.customer
    room_doc.current_reservation = reservation_name
    room_doc.save(ignore_permissions=True)

    # Update reservation
    res.reservation_status = "Checked In"
    res.save(ignore_permissions=True)

    return {"stay": stay.name, "folio": folio.name}


@frappe.whitelist()
def walkin_checkin(customer, room, expected_checkout, number_of_guests=1, rate_per_night=0):
    """Direct walk-in check-in without a prior reservation."""
    room_doc = frappe.get_doc("Hotel Room", room)
    if room_doc.status not in ("Available", "Dirty", "Clean", "Inspected"):
        frappe.throw(_(f"Room {room} is not available (status: {room_doc.status})"))

    folio = frappe.new_doc("Hotel Folio")
    folio.customer = customer
    folio.room = room
    folio.folio_status = "Open"
    folio.insert(ignore_permissions=True)

    stay = frappe.new_doc("Hotel Stay")
    stay.guest = customer
    stay.room = room
    stay.stay_status = "In House"
    stay.folio = folio.name
    stay.checkin_date = now_datetime()
    stay.expected_checkout = expected_checkout
    stay.number_of_guests = number_of_guests
    stay.rate_per_night = rate_per_night
    stay.insert(ignore_permissions=True)

    folio.stay = stay.name
    folio.save(ignore_permissions=True)

    room_doc.status = "Occupied"
    room_doc.current_guest = customer
    room_doc.save(ignore_permissions=True)

    return {"stay": stay.name, "folio": folio.name}
