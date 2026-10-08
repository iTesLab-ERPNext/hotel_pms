import frappe
from frappe import _

@frappe.whitelist()
def get_available_rooms(arrival_date, departure_date, room_type=None):
    """Return list of available rooms for the given date range."""
    filters = {"status": "Available", "active": 1}
    if room_type:
        filters["room_type"] = room_type

    all_rooms = frappe.get_all("Hotel Room",
        filters=filters,
        fields=["name", "room_number", "room_type", "floor", "capacity", "status"])

    # Find rooms with conflicting reservations
    conflict_query = """
        SELECT DISTINCT r.room
        FROM `tabHotel Reservation Room` r
        JOIN `tabHotel Reservation` res ON res.name = r.parent
        WHERE res.status NOT IN ('Cancelled', 'Checked Out')
        AND res.arrival_date < %(departure)s
        AND res.departure_date > %(arrival)s
    """
    booked = frappe.db.sql(conflict_query, {
        "arrival": arrival_date,
        "departure": departure_date
    }, as_dict=True)
    booked_rooms = {b.room for b in booked}

    return [r for r in all_rooms if r.name not in booked_rooms]


@frappe.whitelist()
def get_room_calendar(from_date=None, to_date=None, room_type=None):
    """Return room calendar data."""
    if not from_date:
        from_date = frappe.utils.today()
    if not to_date:
        to_date = frappe.utils.add_days(from_date, 30)

    room_filters = {"active": 1}
    if room_type:
        room_filters["room_type"] = room_type

    rooms = frappe.get_all("Hotel Room",
        filters=room_filters,
        fields=["name", "room_number", "room_type", "status"],
        order_by="room_number asc")

    reservations = frappe.db.sql("""
        SELECT r.room, r.room_type, res.name as reservation,
               res.customer, res.arrival_date, res.departure_date, res.status
        FROM `tabHotel Reservation Room` r
        JOIN `tabHotel Reservation` res ON res.name = r.parent
        WHERE res.status NOT IN ('Cancelled')
        AND res.arrival_date <= %(to_date)s
        AND res.departure_date >= %(from_date)s
        ORDER BY res.arrival_date
    """, {"from_date": from_date, "to_date": to_date}, as_dict=True)

    return {"rooms": rooms, "reservations": reservations, "from_date": from_date, "to_date": to_date}
