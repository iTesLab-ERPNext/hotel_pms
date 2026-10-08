"""
hotel_pms.hotel.api
~~~~~~~~~~~~~~~~~~~~
Whitelisted HTTP endpoints consumed by Frappe pages and DocType JS files.
All heavy logic lives in hotel.lifecycle — this module is thin glue.
"""
import frappe
from frappe.utils import nowdate, add_days, getdate

from hotel_pms.hotel import lifecycle


# ── Dashboard ──────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_dashboard_data():
    """Return all key metrics for the Hotel PMS dashboard."""
    today = nowdate()

    rooms = frappe.get_all("Hotel Room", fields=["status", "housekeeping_status"])
    room_stats = {
        "total": len(rooms),
        "available": 0, "reserved": 0, "occupied": 0,
        "cleaning": 0, "maintenance": 0, "blocked": 0, "out_of_service": 0,
    }
    for r in rooms:
        key = (r.status or "").lower().replace(" ", "_")
        if key in room_stats:
            room_stats[key] += 1

    today_arrivals = frappe.db.count(
        "Hotel Reservation",
        {"arrival_date": today, "status": ["in", ["Confirmed", "Checked In"]]})
    today_departures = frappe.db.count(
        "Hotel Reservation", {"departure_date": today, "status": "Checked In"})
    active_stays = frappe.db.count("Hotel Stay", {"status": "Active"})

    res_stats = {}
    for status in ["Draft", "Confirmed", "Checked In", "Completed", "Cancelled", "No Show"]:
        res_stats[status.lower().replace(" ", "_")] = frappe.db.count(
            "Hotel Reservation", {"status": status})

    today_payments = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabHotel Payment`
        WHERE payment_date = %s AND docstatus != 2
    """, today)[0][0] or 0

    outstanding = frappe.db.sql("""
        SELECT COALESCE(SUM(balance), 0)
        FROM `tabHotel Folio`
        WHERE status != 'Closed' AND balance > 0
    """)[0][0] or 0

    return {
        "rooms": room_stats,
        "today": {
            "arrivals": today_arrivals,
            "departures": today_departures,
            "active_stays": active_stays,
            "available_rooms": room_stats["available"],
        },
        "reservations": res_stats,
        "financial": {
            "today_payments": float(today_payments),
            "outstanding_balances": float(outstanding),
        },
    }


# ── Availability ───────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_room_availability(arrival_date, departure_date, room_type=None):
    """Return rooms available for the given date range."""
    filters = {"active": 1}
    if room_type:
        filters["room_type"] = room_type

    all_rooms = frappe.get_all(
        "Hotel Room", filters=filters,
        fields=["name", "room_number", "room_name", "room_type", "floor", "capacity", "status"])

    busy_rooms = frappe.db.sql("""
        SELECT DISTINCT rr.room
        FROM `tabHotel Reservation Room` rr
        JOIN `tabHotel Reservation` r ON r.name = rr.parent
        WHERE r.status NOT IN ('Cancelled', 'No Show', 'Completed')
          AND r.arrival_date < %s
          AND r.departure_date > %s
    """, (departure_date, arrival_date), as_dict=True)
    busy_names = {b.room for b in busy_rooms}

    active_stays = frappe.db.sql(
        "SELECT DISTINCT room FROM `tabHotel Stay` WHERE status = 'Active'",
        as_dict=True)
    busy_names.update(s.room for s in active_stays)

    return [r for r in all_rooms if r.name not in busy_names]


# ── Room calendar ──────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_room_calendar(from_date=None, to_date=None, room=None, room_type=None):
    """Return reservation blocks for the calendar view."""
    if not from_date:
        from_date = nowdate()
    if not to_date:
        to_date = add_days(from_date, 30)

    filters = {"active": 1}
    if room:
        filters["name"] = room
    if room_type:
        filters["room_type"] = room_type

    rooms = frappe.get_all(
        "Hotel Room", filters=filters,
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


# ── Room planning board ────────────────────────────────────────────────────────

@frappe.whitelist()
def get_planning_board(from_date=None, days=14):
    """Return data for the room-planning Gantt board."""
    from datetime import timedelta

    if not from_date:
        from_date = nowdate()

    days = int(days)
    to_date = add_days(from_date, days)

    rooms = frappe.get_all(
        "Hotel Room", filters={"active": 1},
        fields=["name", "room_number", "room_name", "room_type", "floor", "status"],
        order_by="room_number")
    if not rooms:
        return {"rooms": [], "reservations": [], "dates": []}

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
        "to_date": to_date,
    }


# ── Folio details ──────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_folio_details(reservation=None, stay=None):
    """Return folio document + payment history for a reservation or stay."""
    filters = {}
    if reservation:
        filters["reservation"] = reservation
    if stay:
        filters["stay"] = stay

    folio_name = frappe.db.get_value("Hotel Folio", filters, "name")
    if not folio_name:
        return None

    folio_doc = frappe.get_doc("Hotel Folio", folio_name)
    payments = frappe.get_all(
        "Hotel Payment", filters={"folio": folio_name},
        fields=["name", "payment_date", "payment_type", "payment_method",
                "amount", "reference"])
    return {"folio": folio_doc.as_dict(), "payments": payments}


# ── Actions (thin wrappers so JS only needs one import path) ──────────────────

@frappe.whitelist()
def check_in(reservation):
    return lifecycle.check_in(reservation)


@frappe.whitelist()
def check_out(stay_name):
    return lifecycle.check_out(stay_name)


@frappe.whitelist()
def move_room(stay_name, new_room, reason=None, new_rate=None):
    return lifecycle.move_room(stay_name, new_room, reason, new_rate)


@frappe.whitelist()
def add_folio_charge(folio, charge_type, description, quantity, rate,
                     date=None, service=None, room=None):
    return lifecycle.add_folio_charge(
        folio, charge_type, description, quantity, rate, date, service, room)


@frappe.whitelist()
def create_payment(customer, amount, payment_method, payment_type="Partial",
                   reservation=None, stay=None, folio=None,
                   reference=None, notes=None):
    return lifecycle.create_payment(
        customer, amount, payment_method, payment_type,
        reservation, stay, folio, reference, notes)


@frappe.whitelist()
def update_housekeeping_status(room, new_status, notes=None):
    return lifecycle.update_housekeeping_status(room, new_status, notes)
