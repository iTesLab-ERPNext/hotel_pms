import frappe
from frappe.utils import getdate, add_days, nowdate
from datetime import timedelta


def execute(filters=None):
    filters = filters or {}
    from_date = getdate(filters.get("from_date") or add_days(nowdate(), -30))
    to_date = getdate(filters.get("to_date") or nowdate())

    columns = get_columns()
    data = get_data(from_date, to_date)
    return columns, data


def get_columns():
    return [
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
        {"label": "Total Rooms", "fieldname": "total_rooms", "fieldtype": "Int", "width": 110},
        {"label": "Occupied", "fieldname": "occupied", "fieldtype": "Int", "width": 100},
        {"label": "Reserved", "fieldname": "reserved", "fieldtype": "Int", "width": 100},
        {"label": "Available", "fieldname": "available", "fieldtype": "Int", "width": 100},
        {"label": "Maintenance", "fieldname": "maintenance", "fieldtype": "Int", "width": 110},
        {"label": "Occupancy %", "fieldname": "occupancy_pct", "fieldtype": "Percent", "width": 120},
    ]


def get_data(from_date, to_date):
    total_rooms = frappe.db.count("Hotel Room", {"active": 1})
    if not total_rooms:
        return []

    data = []
    current = from_date
    while current <= to_date:
        date_str = str(current)

        occupied = frappe.db.sql("""
            SELECT COUNT(DISTINCT s.room) FROM `tabHotel Stay` s
            WHERE s.status = 'Active'
              AND DATE(s.checkin_date) <= %s
              AND (s.expected_checkout > %s OR s.expected_checkout IS NULL)
        """, (date_str, date_str))[0][0] or 0

        reserved = frappe.db.sql("""
            SELECT COUNT(DISTINCT rr.room)
            FROM `tabHotel Reservation Room` rr
            JOIN `tabHotel Reservation` r ON r.name = rr.parent
            WHERE r.status = 'Confirmed'
              AND r.arrival_date <= %s
              AND r.departure_date > %s
        """, (date_str, date_str))[0][0] or 0

        maintenance = frappe.db.count("Hotel Room", {"status": ["in", ["Maintenance", "Blocked", "Out of Service"]]})

        available = max(0, total_rooms - occupied - reserved - maintenance)
        occupancy_pct = round((occupied / total_rooms) * 100, 1) if total_rooms else 0

        data.append({
            "date": current,
            "total_rooms": total_rooms,
            "occupied": occupied,
            "reserved": reserved,
            "available": available,
            "maintenance": maintenance,
            "occupancy_pct": occupancy_pct,
        })

        current += timedelta(days=1)

    return data
