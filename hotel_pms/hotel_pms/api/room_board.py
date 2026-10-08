import frappe
from frappe.utils import nowdate


@frappe.whitelist()
def get_room_board():
    """Return all rooms with current status and in-house guest info."""
    rooms = frappe.db.sql(
        """
        SELECT
            hr.name, hr.room_number, hr.floor, hr.status,
            hrt.room_type_name AS room_type_label,
            hs.name AS stay_name,
            hs.guest_name,
            hs.checkin_date,
            hs.expected_checkout
        FROM `tabHotel Room` hr
        LEFT JOIN `tabHotel Room Type` hrt ON hrt.name = hr.room_type
        LEFT JOIN `tabHotel Stay` hs
            ON hs.room = hr.name AND hs.status = 'Checked In'
        WHERE hr.is_active = 1
        ORDER BY hr.floor, hr.room_number
        """,
        as_dict=True,
    )

    # Group by floor
    floors = {}
    for room in rooms:
        fl = room.floor or "0"
        floors.setdefault(fl, []).append(room)

    return {"floors": floors, "rooms": rooms}


@frappe.whitelist()
def get_room_stats():
    """Return KPI counts for the room board header."""
    total = frappe.db.count("Hotel Room", {"is_active": 1})
    occupied = frappe.db.count("Hotel Room", {"status": "Occupied", "is_active": 1})
    available = frappe.db.count("Hotel Room", {"status": "Available", "is_active": 1})
    dirty = frappe.db.count("Hotel Room", {"status": "Dirty", "is_active": 1})
    maintenance = frappe.db.count("Hotel Room", {"status": "Maintenance", "is_active": 1})

    arrivals = frappe.db.count(
        "Hotel Reservation",
        {"arrival_date": nowdate(), "status": ["in", ["Confirmed", "Pending"]]},
    )
    departures = frappe.db.count(
        "Hotel Stay",
        {"expected_checkout": nowdate(), "status": "Checked In"},
    )

    occ_pct = round((occupied / total * 100), 1) if total else 0

    return {
        "total": total,
        "occupied": occupied,
        "available": available,
        "dirty": dirty,
        "maintenance": maintenance,
        "arrivals_today": arrivals,
        "departures_today": departures,
        "occupancy_pct": occ_pct,
    }
