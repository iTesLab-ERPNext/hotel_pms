"""
hotel_pms.hotel.setup
~~~~~~~~~~~~~~~~~~~~~
All idempotent setup logic for Hotel PMS.
Called from hotel_pms.setup.install — never import frappe at module level here
so this file can be imported for tests without a Frappe context.
"""
import frappe

# ── Seed data constants ────────────────────────────────────────────────────────

ROLES = ["Hotel Manager", "Front Desk", "Housekeeping", "Cashier"]

ROLE_PROFILES = {
    "Hotel Manager": ROLES,
    "Front Desk": ["Front Desk"],
    "Housekeeping": ["Housekeeping"],
    "Cashier": ["Cashier"],
}

CUSTOMER_CATEGORIES = ["Individual", "Family", "Corporate", "VIP", "Agency", "Group"]

FAMILY_TYPES = ["Single", "Couple", "Family", "Large Family", "Group"]

ROOM_TYPES = [
    {"room_type": "Single",      "code": "SIN"},
    {"room_type": "Double",      "code": "DBL"},
    {"room_type": "Twin",        "code": "TWN"},
    {"room_type": "Triple",      "code": "TRI"},
    {"room_type": "Family",      "code": "FAM"},
    {"room_type": "Suite",       "code": "SUI"},
    {"room_type": "Deluxe",      "code": "DEL"},
    {"room_type": "Villa",       "code": "VIL"},
]

SERVICES = [
    {"service_name": "Breakfast",     "code": "BRK"},
    {"service_name": "Lunch",         "code": "LCH"},
    {"service_name": "Dinner",        "code": "DIN"},
    {"service_name": "Restaurant",    "code": "RES"},
    {"service_name": "Spa",           "code": "SPA"},
    {"service_name": "Horse Riding",  "code": "HRS"},
    {"service_name": "Transport",     "code": "TRN"},
    {"service_name": "Laundry",       "code": "LND"},
    {"service_name": "Extra Bed",     "code": "EBD"},
    {"service_name": "Other",         "code": "OTH"},
]

# Demo rooms: (room_number, room_name, room_type, floor, capacity, base_rate, status)
DEMO_ROOMS = [
    ("101", "Standard Single 101",  "Single",  1, 1,  800,  "Available"),
    ("102", "Standard Single 102",  "Single",  1, 1,  800,  "Available"),
    ("103", "Double Room 103",      "Double",  1, 2,  1200, "Available"),
    ("104", "Twin Room 104",        "Twin",    1, 2,  1200, "Available"),
    ("105", "Double Room 105",      "Double",  1, 2,  1200, "Available"),
    ("201", "Family Suite 201",     "Family",  2, 4,  2000, "Available"),
    ("202", "Deluxe Double 202",    "Deluxe",  2, 2,  1800, "Available"),
    ("203", "Deluxe Double 203",    "Deluxe",  2, 2,  1800, "Available"),
    ("204", "Triple Room 204",      "Triple",  2, 3,  1600, "Available"),
    ("301", "Junior Suite 301",     "Suite",   3, 2,  3000, "Available"),
    ("302", "Senior Suite 302",     "Suite",   3, 3,  4000, "Available"),
    ("401", "Presidential Villa",   "Villa",   4, 4,  8000, "Available"),
]

# Demo customers: (full_name, email, phone, nationality, customer_category)
DEMO_CUSTOMERS = [
    ("Ahmed Ben Ali",       "ahmed.benali@email.com",   "+216 20 000 001", "Tunisian",  "Individual"),
    ("Marie Dupont",        "marie.dupont@email.com",   "+33 6 00 00 00 01","French",   "Individual"),
    ("John Smith",          "john.smith@email.com",     "+44 7700 000001",  "British",  "Individual"),
    ("Fatima Al-Hassan",    "fatima.hassan@email.com",  "+966 50 000 0001", "Saudi",    "VIP"),
    ("Carlos Rodriguez",    "carlos.rodriguez@corp.com","+34 600 000 001",  "Spanish",  "Corporate"),
    ("Global Travel Agency","gta@globaltravel.com",     "+1 212 000 0001",  "American", "Agency"),
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def _insert(data: dict) -> None:
    """Insert a document unconditionally — caller must guard with db.exists."""
    frappe.get_doc(data).insert(ignore_permissions=True)


# ── Public entry points ────────────────────────────────────────────────────────

def ensure_roles() -> None:
    for role in ROLES:
        if not frappe.db.exists("Role", role):
            _insert({"doctype": "Role", "role_name": role})
            frappe.logger().info(f"Hotel PMS: created role {role!r}")


def ensure_masters() -> None:
    """Seed lookup tables — idempotent."""
    for cat in CUSTOMER_CATEGORIES:
        if not frappe.db.exists("Hotel Customer Category", cat):
            _insert({"doctype": "Hotel Customer Category",
                     "customer_category": cat, "active": 1})

    for ft in FAMILY_TYPES:
        if not frappe.db.exists("Hotel Family Type", ft):
            _insert({"doctype": "Hotel Family Type",
                     "family_type": ft, "active": 1})

    for rt in ROOM_TYPES:
        if not frappe.db.exists("Hotel Room Type", rt["room_type"]):
            _insert({"doctype": "Hotel Room Type",
                     "room_type": rt["room_type"],
                     "code": rt["code"],
                     "active": 1})

    for svc in SERVICES:
        if not frappe.db.exists("Hotel Service", svc["service_name"]):
            _insert({"doctype": "Hotel Service",
                     "service_name": svc["service_name"],
                     "code": svc["code"],
                     "active": 1})


def before_uninstall() -> None:
    """Remove seed data created by this app."""
    for cat in CUSTOMER_CATEGORIES:
        if frappe.db.exists("Hotel Customer Category", cat):
            frappe.delete_doc("Hotel Customer Category", cat, ignore_permissions=True)

    for ft in FAMILY_TYPES:
        if frappe.db.exists("Hotel Family Type", ft):
            frappe.delete_doc("Hotel Family Type", ft, ignore_permissions=True)

    for rt in ROOM_TYPES:
        name = rt["room_type"]
        if frappe.db.exists("Hotel Room Type", name):
            frappe.delete_doc("Hotel Room Type", name, ignore_permissions=True)

    for svc in SERVICES:
        name = svc["service_name"]
        if frappe.db.exists("Hotel Service", name):
            frappe.delete_doc("Hotel Service", name, ignore_permissions=True)

    # Roles are shared system records linked to DocType permissions;
    # Frappe blocks deletion while those links exist. Disable instead.
    for role in ROLES:
        if frappe.db.exists("Role", role):
            try:
                frappe.db.set_value("Role", role, "disabled", 1)
            except Exception:
                pass

    frappe.db.commit()


def ensure_demo_rooms() -> None:
    """Seed demo Hotel Room records — skipped if any room already exists."""
    if frappe.db.count("Hotel Room") > 0:
        return  # Don't overwrite if operator has added their own rooms

    for (num, name, rtype, floor, cap, rate, status) in DEMO_ROOMS:
        if not frappe.db.exists("Hotel Room", {"room_number": num}):
            _insert({
                "doctype": "Hotel Room",
                "room_number": num,
                "room_name": name,
                "room_type": rtype,
                "floor": floor,
                "capacity": cap,
                "base_rate": rate,
                "status": status,
                "housekeeping_status": "Clean",
                "active": 1,
            })
    frappe.logger().info("Hotel PMS: demo rooms created")


def ensure_demo_customers() -> None:
    """Seed demo Hotel Customer records — skipped if any customer already exists."""
    if frappe.db.count("Hotel Customer") > 0:
        return

    for (name, email, phone, nationality, category) in DEMO_CUSTOMERS:
        if not frappe.db.exists("Hotel Customer", {"email": email}):
            _insert({
                "doctype": "Hotel Customer",
                "full_name": name,
                "email": email,
                "mobile": phone,
                "nationality": nationality,
                "customer_category": category,
                "active": 1,
            })
    frappe.logger().info("Hotel PMS: demo customers created")


def run() -> None:
    """Full setup — called from after_migrate."""
    ensure_roles()
    ensure_masters()
    ensure_demo_rooms()
    ensure_demo_customers()
    frappe.db.commit()
