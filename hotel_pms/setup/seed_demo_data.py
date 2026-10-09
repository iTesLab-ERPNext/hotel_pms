"""
Demo / test data seeder for Hotel PMS.

All records created here are marked with is_test_data = 1 and can be
removed safely by calling delete_test_data().
"""

import frappe
from frappe.utils import nowdate, add_days, now_datetime


# ─── Public entry points ──────────────────────────────────────────────────────

@frappe.whitelist()
def seed():
    """Create all test data. Safe to call multiple times (idempotent)."""
    log = []
    errors = []

    def ok(msg):
        print(msg)
        log.append(msg)

    def run(fn):
        try:
            fn(ok)
        except Exception as e:
            msg = f"ERROR in {fn.__name__}: {e}"
            print(msg)
            log.append(msg)
            errors.append(msg)
            frappe.db.rollback()

    run(create_test_room_types)
    run(create_test_rooms)
    run(create_test_services)
    run(create_test_packages)
    run(create_test_customers)
    run(create_test_reservations)
    run(create_test_stays)
    run(create_test_folios)
    run(create_test_payments)
    run(create_test_housekeeping)

    frappe.db.commit()
    ok("=== Test data seeding complete ===")
    return {"log": log, "errors": errors}


@frappe.whitelist()
def delete_test_data():
    """Delete all records where is_test_data = 1, in safe dependency order."""
    log = []

    def ok(msg):
        print(msg)
        log.append(msg)

    # 1. Housekeeping
    _delete_dt("Hotel Housekeeping", ok)

    # 2. Payments
    _delete_dt("Hotel Payment", ok)

    # 3. Folio items (via folio parent)
    folios = frappe.get_all("Hotel Folio", filters={"is_test_data": 1}, pluck="name")
    for f in folios:
        frappe.db.delete("Hotel Folio Item", {"parent": f})
    ok(f"  Deleted folio items for {len(folios)} folios")

    # 4. Folios
    _delete_dt("Hotel Folio", ok)

    # 5. Room movements
    _delete_dt("Hotel Room Movement", ok)

    # 6. Stays
    _delete_dt("Hotel Stay", ok)

    # 7. Reservation child tables
    reservations = frappe.get_all("Hotel Reservation", filters={"is_test_data": 1}, pluck="name")
    for r in reservations:
        frappe.db.delete("Hotel Reservation Room", {"parent": r})
        frappe.db.delete("Hotel Reservation Family", {"parent": r})
        frappe.db.delete("Hotel Reservation Guest", {"parent": r})
    ok(f"  Deleted reservation children for {len(reservations)} reservations")

    # 8. Reservations
    _delete_dt("Hotel Reservation", ok)

    # 9. Package items
    packages = frappe.get_all("Hotel Package", filters={"is_test_data": 1}, pluck="name")
    for p in packages:
        frappe.db.delete("Hotel Package Item", {"parent": p})
    ok(f"  Deleted package items for {len(packages)} packages")

    # 10. Packages
    _delete_dt("Hotel Package", ok)

    # 11. Services
    _delete_dt("Hotel Service", ok)

    # 12. Rooms
    _delete_dt("Hotel Room", ok)

    # 13. Room types
    _delete_dt("Hotel Room Type", ok)

    # 14. Customers
    _delete_dt("Hotel Customer", ok)

    frappe.db.commit()
    ok("=== Test data deletion complete ===")
    return {"log": log}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _delete_dt(doctype, ok):
    records = frappe.get_all(doctype, filters={"is_test_data": 1}, pluck="name")
    for name in records:
        try:
            frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
        except Exception:
            frappe.db.delete(doctype, {"name": name})
    ok(f"  Deleted {len(records)} {doctype} records")


def _exists(doctype, name):
    return frappe.db.exists(doctype, name)


def _insert(doc_dict):
    doc = frappe.get_doc(doc_dict)
    doc.insert(ignore_permissions=True)
    return doc


# ─── Room Types ───────────────────────────────────────────────────────────────

def create_test_room_types(ok):
    room_types = [
        {"room_type": "Standard Room", "code": "STD", "capacity_adults": 2, "capacity_children": 1, "maximum_occupancy": 3, "base_price": 800},
        {"room_type": "Deluxe Room", "code": "DLX", "capacity_adults": 2, "capacity_children": 2, "maximum_occupancy": 4, "base_price": 1200},
        {"room_type": "Suite", "code": "STE", "capacity_adults": 2, "capacity_children": 2, "maximum_occupancy": 4, "base_price": 2000},
        {"room_type": "Family Room", "code": "FAM", "capacity_adults": 2, "capacity_children": 3, "maximum_occupancy": 5, "base_price": 1600},
    ]
    created = 0
    for rt in room_types:
        if not _exists("Hotel Room Type", rt["room_type"]):
            _insert({"doctype": "Hotel Room Type", **rt, "active": 1, "is_test_data": 1})
            created += 1
    ok(f"  Room Types: {created} created (of {len(room_types)})")


# ─── Rooms ────────────────────────────────────────────────────────────────────

def create_test_rooms(ok):
    rooms_data = []
    # Floor 1: Standard rooms 101-105
    for i in range(1, 6):
        rooms_data.append({"room_number": f"10{i}", "room_type": "Standard Room", "floor": "1", "capacity": 2, "status": "Available"})
    # Floor 2: Deluxe rooms 201-205
    for i in range(1, 6):
        rooms_data.append({"room_number": f"20{i}", "room_type": "Deluxe Room", "floor": "2", "capacity": 3, "status": "Available"})
    # Floor 3: Suites 301-305
    for i in range(1, 4):
        rooms_data.append({"room_number": f"30{i}", "room_type": "Suite", "floor": "3", "capacity": 4, "status": "Available"})
    # Floor 4: Family rooms 401-405
    for i in range(1, 7):
        rooms_data.append({"room_number": f"40{i}", "room_type": "Family Room", "floor": "4", "capacity": 5, "status": "Available"})

    created = 0
    for r in rooms_data:
        if not _exists("Hotel Room", r["room_number"]):
            _insert({
                "doctype": "Hotel Room",
                **r,
                "room_name": f"Room {r['room_number']}",
                "housekeeping_status": "Clean",
                "active": 1,
                "is_test_data": 1,
            })
            created += 1
    ok(f"  Rooms: {created} created (of {len(rooms_data)})")


# ─── Services ─────────────────────────────────────────────────────────────────

def create_test_services(ok):
    services = [
        {"service_name": "Breakfast", "code": "BRK", "category": "Food & Beverage", "rate": 120},
        {"service_name": "Half Board", "code": "HB", "category": "Food & Beverage", "rate": 250},
        {"service_name": "Full Board", "code": "FB", "category": "Food & Beverage", "rate": 400},
        {"service_name": "All Inclusive", "code": "AI", "category": "Food & Beverage", "rate": 600},
        {"service_name": "Airport Transfer", "code": "TRNS", "category": "Transport", "rate": 200},
        {"service_name": "Spa Treatment", "code": "SPA", "category": "Wellness", "rate": 350},
        {"service_name": "Laundry Service", "code": "LDY", "category": "Housekeeping", "rate": 80},
        {"service_name": "Horse Riding", "code": "HRS", "category": "Activity", "rate": 300},
        {"service_name": "Extra Bed", "code": "EBD", "category": "Room", "rate": 150},
        {"service_name": "Mini Bar", "code": "MNB", "category": "Food & Beverage", "rate": 50},
    ]
    created = 0
    for s in services:
        if not _exists("Hotel Service", s["service_name"]):
            _insert({"doctype": "Hotel Service", **s, "active": 1, "is_test_data": 1})
            created += 1
    ok(f"  Services: {created} created (of {len(services)})")


# ─── Packages ─────────────────────────────────────────────────────────────────

def create_test_packages(ok):
    pkgs = [
        {
            "package_name": "Bed and Breakfast",
            "code": "BB",
            "description": "Room + daily breakfast",
            "items": [{"service": "Breakfast", "quantity": 1, "rate": 120}],
        },
        {
            "package_name": "Half Board Package",
            "code": "HBP",
            "description": "Room + breakfast + dinner",
            "items": [{"service": "Half Board", "quantity": 1, "rate": 250}],
        },
        {
            "package_name": "Full Board Package",
            "code": "FBP",
            "description": "Room + all meals",
            "items": [{"service": "Full Board", "quantity": 1, "rate": 400}],
        },
        {
            "package_name": "All Inclusive Package",
            "code": "AIP",
            "description": "Room + all meals + activities",
            "items": [
                {"service": "All Inclusive", "quantity": 1, "rate": 600},
                {"service": "Horse Riding", "quantity": 1, "rate": 300},
            ],
        },
        {
            "package_name": "Honeymoon Package",
            "code": "HON",
            "description": "Suite + breakfast + spa",
            "items": [
                {"service": "Breakfast", "quantity": 2, "rate": 120},
                {"service": "Spa Treatment", "quantity": 1, "rate": 350},
            ],
        },
        {
            "package_name": "Family Fun Package",
            "code": "FFP",
            "description": "Family room + activities",
            "items": [
                {"service": "Breakfast", "quantity": 1, "rate": 120},
                {"service": "Horse Riding", "quantity": 2, "rate": 300},
            ],
        },
    ]
    created = 0
    for p in pkgs:
        if not _exists("Hotel Package", p["package_name"]):
            items = p.pop("items", [])
            doc = frappe.get_doc({
                "doctype": "Hotel Package",
                **p,
                "active": 1,
                "is_test_data": 1,
            })
            for item in items:
                item["amount"] = item["quantity"] * item["rate"]
                doc.append("items", item)
            doc.insert(ignore_permissions=True)
            created += 1
    ok(f"  Packages: {created} created (of {len(pkgs)})")


# ─── Customers ────────────────────────────────────────────────────────────────

def create_test_customers(ok):
    customers = [
        {"first_name": "Ahmed", "last_name": "Benali", "phone": "+213-555-0001", "email": "ahmed.benali@email.com", "nationality": "Algerian", "customer_category": "Individual"},
        {"first_name": "Fatima", "last_name": "Cherif", "phone": "+213-555-0002", "email": "fatima.cherif@email.com", "nationality": "Algerian", "customer_category": "Family"},
        {"first_name": "Mohammed", "last_name": "Saidi", "phone": "+213-555-0003", "email": "m.saidi@corp.com", "nationality": "Algerian", "customer_category": "Corporate"},
        {"first_name": "Sarah", "last_name": "Johnson", "phone": "+1-555-0004", "email": "sarah.j@email.com", "nationality": "American", "customer_category": "VIP"},
        {"first_name": "Pierre", "last_name": "Dupont", "phone": "+33-555-0005", "email": "p.dupont@email.fr", "nationality": "French", "customer_category": "Individual"},
        {"first_name": "Amina", "last_name": "Boudiaf", "phone": "+213-555-0006", "email": "amina.b@email.com", "nationality": "Algerian", "customer_category": "Family"},
        {"first_name": "Carlos", "last_name": "Martinez", "phone": "+34-555-0007", "email": "c.martinez@email.es", "nationality": "Spanish", "customer_category": "Individual"},
        {"first_name": "Nadia", "last_name": "Rahmani", "phone": "+213-555-0008", "email": "n.rahmani@email.com", "nationality": "Algerian", "customer_category": "VIP"},
        {"first_name": "John", "last_name": "Smith", "phone": "+44-555-0009", "email": "j.smith@email.co.uk", "nationality": "British", "customer_category": "Corporate"},
        {"first_name": "Khadija", "last_name": "Messaoud", "phone": "+213-555-0010", "email": "k.messaoud@email.com", "nationality": "Algerian", "customer_category": "Family"},
        {"first_name": "Liu", "last_name": "Wei", "phone": "+86-555-0011", "email": "liu.wei@email.cn", "nationality": "Chinese", "customer_category": "Group"},
        {"first_name": "Hassan", "last_name": "Otmani", "phone": "+212-555-0012", "email": "h.otmani@email.ma", "nationality": "Moroccan", "customer_category": "Individual"},
        {"first_name": "Marie", "last_name": "Bernard", "phone": "+33-555-0013", "email": "m.bernard@email.fr", "nationality": "French", "customer_category": "Individual"},
        {"first_name": "Omar", "last_name": "Belkacem", "phone": "+213-555-0014", "email": "o.belkacem@agency.dz", "nationality": "Algerian", "customer_category": "Agency"},
        {"first_name": "Yasmine", "last_name": "Hamdi", "phone": "+216-555-0015", "email": "y.hamdi@email.tn", "nationality": "Tunisian", "customer_category": "Family"},
    ]
    created = 0
    for c in customers:
        # Check by email to avoid duplicates
        existing = frappe.db.get_value("Hotel Customer", {"email": c["email"]}, "name")
        if not existing:
            _insert({"doctype": "Hotel Customer", **c, "active": 1, "is_test_data": 1})
            created += 1
    ok(f"  Customers: {created} created (of {len(customers)})")


# ─── Reservations ─────────────────────────────────────────────────────────────

def _get_customer_by_email(email):
    return frappe.db.get_value("Hotel Customer", {"email": email}, "name")


def create_test_reservations(ok):
    """
    ~40 scenarios spread across 3 months:
      - Past (-30 to -5 days)  : Completed stays with closed folios
      - Current (-2 to +4 days): Checked-In stays with open/partial folios
      - Near future (+1 to +20): Confirmed bookings
      - Far future (+30 to +60): Confirmed bookings for month 2-3
      - Special: No Show, Cancelled, Draft

    Rooms are assigned so no two reservations overlap on the same room.
    """
    today = nowdate()
    d = lambda n: add_days(today, n)   # shorthand

    scenarios = [
        # ── CURRENTLY ACTIVE (Checked In) ──────────────────────────────────
        {
            "id": "A1",
            "customer_email": "ahmed.benali@email.com",
            "arrival": d(-1), "departure": d(2), "status": "Checked In",
            "rooms": [{"room": "101", "adults": 2, "rate": 800}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "A2",
            "customer_email": "m.saidi@corp.com",
            "arrival": d(-2), "departure": d(3), "status": "Checked In",
            "rooms": [{"room": "105", "adults": 1, "rate": 800}],
            "families": [{"family_type": "Single", "adults": 1}],
        },
        {
            "id": "A3",
            "customer_email": "p.dupont@email.fr",
            "arrival": d(-1), "departure": d(3), "status": "Checked In",
            "rooms": [{"room": "201", "adults": 2, "rate": 1200}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "A4",
            "customer_email": "amina.b@email.com",
            "arrival": d(-2), "departure": d(4), "status": "Checked In",
            "rooms": [{"room": "205", "adults": 2, "rate": 1200}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "A5",
            "customer_email": "sarah.j@email.com",
            "arrival": d(0), "departure": d(5), "status": "Checked In",
            "rooms": [{"room": "301", "adults": 2, "rate": 2000}],
            "families": [{"family_type": "Couple", "adults": 2}],
            "package": "Honeymoon Package",
        },
        {
            "id": "A6",
            "customer_email": "fatima.cherif@email.com",
            "arrival": d(-2), "departure": d(3), "status": "Checked In",
            "rooms": [{"room": "401", "adults": 2, "children": 2, "rate": 1600}],
            "families": [{"family_type": "Family", "adults": 2, "children": 2}],
            "package": "Family Fun Package",
        },
        {
            "id": "A7",
            "customer_email": "k.messaoud@email.com",
            "arrival": d(-1), "departure": d(4), "status": "Checked In",
            "rooms": [
                {"room": "402", "adults": 2, "children": 3, "rate": 1600},
                {"room": "403", "adults": 2, "children": 1, "rate": 1600},
            ],
            "families": [{"family_type": "Large Family", "adults": 4, "children": 4}],
        },

        # ── PAST COMPLETED (arrivals -30 to -5) ────────────────────────────
        {
            "id": "P01",
            "customer_email": "y.hamdi@email.tn",
            "arrival": d(-30), "departure": d(-25), "status": "Completed",
            "rooms": [{"room": "101", "adults": 2, "rate": 800}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "P02",
            "customer_email": "ahmed.benali@email.com",
            "arrival": d(-28), "departure": d(-23), "status": "Completed",
            "rooms": [{"room": "102", "adults": 2, "rate": 800}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "P03",
            "customer_email": "c.martinez@email.es",
            "arrival": d(-25), "departure": d(-20), "status": "Completed",
            "rooms": [{"room": "103", "adults": 2, "rate": 800}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "P04",
            "customer_email": "liu.wei@email.cn",
            "arrival": d(-22), "departure": d(-17), "status": "Completed",
            "rooms": [{"room": "104", "adults": 2, "rate": 800}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "P05",
            "customer_email": "h.otmani@email.ma",
            "arrival": d(-18), "departure": d(-13), "status": "Completed",
            "rooms": [{"room": "105", "adults": 2, "rate": 800}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "P06",
            "customer_email": "n.rahmani@email.com",
            "arrival": d(-29), "departure": d(-23), "status": "Completed",
            "rooms": [{"room": "201", "adults": 2, "rate": 1200}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "P07",
            "customer_email": "j.smith@email.co.uk",
            "arrival": d(-26), "departure": d(-20), "status": "Completed",
            "rooms": [{"room": "202", "adults": 1, "rate": 1200}],
            "families": [{"family_type": "Single", "adults": 1}],
        },
        {
            "id": "P08",
            "customer_email": "fatima.cherif@email.com",
            "arrival": d(-22), "departure": d(-17), "status": "Completed",
            "rooms": [{"room": "203", "adults": 2, "children": 2, "rate": 1200}],
            "families": [{"family_type": "Family", "adults": 2, "children": 2}],
        },
        {
            "id": "P09",
            "customer_email": "y.hamdi@email.tn",
            "arrival": d(-20), "departure": d(-14), "status": "Completed",
            "rooms": [{"room": "204", "adults": 2, "rate": 1200}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "P10",
            "customer_email": "k.messaoud@email.com",
            "arrival": d(-15), "departure": d(-10), "status": "Completed",
            "rooms": [{"room": "205", "adults": 2, "rate": 1200}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "P11",
            "customer_email": "sarah.j@email.com",
            "arrival": d(-28), "departure": d(-21), "status": "Completed",
            "rooms": [{"room": "301", "adults": 2, "rate": 2000}],
            "families": [{"family_type": "Couple", "adults": 2}],
            "package": "Honeymoon Package",
        },
        {
            "id": "P12",
            "customer_email": "p.dupont@email.fr",
            "arrival": d(-24), "departure": d(-18), "status": "Completed",
            "rooms": [{"room": "302", "adults": 2, "rate": 2000}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "P13",
            "customer_email": "m.saidi@corp.com",
            "arrival": d(-20), "departure": d(-15), "status": "Completed",
            "rooms": [{"room": "303", "adults": 1, "rate": 2000}],
            "families": [{"family_type": "Single", "adults": 1}],
        },
        {
            "id": "P14",
            "customer_email": "o.belkacem@agency.dz",
            "arrival": d(-26), "departure": d(-20), "status": "Completed",
            "rooms": [{"room": "401", "adults": 2, "children": 3, "rate": 1600}],
            "families": [{"family_type": "Family", "adults": 2, "children": 3}],
        },
        {
            "id": "P15",
            "customer_email": "c.martinez@email.es",
            "arrival": d(-22), "departure": d(-16), "status": "Completed",
            "rooms": [{"room": "402", "adults": 2, "children": 2, "rate": 1600}],
            "families": [{"family_type": "Family", "adults": 2, "children": 2}],
        },
        {
            "id": "P16",
            "customer_email": "amina.b@email.com",
            "arrival": d(-18), "departure": d(-12), "status": "Completed",
            "rooms": [{"room": "403", "adults": 2, "children": 1, "rate": 1600}],
            "families": [{"family_type": "Family", "adults": 2, "children": 1}],
        },
        {
            "id": "P17",
            "customer_email": "liu.wei@email.cn",
            "arrival": d(-25), "departure": d(-19), "status": "Completed",
            "rooms": [{"room": "404", "adults": 2, "children": 3, "rate": 1600}],
            "families": [{"family_type": "Family", "adults": 2, "children": 3}],
        },
        {
            "id": "P18",
            "customer_email": "m.bernard@email.fr",
            "arrival": d(-29), "departure": d(-23), "status": "Completed",
            "rooms": [{"room": "405", "adults": 2, "rate": 1600}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "P19",
            "customer_email": "ahmed.benali@email.com",
            "arrival": d(-14), "departure": d(-9), "status": "Completed",
            "rooms": [{"room": "406", "adults": 2, "children": 1, "rate": 1600}],
            "families": [{"family_type": "Family", "adults": 2, "children": 1}],
        },

        # ── NO SHOW / CANCELLED ─────────────────────────────────────────────
        {
            "id": "NS1",
            "customer_email": "h.otmani@email.ma",
            "arrival": d(-3), "departure": d(-1), "status": "No Show",
            "rooms": [{"room": "204", "adults": 2, "rate": 1200}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "CX1",
            "customer_email": "m.bernard@email.fr",
            "arrival": d(-12), "departure": d(-8), "status": "Cancelled",
            "rooms": [{"room": "203", "adults": 2, "rate": 1200}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },

        # ── NEAR FUTURE — CONFIRMED (+1 to +20) ────────────────────────────
        {
            "id": "F01",
            "customer_email": "h.otmani@email.ma",
            "arrival": d(5), "departure": d(10), "status": "Confirmed",
            "rooms": [{"room": "101", "adults": 2, "rate": 800}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "F02",
            "customer_email": "m.bernard@email.fr",
            "arrival": d(2), "departure": d(7), "status": "Confirmed",
            "rooms": [{"room": "102", "adults": 2, "rate": 800}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "F03",
            "customer_email": "p.dupont@email.fr",
            "arrival": d(5), "departure": d(10), "status": "Confirmed",
            "rooms": [{"room": "103", "adults": 2, "rate": 800}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "F04",
            "customer_email": "j.smith@email.co.uk",
            "arrival": d(5), "departure": d(11), "status": "Confirmed",
            "rooms": [{"room": "201", "adults": 1, "rate": 1200}],
            "families": [{"family_type": "Single", "adults": 1}],
        },
        {
            "id": "F05",
            "customer_email": "n.rahmani@email.com",
            "arrival": d(3), "departure": d(9), "status": "Confirmed",
            "rooms": [{"room": "303", "adults": 2, "rate": 2000}],
            "families": [{"family_type": "Couple", "adults": 2}],
            "package": "Honeymoon Package",
        },
        {
            "id": "F06",
            "customer_email": "c.martinez@email.es",
            "arrival": d(2), "departure": d(8), "status": "Confirmed",
            "rooms": [{"room": "404", "adults": 2, "children": 2, "rate": 1600}],
            "families": [{"family_type": "Family", "adults": 2, "children": 2}],
        },
        {
            "id": "F07",
            "customer_email": "o.belkacem@agency.dz",
            "arrival": d(3), "departure": d(9), "status": "Confirmed",
            "rooms": [{"room": "405", "adults": 2, "children": 3, "rate": 1600}],
            "families": [{"family_type": "Family", "adults": 2, "children": 3}],
        },
        {
            "id": "F08",
            "customer_email": "y.hamdi@email.tn",
            "arrival": d(2), "departure": d(8), "status": "Confirmed",
            "rooms": [{"room": "406", "adults": 2, "children": 2, "rate": 1600}],
            "families": [{"family_type": "Family", "adults": 2, "children": 2}],
        },
        {
            "id": "F09",
            "customer_email": "fatima.cherif@email.com",
            "arrival": d(8), "departure": d(13), "status": "Confirmed",
            "rooms": [{"room": "402", "adults": 2, "children": 2, "rate": 1600}],
            "families": [{"family_type": "Family", "adults": 2, "children": 2}],
        },
        {
            "id": "F10",
            "customer_email": "k.messaoud@email.com",
            "arrival": d(8), "departure": d(14), "status": "Confirmed",
            "rooms": [{"room": "403", "adults": 2, "children": 1, "rate": 1600}],
            "families": [{"family_type": "Family", "adults": 2, "children": 1}],
        },
        {
            "id": "F11",
            "customer_email": "liu.wei@email.cn",
            "arrival": d(1), "departure": d(7), "status": "Confirmed",
            "rooms": [{"room": "104", "adults": 2, "rate": 800}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "F12",
            "customer_email": "amina.b@email.com",
            "arrival": d(8), "departure": d(14), "status": "Confirmed",
            "rooms": [{"room": "202", "adults": 2, "rate": 1200}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },

        # ── FAR FUTURE — MONTH 2 & 3 (+30 to +60) ─────────────────────────
        {
            "id": "M2A",
            "customer_email": "p.dupont@email.fr",
            "arrival": d(35), "departure": d(41), "status": "Confirmed",
            "rooms": [{"room": "101", "adults": 2, "rate": 800}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "M2B",
            "customer_email": "n.rahmani@email.com",
            "arrival": d(32), "departure": d(38), "status": "Confirmed",
            "rooms": [{"room": "201", "adults": 2, "rate": 1200}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "M2C",
            "customer_email": "sarah.j@email.com",
            "arrival": d(40), "departure": d(47), "status": "Confirmed",
            "rooms": [{"room": "301", "adults": 2, "rate": 2000}],
            "families": [{"family_type": "Couple", "adults": 2}],
            "package": "Honeymoon Package",
        },
        {
            "id": "M2D",
            "customer_email": "k.messaoud@email.com",
            "arrival": d(30), "departure": d(37), "status": "Confirmed",
            "rooms": [{"room": "401", "adults": 2, "children": 3, "rate": 1600}],
            "families": [{"family_type": "Family", "adults": 2, "children": 3}],
        },
        {
            "id": "M2E",
            "customer_email": "c.martinez@email.es",
            "arrival": d(30), "departure": d(35), "status": "Confirmed",
            "rooms": [{"room": "105", "adults": 2, "rate": 800}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "M2F",
            "customer_email": "ahmed.benali@email.com",
            "arrival": d(45), "departure": d(51), "status": "Confirmed",
            "rooms": [{"room": "202", "adults": 2, "rate": 1200}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },

        # ── DRAFT ───────────────────────────────────────────────────────────
        {
            "id": "DR1",
            "customer_email": "n.rahmani@email.com",
            "arrival": d(10), "departure": d(17), "status": "Draft",
            "rooms": [{"room": "204", "adults": 2, "rate": 1200}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
        {
            "id": "DR2",
            "customer_email": "o.belkacem@agency.dz",
            "arrival": d(20), "departure": d(28), "status": "Draft",
            "rooms": [{"room": "302", "adults": 2, "rate": 2000}],
            "families": [{"family_type": "Couple", "adults": 2}],
        },
    ]

    created = 0
    skipped = 0
    for s in scenarios:
        try:
            customer = _get_customer_by_email(s["customer_email"])
            if not customer:
                ok(f"    Skipped {s['id']}: customer not found ({s['customer_email']})")
                skipped += 1
                continue

            existing = frappe.db.exists("Hotel Reservation", {
                "customer": customer,
                "arrival_date": s["arrival"],
                "is_test_data": 1,
            })
            if existing:
                skipped += 1
                continue

            doc = frappe.get_doc({
                "doctype": "Hotel Reservation",
                "customer": customer,
                "booking_date": add_days(s["arrival"], -7),
                "arrival_date": s["arrival"],
                "departure_date": s["departure"],
                "status": s["status"],
                "package": s.get("package"),
                "notes": f"Test scenario {s['id']}",
                "is_test_data": 1,
            })
            for r in s.get("rooms", []):
                r_item = {k: v for k, v in r.items()}
                r_item["room_type"] = frappe.db.get_value("Hotel Room", r["room"], "room_type")
                doc.append("rooms", r_item)
            for f in s.get("families", []):
                f_item = {k: v for k, v in f.items()}
                f_item["total_guests"] = (f.get("adults", 0) + f.get("children", 0) + f.get("infants", 0))
                doc.append("families", f_item)

            doc.flags.ignore_validate = True
            doc.insert(ignore_permissions=True)
            created += 1
        except Exception as e:
            frappe.db.rollback()
            ok(f"    Skipped {s['id']}: {e}")
            skipped += 1

    ok(f"  Reservations: {created} created, {skipped} skipped (of {len(scenarios)})")


# ─── Stays ────────────────────────────────────────────────────────────────────

def create_test_stays(ok):
    """
    Create stays for:
      - "Checked In"  reservations → status "Active"     (room stays Occupied)
      - "Completed"   reservations → status "Checked Out" (room stays Available)
    """
    created = 0

    for status_filter, stay_status, room_status in [
        ("Checked In",  "Active",      "Occupied"),
        ("Completed",   "Checked Out", "Available"),
    ]:
        reservations = frappe.get_all(
            "Hotel Reservation",
            filters={"status": status_filter, "is_test_data": 1},
            pluck="name",
        )
        for res_name in reservations:
            if frappe.db.count("Hotel Stay", {"reservation": res_name}):
                continue

            res = frappe.get_doc("Hotel Reservation", res_name)
            for res_room in res.rooms:
                stay = frappe.get_doc({
                    "doctype": "Hotel Stay",
                    "customer": res.customer,
                    "reservation": res_name,
                    "room": res_room.room,
                    "checkin_date": f"{res.arrival_date} 14:00:00",
                    "expected_checkout": res.departure_date,
                    "status": stay_status,
                    "is_test_data": 1,
                })
                stay.insert(ignore_permissions=True)
                frappe.db.set_value("Hotel Room", res_room.room, "status", room_status)
                created += 1

    ok(f"  Stays: {created} created")


# ─── Folios ───────────────────────────────────────────────────────────────────

def create_test_folios(ok):
    """
    Create folios for all stays (Active and Checked Out).
      - Active stays      → status "Open" (partial charges so far)
      - Checked Out stays → status "Paid" (full room charges for all nights)
    Breakfast extras added for variety.
    """
    from frappe.utils import date_diff, getdate
    from datetime import timedelta

    created = 0

    stays = frappe.get_all(
        "Hotel Stay",
        filters={"is_test_data": 1},
        fields=["name", "customer", "reservation", "room", "checkin_date", "expected_checkout", "status"],
    )

    for stay in stays:
        if frappe.db.exists("Hotel Folio", {"stay": stay.name}):
            continue

        # Get room rate from reservation
        rate = 800
        if stay.reservation:
            res_rate = frappe.db.get_value(
                "Hotel Reservation Room",
                {"parent": stay.reservation, "room": stay.room},
                "rate",
            )
            if res_rate:
                rate = res_rate

        checkin_str = getdate(stay.checkin_date).strftime("%Y-%m-%d")
        nights = date_diff(stay.expected_checkout, checkin_str)
        if nights < 1:
            nights = 1

        is_past = stay.status == "Checked Out"
        folio_status = "Open" if not is_past else "Paid"

        folio = frappe.get_doc({
            "doctype": "Hotel Folio",
            "customer": stay.customer,
            "reservation": stay.reservation,
            "stay": stay.name,
            "status": folio_status,
            "is_test_data": 1,
        })

        # Room charge per night
        current_date = getdate(stay.checkin_date)
        for _n in range(nights):
            folio.append("items", {
                "date": str(current_date),
                "charge_type": "Room",
                "description": f"Room charge - {stay.room}",
                "quantity": 1,
                "rate": rate,
                "amount": rate,
                "room": stay.room,
                "is_test_data": 1,
            })
            current_date += timedelta(days=1)

        # Breakfast extras
        breakfast_date = getdate(stay.checkin_date)
        for _n in range(min(nights, 3)):
            folio.append("items", {
                "date": str(breakfast_date),
                "charge_type": "Breakfast",
                "description": "Breakfast × 2 guests",
                "quantity": 2,
                "rate": 120,
                "amount": 240,
                "is_test_data": 1,
            })
            breakfast_date += timedelta(days=1)

        total = sum(i.amount for i in folio.items)
        folio.total_charges = total
        folio.total_payments = total if is_past else 0
        folio.balance = 0 if is_past else total
        folio.insert(ignore_permissions=True)
        created += 1

    ok(f"  Folios: {created} created")


# ─── Payments ─────────────────────────────────────────────────────────────────

def create_test_payments(ok):
    """
    Create payments for all folios that have no payment yet:
      - Paid folios (past stays)    → full payment, dated at checkout
      - Open folios (active stays)  → 50 % advance payment, dated today

    Payment dates are spread across real reservation dates so the Revenue
    Trend dashboard chart shows realistic data over 3 months.
    """
    from frappe.utils import getdate

    METHODS = ["Cash", "Credit Card", "Bank Transfer", "Cash", "Credit Card"]

    created = 0

    folios = frappe.get_all(
        "Hotel Folio",
        filters={"is_test_data": 1},
        fields=["name", "customer", "reservation", "stay", "total_charges", "status"],
    )

    for folio in folios:
        if frappe.db.exists("Hotel Payment", {"folio": folio.name}):
            continue

        total = folio.total_charges or 0
        if total <= 0:
            continue

        is_paid = folio.status == "Paid"

        # Use checkout date for past stays so revenue appears on the correct month
        pay_date = nowdate()
        if is_paid and folio.stay:
            checkout = frappe.db.get_value("Hotel Stay", folio.stay, "expected_checkout")
            if checkout:
                pay_date = str(checkout)

        # Pick payment method deterministically from folio name
        idx = sum(ord(c) for c in folio.name) % len(METHODS)
        method = METHODS[idx]

        if is_paid:
            # Full settlement
            amount = total
            pay_type = "Full"
            new_folio_status = "Paid"
            remaining = 0.0
        else:
            # 50 % advance
            amount = round(total * 0.5, 2)
            pay_type = "Partial"
            new_folio_status = "Partially Paid"
            remaining = round(total - amount, 2)

        payment = frappe.get_doc({
            "doctype": "Hotel Payment",
            "customer": folio.customer,
            "reservation": folio.reservation,
            "stay": folio.stay,
            "folio": folio.name,
            "payment_date": pay_date,
            "payment_type": pay_type,
            "payment_method": method,
            "amount": amount,
            "is_test_data": 1,
        })
        payment.insert(ignore_permissions=True)

        frappe.db.set_value("Hotel Folio", folio.name, {
            "total_payments": amount,
            "balance": remaining,
            "status": new_folio_status,
        })
        created += 1

    ok(f"  Payments: {created} created")


# ─── Housekeeping ─────────────────────────────────────────────────────────────

def create_test_housekeeping(ok):
    # Mark some available rooms as needing cleaning
    rooms = frappe.get_all("Hotel Room",
        filters={"status": "Available", "is_test_data": 1},
        fields=["name", "housekeeping_status"],
        limit=5)

    created = 0
    for room in rooms:
        if frappe.db.exists("Hotel Housekeeping", {"room": room.name, "is_test_data": 1}):
            continue

        hk = frappe.get_doc({
            "doctype": "Hotel Housekeeping",
            "room": room.name,
            "date": nowdate(),
            "previous_status": "Dirty",
            "new_status": "Clean",
            "assigned_to": "Administrator",
            "notes": "Test housekeeping record",
            "is_test_data": 1,
        })
        hk.insert(ignore_permissions=True)
        created += 1

    ok(f"  Housekeeping: {created} created")