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

    # Today's payments via Frappe ORM
    today_pmt_rows = frappe.get_all(
        "Hotel Payment",
        filters={"payment_date": today, "docstatus": ["!=", 2]},
        fields=["amount"],
    )
    today_payments = sum(float(p.amount or 0) for p in today_pmt_rows)

    # Outstanding balance across all open folios
    open_folio_rows = frappe.get_all(
        "Hotel Folio",
        filters={"status": ["not in", ["Closed"]], "balance": [">", 0]},
        fields=["balance"],
    )
    outstanding = sum(float(f.balance or 0) for f in open_folio_rows)

    open_folios = frappe.db.count(
        "Hotel Folio", {"status": ["in", ["Open", "Partially Paid"]]})

    month_start = str(frappe.utils.get_first_day(today))
    month_pmt_rows = frappe.get_all(
        "Hotel Payment",
        filters={
            "payment_date": ["between", [month_start, today]],
            "docstatus": ["!=", 2],
        },
        fields=["amount"],
    )
    month_payments = sum(float(p.amount or 0) for p in month_pmt_rows)

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
            "open_folios": open_folios,
            "month_payments": float(month_payments),
        },
    }


# ── Availability ───────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_room_board_data():
    """Return all rooms enriched with current stay/guest/balance for Room Board."""
    rooms = frappe.get_all(
        "Hotel Room",
        filters={"active": 1},
        fields=["name", "room_number", "room_name", "room_type", "floor",
                "capacity", "status", "housekeeping_status", "base_rate"],
        order_by="floor asc, room_number asc",
    )

    # Active stays using Frappe ORM
    active_stays = frappe.get_all(
        "Hotel Stay",
        filters={"status": "Active"},
        fields=["name", "room", "guest_name"],
    )
    stay_names = [s.name for s in active_stays]

    # Batch-fetch folio balances for all active stays at once
    folio_balance_map = {}
    if stay_names:
        folios = frappe.get_all(
            "Hotel Folio",
            filters={"stay": ["in", stay_names]},
            fields=["stay", "balance"],
        )
        folio_balance_map = {f.stay: float(f.balance or 0) for f in folios}

    stay_map = {
        s.room: frappe._dict(
            stay=s.name,
            guest_name=s.guest_name,
            balance=folio_balance_map.get(s.name, 0.0),
        )
        for s in active_stays
    }

    # Room type names
    type_names = {
        rt["name"]: rt["room_type"]
        for rt in frappe.get_all("Hotel Room Type", fields=["name", "room_type"])
    }

    result = []
    for r in rooms:
        stay_info = stay_map.get(r.name, frappe._dict())
        result.append({
            **r,
            "room_type_name": type_names.get(r.room_type, r.room_type),
            "stay":       stay_info.get("stay"),
            "guest_name": stay_info.get("guest_name"),
            "balance":    float(stay_info.get("balance") or 0),
        })
    return result


@frappe.whitelist()
def get_room_availability(arrival_date, departure_date, room_type=None):
    """Return rooms available for the given date range."""
    filters = {"active": 1}
    if room_type:
        filters["room_type"] = room_type

    all_rooms = frappe.get_all(
        "Hotel Room", filters=filters,
        fields=["name", "room_number", "room_name", "room_type", "floor", "capacity", "status"])

    # Reservations overlapping the date range (Frappe ORM + db.sql for complex overlap)
    overlapping_res = frappe.get_all(
        "Hotel Reservation",
        filters={
            "status": ["not in", ["Cancelled", "No Show", "Completed"]],
            "arrival_date": ["<", departure_date],
            "departure_date": [">", arrival_date],
        },
        fields=["name"],
    )
    busy_names = set()
    for res in overlapping_res:
        rooms_in_res = frappe.get_all(
            "Hotel Reservation Room",
            filters={"parent": res.name},
            fields=["room"],
        )
        busy_names.update(r.room for r in rooms_in_res if r.room)

    active_stays = frappe.get_all(
        "Hotel Stay", filters={"status": "Active"}, fields=["room"])
    busy_names.update(s.room for s in active_stays if s.room)

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


# ── Revenue trend ──────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_revenue_trend(days=14):
    """Return daily payment totals for the last N days (for the dashboard line chart)."""
    today = nowdate()
    labels, values = [], []
    for i in range(int(days) - 1, -1, -1):
        day = str(add_days(today, -i))
        # Use Frappe ORM to fetch all payments on this day
        day_payments = frappe.get_all(
            "Hotel Payment",
            filters={"payment_date": day, "docstatus": ["!=", 2]},
            fields=["amount"],
        )
        total = sum(float(p.amount or 0) for p in day_payments)
        labels.append(day)
        values.append(total)
    return {"labels": labels, "values": values}


@frappe.whitelist()
def get_occupancy_trend(days=14):
    """Return daily occupancy % for the last N days."""
    today = nowdate()
    total_rooms = frappe.db.count("Hotel Room", {"active": 1}) or 1
    labels, values = [], []
    for i in range(int(days) - 1, -1, -1):
        day = str(add_days(today, -i))
        # Stays whose checkin <= day and expected_checkout > day (i.e. active on that day)
        occupied = frappe.db.count(
            "Hotel Stay",
            {"checkin_date": ["<=", day], "expected_checkout": [">", day]},
        )
        labels.append(day)
        values.append(round((occupied or 0) / total_rooms * 100, 1))
    return {"labels": labels, "values": values}


@frappe.whitelist()
def get_revenue_by_type():
    """Return revenue grouped by charge_type for the current month."""
    month_start = str(frappe.utils.get_first_day(nowdate()))
    folio_items = frappe.get_all(
        "Hotel Folio Item",
        filters={"date": [">=", month_start]},
        fields=["charge_type", "amount"],
    )
    totals = {}
    for item in folio_items:
        ct = item.charge_type or "Other"
        totals[ct] = totals.get(ct, 0) + float(item.amount or 0)
    # Sort by value desc
    sorted_items = sorted(totals.items(), key=lambda x: -x[1])
    return {
        "labels": [k for k, _ in sorted_items],
        "values": [v for _, v in sorted_items],
    }
