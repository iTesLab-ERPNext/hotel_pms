"""
hotel_pms.demo.hotel
~~~~~~~~~~~~~~~~~~~~~
Demo / test data for Hotel PMS.
NEVER auto-loaded — only called by 'bench hotel-demo seed' or from the
Test Data page in the workspace.

All inserts are wrapped in existence checks so the function is safe to
call multiple times (idempotent).
"""
import frappe
from frappe.utils import add_days, nowdate


# ── Demo fixtures ──────────────────────────────────────────────────────────────

DEMO_ROOMS = [
    {"room_number": "101", "room_name": "Standard Single",  "room_type": "Single",  "floor": "1", "capacity": 1, "rate": 80},
    {"room_number": "102", "room_name": "Standard Double",  "room_type": "Double",  "floor": "1", "capacity": 2, "rate": 120},
    {"room_number": "103", "room_name": "Twin Room",        "room_type": "Twin",    "floor": "1", "capacity": 2, "rate": 115},
    {"room_number": "201", "room_name": "Family Suite",     "room_type": "Family",  "floor": "2", "capacity": 4, "rate": 200},
    {"room_number": "202", "room_name": "Deluxe Double",    "room_type": "Deluxe",  "floor": "2", "capacity": 2, "rate": 180},
    {"room_number": "301", "room_name": "Executive Suite",  "room_type": "Suite",   "floor": "3", "capacity": 2, "rate": 350},
    {"room_number": "302", "room_name": "Penthouse Villa",  "room_type": "Villa",   "floor": "3", "capacity": 4, "rate": 600},
]

DEMO_CUSTOMERS = [
    {"full_name": "Ahmed Al-Mansouri", "nationality": "AE", "customer_category": "VIP"},
    {"full_name": "Sophie Martin",     "nationality": "FR", "customer_category": "Individual"},
    {"full_name": "James Wilson",      "nationality": "GB", "customer_category": "Corporate"},
    {"full_name": "Fatima Hassan",     "nationality": "EG", "customer_category": "Family"},
    {"full_name": "Carlos Rivera",     "nationality": "ES", "customer_category": "Individual"},
]


# ── Public API ─────────────────────────────────────────────────────────────────

def seed_demo_data() -> dict:
    """Insert demo rooms, customers, and a pair of reservations.
    Returns a summary dict of created records.
    """
    rooms     = _seed_rooms()
    customers = _seed_customers()
    res       = _seed_reservations(customers, rooms)
    frappe.db.commit()
    return {
        "rooms":        len(rooms),
        "customers":    len(customers),
        "reservations": len(res),
    }


def remove_demo_data() -> None:
    """Delete all records created by seed_demo_data."""
    # Reservations first (child tables cascade)
    for name in frappe.get_all("Hotel Reservation", pluck="name"):
        frappe.delete_doc("Hotel Reservation", name, ignore_permissions=True, force=True)
    for name in frappe.get_all("Hotel Stay", pluck="name"):
        frappe.delete_doc("Hotel Stay", name, ignore_permissions=True, force=True)
    for name in frappe.get_all("Hotel Folio", pluck="name"):
        frappe.delete_doc("Hotel Folio", name, ignore_permissions=True, force=True)
    for name in frappe.get_all("Hotel Payment", pluck="name"):
        frappe.delete_doc("Hotel Payment", name, ignore_permissions=True, force=True)
    for name in frappe.get_all("Hotel Room Movement", pluck="name"):
        frappe.delete_doc("Hotel Room Movement", name, ignore_permissions=True, force=True)
    for name in frappe.get_all("Hotel Housekeeping", pluck="name"):
        frappe.delete_doc("Hotel Housekeeping", name, ignore_permissions=True, force=True)
    for name in frappe.get_all("Hotel Customer", pluck="name"):
        frappe.delete_doc("Hotel Customer", name, ignore_permissions=True, force=True)
    for name in frappe.get_all("Hotel Room", pluck="name"):
        frappe.delete_doc("Hotel Room", name, ignore_permissions=True, force=True)
    frappe.db.commit()


# ── Internal helpers ───────────────────────────────────────────────────────────

def _seed_rooms() -> list:
    created = []
    for r in DEMO_ROOMS:
        existing = frappe.db.get_value("Hotel Room", {"room_number": r["room_number"]}, "name")
        if not existing:
            doc = frappe.get_doc({
                "doctype": "Hotel Room",
                "room_number": r["room_number"],
                "room_name":   r["room_name"],
                "room_type":   r["room_type"],
                "floor":       r["floor"],
                "capacity":    r["capacity"],
                "rate":        r["rate"],
                "status":      "Available",
                "active":      1,
            })
            doc.insert(ignore_permissions=True)
            created.append(doc.name)
        else:
            created.append(existing)
    return created


def _seed_customers() -> list:
    created = []
    for c in DEMO_CUSTOMERS:
        existing = frappe.db.get_value(
            "Hotel Customer", {"full_name": c["full_name"]}, "name")
        if not existing:
            doc = frappe.get_doc({
                "doctype": "Hotel Customer",
                "full_name":          c["full_name"],
                "nationality":        c.get("nationality"),
                "customer_category":  c.get("customer_category", "Individual"),
            })
            doc.insert(ignore_permissions=True)
            created.append(doc.name)
        else:
            created.append(existing)
    return created


def _seed_reservations(customers: list, rooms: list) -> list:
    created = []
    today = nowdate()

    # 1. A confirmed upcoming reservation (tomorrow → +3 nights)
    if len(customers) >= 1 and len(rooms) >= 2:
        arrival   = add_days(today, 1)
        departure = add_days(today, 4)
        res = frappe.get_doc({
            "doctype":        "Hotel Reservation",
            "customer":       customers[0],
            "booking_date":   today,
            "arrival_date":   arrival,
            "departure_date": departure,
            "status":         "Confirmed",
            "rooms": [
                {"room": rooms[0], "rate": 80,  "nights": 3},
                {"room": rooms[1], "rate": 120, "nights": 3},
            ],
            "families": [
                {"adults": 2, "children": 0, "infants": 0,
                 "family_type": "Couple"},
            ],
        })
        res.insert(ignore_permissions=True)
        created.append(res.name)

    # 2. A reservation that checked in today
    if len(customers) >= 2 and len(rooms) >= 4:
        departure = add_days(today, 2)
        res2 = frappe.get_doc({
            "doctype":        "Hotel Reservation",
            "customer":       customers[1],
            "booking_date":   add_days(today, -5),
            "arrival_date":   today,
            "departure_date": departure,
            "status":         "Confirmed",
            "rooms": [
                {"room": rooms[3], "rate": 200, "nights": 2},
            ],
            "families": [
                {"adults": 2, "children": 2, "infants": 0,
                 "family_type": "Family"},
            ],
        })
        res2.insert(ignore_permissions=True)
        created.append(res2.name)

    frappe.db.commit()
    return created
