"""
hotel_pms.hotel.lifecycle
~~~~~~~~~~~~~~~~~~~~~~~~~~
Business-logic service module for Hotel PMS.
DocType controllers import from here and delegate — they do NOT contain
business logic themselves.  This mirrors the pattern in erpnext_lmd/lastmile/lifecycle.py.

All public functions raise frappe.ValidationError / frappe.throw on business
rule violations and return plain dicts on success.
"""
import frappe
from frappe import _
from frappe.utils import date_diff, getdate, nowdate, now_datetime, add_days


# ── Reservation ────────────────────────────────────────────────────────────────

def validate_reservation(doc) -> None:
    """Full validation pipeline for Hotel Reservation."""
    _validate_dates(doc)
    _calculate_nights(doc)
    _calculate_family_totals(doc)
    _calculate_room_totals(doc)
    _check_room_availability(doc)


def _validate_dates(doc) -> None:
    if doc.arrival_date and doc.departure_date:
        if getdate(doc.departure_date) <= getdate(doc.arrival_date):
            frappe.throw(_("Departure date must be after arrival date"))


def _calculate_nights(doc) -> None:
    if doc.arrival_date and doc.departure_date:
        doc.number_of_nights = date_diff(doc.departure_date, doc.arrival_date)
        if doc.number_of_nights <= 0:
            frappe.throw(_("Number of nights must be greater than zero"))
        doc.number_of_days = doc.number_of_nights + 1


def _calculate_family_totals(doc) -> None:
    total_adults = total_children = total_infants = num_families = 0
    for f in (doc.families or []):
        f.total_guests = (f.adults or 0) + (f.children or 0) + (f.infants or 0)
        total_adults  += f.adults   or 0
        total_children += f.children or 0
        total_infants  += f.infants  or 0
        num_families   += 1
    doc.number_of_families = num_families
    doc.total_adults   = total_adults
    doc.total_children = total_children
    doc.total_infants  = total_infants
    doc.total_guests   = total_adults + total_children + total_infants


def _calculate_room_totals(doc) -> None:
    for r in (doc.rooms or []):
        r.total_guests = (r.adults or 0) + (r.children or 0) + (r.infants or 0)
        r.amount = (r.rate or 0) * (r.nights or doc.number_of_nights or 0)
        if r.room and not r.room_type:
            r.room_type = frappe.db.get_value("Hotel Room", r.room, "room_type")


def _check_room_availability(doc) -> None:
    if not doc.rooms or doc.status in ("Cancelled", "No Show"):
        return
    for res_room in doc.rooms:
        if not res_room.room:
            continue
        conflicts = frappe.db.sql("""
            SELECT r.name
            FROM `tabHotel Reservation Room` rr
            JOIN `tabHotel Reservation` r ON r.name = rr.parent
            WHERE rr.room = %s
              AND r.name != %s
              AND r.status NOT IN ('Cancelled', 'No Show', 'Completed')
              AND r.arrival_date < %s
              AND r.departure_date > %s
        """, (res_room.room, doc.name or "NEW", doc.departure_date, doc.arrival_date))
        if conflicts:
            frappe.throw(_(
                "Room {0} is already reserved for the selected dates"
            ).format(res_room.room))


# ── Check-in ───────────────────────────────────────────────────────────────────

def check_in(reservation_name: str) -> dict:
    """Check in a confirmed reservation.

    Creates Hotel Stay + Hotel Folio for each room.
    Returns {"stays": [names], "message": str}.
    """
    frappe.has_permission("Hotel Stay", "create", throw=True)

    res = frappe.get_doc("Hotel Reservation", reservation_name)

    if res.status == "Cancelled":
        frappe.throw(_("Cannot check in a cancelled reservation"))
    if res.status == "No Show":
        frappe.throw(_("Cannot check in a No Show reservation"))
    if res.status == "Checked In":
        frappe.throw(_("Reservation is already checked in"))
    if res.status == "Completed":
        frappe.throw(_("Reservation is already completed"))
    if not res.rooms:
        frappe.throw(_("No rooms assigned to this reservation"))

    stays = []
    for res_room in res.rooms:
        room = frappe.get_doc("Hotel Room", res_room.room)
        if room.status == "Occupied":
            frappe.throw(_("Room {0} is already occupied").format(res_room.room))
        if room.status in ("Maintenance", "Out of Service", "Blocked"):
            frappe.throw(_(
                "Room {0} is not available (status: {1})"
            ).format(res_room.room, room.status))

        stay = frappe.get_doc({
            "doctype": "Hotel Stay",
            "customer": res.customer,
            "reservation": reservation_name,
            "room": res_room.room,
            "checkin_date": now_datetime(),
            "expected_checkout": res.departure_date,
            "status": "Active",
        })
        stay.insert(ignore_permissions=True)
        stays.append(stay.name)

        frappe.db.set_value("Hotel Room", res_room.room, "status", "Occupied")

        if not frappe.db.exists("Hotel Folio",
                {"reservation": reservation_name, "stay": stay.name}):
            folio = frappe.get_doc({
                "doctype": "Hotel Folio",
                "customer": res.customer,
                "reservation": reservation_name,
                "stay": stay.name,
                "status": "Open",
            })
            folio.insert(ignore_permissions=True)

    frappe.db.set_value("Hotel Reservation", reservation_name, "status", "Checked In")
    return {"stays": stays, "message": _("Check-in successful")}


# ── Check-out ──────────────────────────────────────────────────────────────────

def check_out(stay_name: str) -> dict:
    """Check out an active stay. Returns {"room": room_name, "message": str}."""
    frappe.has_permission("Hotel Stay", "write", throw=True)

    stay = frappe.get_doc("Hotel Stay", stay_name)
    if stay.status != "Active":
        frappe.throw(_(
            "Cannot check out: stay is not active (status: {0})"
        ).format(stay.status))

    frappe.db.set_value("Hotel Stay", stay_name, {
        "status": "Checked Out",
        "actual_checkout": now_datetime(),
    })
    frappe.db.set_value("Hotel Room", stay.room, {
        "status": "Cleaning",
        "housekeeping_status": "Dirty",
    })

    if stay.reservation:
        active_stays = frappe.db.count(
            "Hotel Stay", {"reservation": stay.reservation, "status": "Active"})
        if active_stays == 0:
            frappe.db.set_value(
                "Hotel Reservation", stay.reservation, "status", "Completed")

        folio = frappe.db.get_value(
            "Hotel Folio", {"stay": stay_name, "status": ["!=", "Closed"]}, "name")
        if folio:
            frappe.db.set_value("Hotel Folio", folio, "status", "Closed")

    return {"room": stay.room, "message": _("Check-out successful")}


# ── Room move ──────────────────────────────────────────────────────────────────

def move_room(stay_name: str, new_room: str,
              reason: str = None, new_rate=None) -> dict:
    """Move guest from their current room to new_room."""
    frappe.has_permission("Hotel Room Movement", "create", throw=True)

    stay = frappe.get_doc("Hotel Stay", stay_name)
    if stay.status != "Active":
        frappe.throw(_("Cannot move guest: stay is not active"))

    new_room_doc = frappe.get_doc("Hotel Room", new_room)
    if new_room_doc.status == "Occupied":
        frappe.throw(_("Room {0} is already occupied").format(new_room))
    if new_room_doc.status in ("Maintenance", "Out of Service", "Blocked"):
        frappe.throw(_(
            "Room {0} is not available (status: {1})"
        ).format(new_room, new_room_doc.status))
    if new_room == stay.room:
        frappe.throw(_("New room must be different from the current room"))

    old_room = stay.room
    movement = frappe.get_doc({
        "doctype": "Hotel Room Movement",
        "stay": stay_name,
        "reservation": stay.reservation,
        "customer": stay.customer,
        "old_room": old_room,
        "new_room": new_room,
        "movement_date": now_datetime(),
        "reason": reason or "Guest Request",
        "new_rate": new_rate,
    })
    movement.insert(ignore_permissions=True)

    frappe.db.set_value("Hotel Room", old_room, "status", "Cleaning")
    frappe.db.set_value("Hotel Room", new_room, "status", "Occupied")
    frappe.db.set_value("Hotel Stay", stay_name, "room", new_room)

    return {
        "movement": movement.name,
        "message": _("Guest moved from {0} to {1}").format(old_room, new_room),
    }


# ── Folio ──────────────────────────────────────────────────────────────────────

def add_folio_charge(folio_name: str, charge_type: str, description: str,
                     quantity, rate, date=None, service=None, room=None) -> dict:
    """Append a charge line to an open folio."""
    frappe.has_permission("Hotel Folio", "write", throw=True)

    folio = frappe.get_doc("Hotel Folio", folio_name)
    if folio.status == "Closed":
        frappe.throw(_("Cannot add charges to a closed folio"))

    amount = float(quantity) * float(rate)
    folio.append("items", {
        "date": date or nowdate(),
        "charge_type": charge_type,
        "description": description,
        "quantity": float(quantity),
        "rate": float(rate),
        "amount": amount,
        "service": service,
        "room": room,
    })
    folio.save(ignore_permissions=True)
    return {"folio": folio_name}


def update_folio_balance(folio_name: str) -> None:
    """Recalculate and persist folio totals + status."""
    folio = frappe.get_doc("Hotel Folio", folio_name)

    total_charges = sum((item.amount or 0) for item in (folio.items or []))
    total_payments = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0) FROM `tabHotel Payment`
        WHERE folio = %s
    """, folio_name)[0][0] or 0

    balance = total_charges - float(total_payments)

    if total_payments >= total_charges and total_charges > 0:
        status = "Paid"
    elif float(total_payments) > 0:
        status = "Partially Paid"
    else:
        status = "Open"

    frappe.db.set_value("Hotel Folio", folio_name, {
        "total_charges": total_charges,
        "total_payments": float(total_payments),
        "balance": balance,
        "status": status,
    })


# ── Payment ────────────────────────────────────────────────────────────────────

def create_payment(customer: str, amount, payment_method: str,
                   payment_type: str = "Partial",
                   reservation=None, stay=None, folio=None,
                   reference=None, notes=None) -> dict:
    """Create a payment record and refresh the linked folio balance."""
    frappe.has_permission("Hotel Payment", "create", throw=True)

    amount = float(amount)
    if amount <= 0:
        frappe.throw(_("Payment amount must be greater than zero"))

    payment = frappe.get_doc({
        "doctype": "Hotel Payment",
        "customer": customer,
        "reservation": reservation,
        "stay": stay,
        "folio": folio,
        "payment_date": nowdate(),
        "payment_type": payment_type,
        "payment_method": payment_method,
        "amount": amount,
        "reference": reference,
        "notes": notes,
    })
    payment.insert(ignore_permissions=True)

    if folio:
        update_folio_balance(folio)

    return {"payment": payment.name}


# ── Housekeeping ───────────────────────────────────────────────────────────────

def update_housekeeping_status(room: str, new_status: str,
                               notes: str = None) -> dict:
    """Log a housekeeping status change and update the room record."""
    frappe.has_permission("Hotel Housekeeping", "create", throw=True)

    old_status = frappe.db.get_value("Hotel Room", room, "housekeeping_status")

    hk = frappe.get_doc({
        "doctype": "Hotel Housekeeping",
        "room": room,
        "date": nowdate(),
        "previous_status": old_status,
        "new_status": new_status,
        "assigned_to": frappe.session.user,
        "notes": notes or "",
    })
    hk.insert(ignore_permissions=True)

    frappe.db.set_value("Hotel Room", room, "housekeeping_status", new_status)

    if new_status in ("Clean", "Inspected"):
        current_status = frappe.db.get_value("Hotel Room", room, "status")
        if current_status == "Cleaning":
            frappe.db.set_value("Hotel Room", room, "status", "Available")

    return {"hk_record": hk.name}
