import frappe
from frappe import _
from frappe.utils import nowdate, now_datetime, date_diff, add_days, getdate


@frappe.whitelist()
def get_dashboard_data():
    """Return all dashboard statistics."""
    today = nowdate()

    rooms = frappe.get_all("Hotel Room", fields=["status", "housekeeping_status"])
    room_stats = {
        "total": len(rooms),
        "available": 0, "reserved": 0, "occupied": 0,
        "cleaning": 0, "maintenance": 0, "blocked": 0, "out_of_service": 0
    }
    for r in rooms:
        s = (r.status or "").lower().replace(" ", "_")
        if s in room_stats:
            room_stats[s] += 1

    today_arrivals = frappe.db.count("Hotel Reservation",
        {"arrival_date": today, "status": ["in", ["Confirmed", "Checked In"]]})
    today_departures = frappe.db.count("Hotel Reservation",
        {"departure_date": today, "status": "Checked In"})
    active_stays = frappe.db.count("Hotel Stay", {"status": "Active"})

    res_stats = {}
    for status in ["Draft", "Confirmed", "Checked In", "Completed", "Cancelled", "No Show"]:
        res_stats[status.lower().replace(" ", "_")] = frappe.db.count(
            "Hotel Reservation", {"status": status})

    today_payments = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM `tabHotel Payment`
        WHERE payment_date = %s AND docstatus = 1
    """, today, as_dict=True)[0].total or 0

    outstanding = frappe.db.sql("""
        SELECT COALESCE(SUM(balance), 0) as total
        FROM `tabHotel Folio`
        WHERE status != 'Closed' AND balance > 0
    """, as_dict=True)[0].total or 0

    return {
        "rooms": room_stats,
        "today": {
            "arrivals": today_arrivals,
            "departures": today_departures,
            "active_stays": active_stays,
            "available_rooms": room_stats["available"]
        },
        "reservations": res_stats,
        "financial": {
            "today_payments": float(today_payments),
            "outstanding_balances": float(outstanding)
        }
    }


@frappe.whitelist()
def get_room_availability(arrival_date, departure_date, room_type=None):
    """Return rooms available for the given dates."""
    filters = {"active": 1}
    if room_type:
        filters["room_type"] = room_type

    all_rooms = frappe.get_all("Hotel Room",
        filters=filters,
        fields=["name", "room_number", "room_name", "room_type", "floor", "capacity", "status"])

    busy_rooms = frappe.db.sql("""
        SELECT DISTINCT rr.room
        FROM `tabHotel Reservation Room` rr
        JOIN `tabHotel Reservation` r ON r.name = rr.parent
        WHERE r.status NOT IN ('Cancelled', 'No Show', 'Completed')
          AND r.arrival_date < %s
          AND r.departure_date > %s
    """, (departure_date, arrival_date), as_dict=True)

    busy_room_names = {b.room for b in busy_rooms}

    active_stays = frappe.db.sql(
        "SELECT DISTINCT room FROM `tabHotel Stay` WHERE status = 'Active'",
        as_dict=True)
    busy_room_names.update(s.room for s in active_stays)

    available = [r for r in all_rooms if r.name not in busy_room_names]
    return available


@frappe.whitelist()
def get_room_calendar(from_date=None, to_date=None, room=None, room_type=None):
    """Return calendar data for rooms."""
    if not from_date:
        from_date = nowdate()
    if not to_date:
        to_date = add_days(from_date, 30)

    filters = {"active": 1}
    if room:
        filters["name"] = room
    if room_type:
        filters["room_type"] = room_type

    rooms = frappe.get_all("Hotel Room", filters=filters,
        fields=["name", "room_number", "room_name", "room_type", "floor", "status"])

    room_names = [r.name for r in rooms]
    if not room_names:
        return {"rooms": [], "reservations": []}

    reservations = frappe.db.sql("""
        SELECT rr.room, r.name as reservation, r.customer,
               hc.full_name as customer_name,
               r.arrival_date, r.departure_date, r.status,
               r.number_of_nights
        FROM `tabHotel Reservation Room` rr
        JOIN `tabHotel Reservation` r ON r.name = rr.parent
        LEFT JOIN `tabHotel Customer` hc ON hc.name = r.customer
        WHERE rr.room IN %(rooms)s
          AND r.arrival_date <= %(to_date)s
          AND r.departure_date >= %(from_date)s
          AND r.status NOT IN ('Cancelled', 'No Show')
        ORDER BY r.arrival_date
    """, {"rooms": room_names, "from_date": from_date, "to_date": to_date}, as_dict=True)

    return {"rooms": rooms, "reservations": reservations}


@frappe.whitelist()
def check_in(reservation):
    """Check in a reservation - create Hotel Stay records and update room statuses."""
    frappe.has_permission("Hotel Stay", "create", throw=True)

    res = frappe.get_doc("Hotel Reservation", reservation)

    if res.status == "Cancelled":
        frappe.throw(_("Cannot check in a cancelled reservation"))
    if res.status == "No Show":
        frappe.throw(_("Cannot check in a No Show reservation"))
    if res.status == "Checked In":
        frappe.throw(_("This reservation is already checked in"))
    if res.status == "Completed":
        frappe.throw(_("This reservation is already completed"))
    if not res.rooms:
        frappe.throw(_("No rooms assigned to this reservation"))

    stays = []
    for res_room in res.rooms:
        room = frappe.get_doc("Hotel Room", res_room.room)
        if room.status == "Occupied":
            frappe.throw(_("Room {0} is already occupied").format(res_room.room))
        if room.status in ["Maintenance", "Out of Service", "Blocked"]:
            frappe.throw(_("Room {0} is not available (status: {1})").format(
                res_room.room, room.status))

        stay = frappe.get_doc({
            "doctype": "Hotel Stay",
            "customer": res.customer,
            "reservation": reservation,
            "room": res_room.room,
            "checkin_date": now_datetime(),
            "expected_checkout": res.departure_date,
            "status": "Active",
        })
        stay.insert(ignore_permissions=True)
        stays.append(stay.name)

        frappe.db.set_value("Hotel Room", res_room.room, "status", "Occupied")

        existing_folio = frappe.db.exists("Hotel Folio",
            {"reservation": reservation, "stay": stay.name})
        if not existing_folio:
            folio = frappe.get_doc({
                "doctype": "Hotel Folio",
                "customer": res.customer,
                "reservation": reservation,
                "stay": stay.name,
                "status": "Open"
            })
            folio.insert(ignore_permissions=True)

    frappe.db.set_value("Hotel Reservation", reservation, "status", "Checked In")

    return {
        "success": True,
        "message": _("Check-in successful"),
        "stays": stays
    }


@frappe.whitelist()
def check_out(stay_name):
    """Check out a stay - update stay, room, and reservation."""
    frappe.has_permission("Hotel Stay", "write", throw=True)

    stay = frappe.get_doc("Hotel Stay", stay_name)

    if stay.status != "Active":
        frappe.throw(_("Cannot check out: stay is not active (status: {0})").format(stay.status))

    frappe.db.set_value("Hotel Stay", stay_name, {
        "status": "Checked Out",
        "actual_checkout": now_datetime()
    })

    frappe.db.set_value("Hotel Room", stay.room, {
        "status": "Cleaning",
        "housekeeping_status": "Dirty"
    })

    if stay.reservation:
        active_stays = frappe.db.count("Hotel Stay",
            {"reservation": stay.reservation, "status": "Active"})
        if active_stays == 0:
            frappe.db.set_value("Hotel Reservation", stay.reservation, "status", "Completed")

        folio = frappe.db.get_value("Hotel Folio",
            {"stay": stay_name, "status": ["!=", "Closed"]}, "name")
        if folio:
            frappe.db.set_value("Hotel Folio", folio, "status", "Closed")

    return {
        "success": True,
        "message": _("Check-out successful"),
        "room": stay.room
    }


@frappe.whitelist()
def move_room(stay_name, new_room, reason=None, new_rate=None):
    """Move a guest from their current room to a different room."""
    frappe.has_permission("Hotel Room Movement", "create", throw=True)

    stay = frappe.get_doc("Hotel Stay", stay_name)

    if stay.status != "Active":
        frappe.throw(_("Cannot move guest: stay is not active"))

    new_room_doc = frappe.get_doc("Hotel Room", new_room)

    if new_room_doc.status == "Occupied":
        frappe.throw(_("Room {0} is already occupied").format(new_room))
    if new_room_doc.status in ["Maintenance", "Out of Service", "Blocked"]:
        frappe.throw(_("Room {0} is not available (status: {1})").format(
            new_room, new_room_doc.status))
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
        "success": True,
        "message": _("Guest moved from {0} to {1}").format(old_room, new_room),
        "movement": movement.name
    }


@frappe.whitelist()
def add_folio_charge(folio, charge_type, description, quantity, rate,
                     date=None, service=None, room=None):
    """Add a charge line to a folio."""
    frappe.has_permission("Hotel Folio", "write", throw=True)

    folio_doc = frappe.get_doc("Hotel Folio", folio)

    if folio_doc.status == "Closed":
        frappe.throw(_("Cannot add charges to a closed folio"))

    amount = float(quantity) * float(rate)
    folio_doc.append("items", {
        "date": date or nowdate(),
        "charge_type": charge_type,
        "description": description,
        "quantity": float(quantity),
        "rate": float(rate),
        "amount": amount,
        "service": service,
        "room": room,
    })
    folio_doc.save(ignore_permissions=True)

    return {"success": True, "folio": folio}


@frappe.whitelist()
def create_payment(customer, amount, payment_method, payment_type="Partial",
                   reservation=None, stay=None, folio=None, reference=None, notes=None):
    """Create a payment record and update the linked folio."""
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
        _update_folio_balance(folio)

    return {"success": True, "payment": payment.name}


def _update_folio_balance(folio_name):
    """Recalculate and save folio balance."""
    folio = frappe.get_doc("Hotel Folio", folio_name)

    total_charges = sum((item.amount or 0) for item in (folio.items or []))

    total_payments = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM `tabHotel Payment`
        WHERE folio = %s
    """, folio_name, as_dict=True)[0].total or 0

    balance = total_charges - total_payments

    status = "Open"
    if total_payments >= total_charges and total_charges > 0:
        status = "Paid"
    elif total_payments > 0:
        status = "Partially Paid"

    frappe.db.set_value("Hotel Folio", folio_name, {
        "total_charges": total_charges,
        "total_payments": total_payments,
        "balance": balance,
        "status": status
    })


@frappe.whitelist()
def get_folio_details(reservation=None, stay=None):
    """Get folio document with all charges and payment history."""
    filters = {}
    if reservation:
        filters["reservation"] = reservation
    if stay:
        filters["stay"] = stay

    folio_name = frappe.db.get_value("Hotel Folio", filters, "name")
    if not folio_name:
        return None

    folio_doc = frappe.get_doc("Hotel Folio", folio_name)

    payments = frappe.get_all("Hotel Payment",
        filters={"folio": folio_name},
        fields=["name", "payment_date", "payment_type", "payment_method", "amount", "reference"])

    return {
        "folio": folio_doc.as_dict(),
        "payments": payments
    }


@frappe.whitelist()
def get_planning_board(from_date=None, days=14):
    """Return room planning board data for the given date range."""
    if not from_date:
        from_date = nowdate()

    days = int(days)
    to_date = add_days(from_date, days)

    rooms = frappe.get_all("Hotel Room",
        filters={"active": 1},
        fields=["name", "room_number", "room_name", "room_type", "floor", "status"],
        order_by="room_number")

    if not rooms:
        return {"rooms": [], "reservations": [], "dates": []}

    from datetime import timedelta
    dates = []
    current = getdate(from_date)
    end = getdate(to_date)
    while current <= end:
        dates.append(str(current))
        current += timedelta(days=1)

    room_names = [r.name for r in rooms]

    reservations = frappe.db.sql("""
        SELECT rr.room, r.name as reservation, r.customer,
               hc.full_name as customer_name,
               r.arrival_date, r.departure_date, r.status,
               r.number_of_nights
        FROM `tabHotel Reservation Room` rr
        JOIN `tabHotel Reservation` r ON r.name = rr.parent
        LEFT JOIN `tabHotel Customer` hc ON hc.name = r.customer
        WHERE rr.room IN %(rooms)s
          AND r.arrival_date < %(to_date)s
          AND r.departure_date > %(from_date)s
          AND r.status NOT IN ('Cancelled', 'No Show')
        ORDER BY r.arrival_date
    """, {"rooms": room_names, "from_date": from_date, "to_date": to_date}, as_dict=True)

    return {
        "rooms": rooms,
        "reservations": [dict(r) for r in reservations],
        "dates": dates,
        "from_date": from_date,
        "to_date": to_date
    }


@frappe.whitelist()
def update_housekeeping_status(room, new_status, notes=None):
    """Update room housekeeping status and create a housekeeping log entry."""
    frappe.has_permission("Hotel Housekeeping", "create", throw=True)

    room_doc = frappe.get_doc("Hotel Room", room)
    old_status = room_doc.housekeeping_status

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
        current_room_status = frappe.db.get_value("Hotel Room", room, "status")
        if current_room_status == "Cleaning":
            frappe.db.set_value("Hotel Room", room, "status", "Available")

    return {"success": True, "hk_record": hk.name}
