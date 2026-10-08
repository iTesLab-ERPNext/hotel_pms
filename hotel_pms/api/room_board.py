import frappe
from frappe.utils import today, now_datetime


@frappe.whitelist()
def get_room_board():
    """
    Return real-time status of all rooms for the Room Board page.
    """
    rooms = frappe.db.sql(
        """
        SELECT
            r.name,
            r.room_number,
            rt.room_type_name,
            r.floor,
            r.building,
            r.status,
            r.housekeeping_status,
            r.current_guest,
            stay.name AS stay_name,
            stay.guest_name,
            stay.checkin_date,
            stay.expected_checkout,
            stay.number_of_nights,
            stay.balance_due
        FROM `tabHotel Room` r
        LEFT JOIN `tabHotel Room Type` rt ON rt.name = r.room_type
        LEFT JOIN `tabHotel Stay` stay
            ON stay.room = r.name AND stay.stay_status IN ('In House','Extended')
        WHERE r.active = 1
        ORDER BY r.floor, r.room_number
        """,
        as_dict=True,
    )

    # Color coding helper
    status_color = {
        "Available": "green",
        "Occupied": "blue",
        "Reserved": "orange",
        "Cleaning": "yellow",
        "Dirty": "grey",
        "Maintenance": "red",
        "Out of Service": "darkred",
        "Blocked": "purple",
    }

    for room in rooms:
        room["color"] = status_color.get(room["status"], "grey")
        room["checkin_date"] = str(room.get("checkin_date") or "")
        room["expected_checkout"] = str(room.get("expected_checkout") or "")

    return rooms


@frappe.whitelist()
def get_room_stats():
    """Return aggregate counts for dashboard KPIs."""
    today_date = today()
    rooms = frappe.db.sql(
        """
        SELECT status, COUNT(*) as cnt FROM `tabHotel Room`
        WHERE active = 1 GROUP BY status
        """,
        as_dict=True,
    )
    stats = {r.status: r.cnt for r in rooms}

    arrivals = frappe.db.count(
        "Hotel Reservation",
        {
            "arrival_date": ["like", f"{today_date}%"],
            "reservation_status": ["in", ["Confirmed", "Deposit Paid"]],
        },
    )
    departures = frappe.db.count(
        "Hotel Stay",
        {
            "expected_checkout": ["like", f"{today_date}%"],
            "stay_status": ["in", ["In House", "Extended"]],
        },
    )

    total = sum(stats.values())
    occupied = stats.get("Occupied", 0)
    occupancy_pct = round(occupied / total * 100, 1) if total else 0

    return {
        "room_stats": stats,
        "total_rooms": total,
        "occupied": occupied,
        "available": stats.get("Available", 0),
        "occupancy_pct": occupancy_pct,
        "arrivals_today": arrivals,
        "departures_today": departures,
    }
