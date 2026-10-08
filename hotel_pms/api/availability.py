import frappe
from frappe import _
from frappe.utils import getdate


def check_room_conflict(room, checkin, checkout, exclude_reservation=None):
    """
    Return True if the room is already booked for the given dates.
    Checks Hotel Reservation Room child table entries.
    """
    filters = [
        ["Hotel Reservation Room", "room", "=", room],
        ["Hotel Reservation", "reservation_status", "not in",
         ["Cancelled", "No Show", "Checked Out", "Completed"]],
        ["Hotel Reservation Room", "checkin", "<", checkout],
        ["Hotel Reservation Room", "checkout", ">", checkin],
    ]
    if exclude_reservation:
        filters.append(["Hotel Reservation", "name", "!=", exclude_reservation])

    conflicts = frappe.db.sql(
        """
        SELECT res.name
        FROM `tabHotel Reservation` res
        JOIN `tabHotel Reservation Room` rr ON rr.parent = res.name
        WHERE rr.room = %s
          AND res.reservation_status NOT IN ('Cancelled','No Show','Checked Out','Completed')
          AND rr.checkin < %s
          AND rr.checkout > %s
          {exclude}
        LIMIT 1
        """.format(exclude="AND res.name != %s" if exclude_reservation else ""),
        (room, checkout, checkin, exclude_reservation) if exclude_reservation else (room, checkout, checkin),
        as_dict=True,
    )
    return bool(conflicts)


@frappe.whitelist()
def get_available_rooms(checkin, checkout, room_type=None, adults=1, children=0):
    """Return list of available rooms for the given date range."""
    filters = {"active": 1, "status": ["in", ["Available", "Dirty", "Clean"]]}
    if room_type:
        filters["room_type"] = room_type

    all_rooms = frappe.get_all(
        "Hotel Room",
        filters=filters,
        fields=["name", "room_number", "room_type", "floor", "building", "status"],
    )

    available = []
    for room in all_rooms:
        if not check_room_conflict(room.name, checkin, checkout):
            available.append(room)

    return available


@frappe.whitelist()
def check_availability(room, checkin, checkout, exclude_reservation=None):
    """Whitelisted wrapper — returns True/False."""
    conflict = check_room_conflict(room, checkin, checkout, exclude_reservation)
    return not conflict
