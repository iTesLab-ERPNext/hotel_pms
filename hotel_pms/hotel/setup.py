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


def ensure_module_def() -> None:
    """Guarantee 'Hotel' Module Def exists before any Hotel DocType records are inserted.

    bench migrate normally creates Module Def entries from modules.txt, but on sites
    that already have other apps (e.g. ERPNext) the sync can happen after after_migrate
    fires.  Creating it here is idempotent and safe.
    """
    if not frappe.db.exists("Module Def", "Hotel"):
        _insert({
            "doctype": "Module Def",
            "module_name": "Hotel",
            "app_name": "hotel_pms",
        })
        frappe.db.commit()
        frappe.logger().info("Hotel PMS: created Module Def 'Hotel'")


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


def run() -> None:
    """Full setup — called from after_migrate."""
    ensure_module_def()
    ensure_roles()
    ensure_masters()
    frappe.db.commit()
