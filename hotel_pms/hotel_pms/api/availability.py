import frappe
from frappe.utils import getdate


def check_room_conflict(room, arrival_date, departure_date, exclude_reservation=None):
    """Return True if room is already booked for the given dates."""
    conditions = ""
    if exclude_reservation:
        conditions = f"AND r.name != {frappe.db.escape(exclude_reservation)}"

    result = frappe.db.sql(
        f"""
        SELECT COUNT(*) as cnt
        FROM `tabHotel Reservation Room` rr
        JOIN `tabHotel Reservation` r ON rr.parent = r.name
        WHERE rr.room = %s
          AND r.status NOT IN ('Cancelled', 'No Show')
          AND r.arrival_date < %s
          AND r.departure_date > %s
          {conditions}
        """,
        (room, getdate(departure_date), getdate(arrival_date)),
        as_dict=True,
    )
    return result[0].cnt > 0


@frappe.whitelist()
def get_available_rooms(arrival_date, departure_date, room_type=None):
    """Return list of available rooms for the given date range."""
    occupied = frappe.db.sql(
        """
        SELECT DISTINCT rr.room
        FROM `tabHotel Reservation Room` rr
        JOIN `tabHotel Reservation` r ON rr.parent = r.name
        WHERE r.status NOT IN ('Cancelled', 'No Show')
          AND r.arrival_date < %s
          AND r.departure_date > %s
        """,
        (getdate(departure_date), getdate(arrival_date)),
        as_list=True,
    )
    occupied_rooms = [r[0] for r in occupied] if occupied else []

    rooms = frappe.get_all(
        "Hotel Room",
        filters={"status": "Available", "is_active": 1},
        fields=["name", "room_number", "room_type", "floor", "rate"],
    )

    if room_type:
        rooms = [r for r in rooms if r.room_type == room_type]

    available = [r for r in rooms if r.name not in occupied_rooms]
    return available


@frappe.whitelist()
def check_availability(arrival_date, departure_date, room_type=None):
    rooms = get_available_rooms(arrival_date, departure_date, room_type)
    return {"available": len(rooms) > 0, "rooms": rooms, "count": len(rooms)}
