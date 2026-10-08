"""
Hotel PMS - Seed Data
Run: bench execute hotel_pms.fixtures.seed_data.create_demo_data
"""

import frappe
from frappe.utils import add_days, today, getdate


def create_demo_data():
    """Create complete demo data for Hotel PMS."""
    print("Creating Hotel PMS demo data...")

    frappe.db.savepoint("seed_start")
    try:
        create_customer_categories()
        create_family_types()
        create_room_types()
        create_rooms()
        create_services()
        create_packages()
        create_customers()
        create_reservations()
        frappe.db.commit()
        print("Hotel PMS demo data created successfully!")
    except Exception as e:
        frappe.db.rollback()
        print(f"Error creating demo data: {e}")
        raise


def _exists(doctype, name):
    return frappe.db.exists(doctype, name)


def _create_if_not_exists(doc_data):
    doctype = doc_data["doctype"]
    name = doc_data.get("name") or doc_data.get(list(doc_data.keys())[1])
    if _exists(doctype, name):
        return frappe.get_doc(doctype, name)
    doc = frappe.get_doc(doc_data)
    doc.insert(ignore_permissions=True)
    return doc


def create_customer_categories():
    print("  Creating customer categories...")
    for cat in ["Individual", "Family", "Corporate", "VIP", "Agency", "Group"]:
        if not _exists("Hotel Customer Category", cat):
            frappe.get_doc({"doctype": "Hotel Customer Category", "category_name": cat}).insert(ignore_permissions=True)


def create_family_types():
    print("  Creating family types...")
    for ft in ["Single", "Couple", "Family", "Large Family", "Group"]:
        if not _exists("Hotel Family Type", ft):
            frappe.get_doc({"doctype": "Hotel Family Type", "type_name": ft}).insert(ignore_permissions=True)


def create_room_types():
    print("  Creating room types...")
    types = [
        {"room_type": "Single",  "code": "SGL", "capacity_adults": 1, "capacity_children": 0, "base_price": 80},
        {"room_type": "Double",  "code": "DBL", "capacity_adults": 2, "capacity_children": 1, "base_price": 120},
        {"room_type": "Twin",    "code": "TWN", "capacity_adults": 2, "capacity_children": 0, "base_price": 110},
        {"room_type": "Triple",  "code": "TRP", "capacity_adults": 3, "capacity_children": 1, "base_price": 150},
        {"room_type": "Family",  "code": "FAM", "capacity_adults": 2, "capacity_children": 2, "base_price": 180},
        {"room_type": "Suite",   "code": "STE", "capacity_adults": 2, "capacity_children": 2, "base_price": 300},
        {"room_type": "Deluxe",  "code": "DLX", "capacity_adults": 2, "capacity_children": 2, "base_price": 220},
        {"room_type": "Villa",   "code": "VIL", "capacity_adults": 4, "capacity_children": 4, "base_price": 500},
    ]
    for t in types:
        if not _exists("Hotel Room Type", t["room_type"]):
            frappe.get_doc({"doctype": "Hotel Room Type", "active": 1, **t}).insert(ignore_permissions=True)


def create_rooms():
    print("  Creating rooms...")
    rooms = [
        {"room_number": "101", "room_type": "Single",  "floor": 1, "capacity": 1},
        {"room_number": "102", "room_type": "Double",  "floor": 1, "capacity": 2},
        {"room_number": "103", "room_type": "Twin",    "floor": 1, "capacity": 2},
        {"room_number": "104", "room_type": "Triple",  "floor": 1, "capacity": 3},
        {"room_number": "105", "room_type": "Family",  "floor": 1, "capacity": 4},
        {"room_number": "201", "room_type": "Double",  "floor": 2, "capacity": 2},
        {"room_number": "202", "room_type": "Deluxe",  "floor": 2, "capacity": 2},
        {"room_number": "203", "room_type": "Suite",   "floor": 2, "capacity": 4},
        {"room_number": "204", "room_type": "Family",  "floor": 2, "capacity": 4},
        {"room_number": "205", "room_type": "Villa",   "floor": 2, "capacity": 6},
    ]
    for r in rooms:
        if not _exists("Hotel Room", r["room_number"]):
            frappe.get_doc({"doctype": "Hotel Room", "status": "Available", "active": 1, **r}).insert(ignore_permissions=True)


def create_services():
    print("  Creating services...")
    services = [
        {"service_name": "Breakfast",     "service_category": "Food & Beverage",  "rate": 15},
        {"service_name": "Lunch",          "service_category": "Food & Beverage",  "rate": 20},
        {"service_name": "Dinner",         "service_category": "Food & Beverage",  "rate": 25},
        {"service_name": "Restaurant",     "service_category": "Food & Beverage",  "rate": 0},
        {"service_name": "Spa",            "service_category": "Spa & Wellness",   "rate": 60},
        {"service_name": "Laundry",        "service_category": "Laundry",          "rate": 10},
        {"service_name": "Transport",      "service_category": "Transport",         "rate": 30},
        {"service_name": "Horse Riding",   "service_category": "Activities",        "rate": 45},
        {"service_name": "Extra Bed",      "service_category": "Accommodation",     "rate": 20},
    ]
    for s in services:
        if not _exists("Hotel Service", s["service_name"]):
            frappe.get_doc({"doctype": "Hotel Service", "active": 1, **s}).insert(ignore_permissions=True)


def create_packages():
    print("  Creating packages...")
    packages = [
        {
            "package_name": "Room Only",
            "package_code": "RO",
            "items": []
        },
        {
            "package_name": "Bed & Breakfast",
            "package_code": "BB",
            "items": [{"service": "Breakfast", "quantity": 1, "rate": 15}]
        },
        {
            "package_name": "Half Board",
            "package_code": "HB",
            "items": [
                {"service": "Breakfast", "quantity": 1, "rate": 15},
                {"service": "Dinner",    "quantity": 1, "rate": 25}
            ]
        },
        {
            "package_name": "Full Board",
            "package_code": "FB",
            "items": [
                {"service": "Breakfast", "quantity": 1, "rate": 15},
                {"service": "Lunch",     "quantity": 1, "rate": 20},
                {"service": "Dinner",    "quantity": 1, "rate": 25}
            ]
        },
        {
            "package_name": "Family Weekend",
            "package_code": "FW",
            "items": [
                {"service": "Breakfast",   "quantity": 1, "rate": 15},
                {"service": "Dinner",      "quantity": 1, "rate": 25},
                {"service": "Horse Riding","quantity": 1, "rate": 45}
            ]
        },
        {
            "package_name": "Adventure Package",
            "package_code": "ADV",
            "items": [
                {"service": "Breakfast",   "quantity": 1, "rate": 15},
                {"service": "Horse Riding","quantity": 2, "rate": 45},
                {"service": "Transport",   "quantity": 1, "rate": 30}
            ]
        },
    ]
    for p in packages:
        if not _exists("Hotel Package", p["package_name"]):
            doc = frappe.get_doc({
                "doctype": "Hotel Package",
                "package_name": p["package_name"],
                "package_code": p["package_code"],
                "active": 1,
                "items": [{"doctype": "Hotel Package Item", **item} for item in p["items"]]
            })
            doc.insert(ignore_permissions=True)


def create_customers():
    print("  Creating demo customers...")
    customers = [
        {"first_name": "Ahmed",   "last_name": "Ben Ali",     "phone": "+216 22 000 001", "email": "ahmed@example.com",    "nationality": "Tunisian",  "customer_category": "Individual"},
        {"first_name": "Sophie",  "last_name": "Martin",      "phone": "+33 6 00 000 002", "email": "sophie@example.com",   "nationality": "French",    "customer_category": "Family",     "family_type": "Family"},
        {"first_name": "John",    "last_name": "Smith",        "phone": "+1 555 000 003",   "email": "john@example.com",     "nationality": "American",  "customer_category": "VIP"},
        {"first_name": "Fatima",  "last_name": "Al Rashid",   "phone": "+971 50 000 004",  "email": "fatima@example.com",   "nationality": "Emirati",   "customer_category": "Corporate"},
        {"first_name": "Carlos",  "last_name": "Rodriguez",   "phone": "+34 600 000 005",  "email": "carlos@example.com",   "nationality": "Spanish",   "customer_category": "Agency"},
    ]
    for c in customers:
        if not frappe.db.exists("Hotel Customer", {"first_name": c["first_name"], "last_name": c["last_name"]}):
            frappe.get_doc({"doctype": "Hotel Customer", **c}).insert(ignore_permissions=True)


def _get_customer(first_name, last_name):
    result = frappe.db.get_value("Hotel Customer",
        {"first_name": first_name, "last_name": last_name}, "name")
    return result


def create_reservations():
    print("  Creating demo reservations...")

    c1 = _get_customer("Ahmed", "Ben Ali")
    c2 = _get_customer("Sophie", "Martin")
    c3 = _get_customer("John", "Smith")
    c4 = _get_customer("Fatima", "Al Rashid")
    c5 = _get_customer("Carlos", "Rodriguez")

    t = getdate(today())

    # 1. Future reservation (Draft)
    _create_reservation({
        "customer": c1,
        "booking_date": today(),
        "arrival_date": add_days(t, 10),
        "departure_date": add_days(t, 13),
        "status": "Draft",
        "package": "Room Only",
        "rooms": [{"room": "103", "adults": 1, "rate": 110}],
        "families": [{"family_type": "Single", "adults": 1, "children": 0, "infants": 0}],
        "notes": "Future draft reservation"
    })

    # 2. Confirmed reservation
    _create_reservation({
        "customer": c2,
        "booking_date": today(),
        "arrival_date": add_days(t, 3),
        "departure_date": add_days(t, 7),
        "status": "Confirmed",
        "package": "Bed & Breakfast",
        "rooms": [{"room": "105", "adults": 2, "children": 2, "rate": 180}],
        "families": [{"family_type": "Family", "adults": 2, "children": 2, "infants": 0}],
        "notes": "Family confirmed reservation"
    }, submit=True)

    # 3. Confirmed with advance payment
    res3 = _create_reservation({
        "customer": c3,
        "booking_date": add_days(t, -2),
        "arrival_date": add_days(t, 5),
        "departure_date": add_days(t, 8),
        "status": "Confirmed",
        "package": "Half Board",
        "rooms": [{"room": "203", "adults": 2, "rate": 300}],
        "families": [{"family_type": "Couple", "adults": 2, "children": 0, "infants": 0}],
        "notes": "VIP with advance payment"
    }, submit=True)
    if res3:
        _add_advance_payment(res3, c3, 300)

    # 4. Multi-room reservation
    _create_reservation({
        "customer": c5,
        "booking_date": add_days(t, -1),
        "arrival_date": add_days(t, 15),
        "departure_date": add_days(t, 20),
        "status": "Confirmed",
        "package": "Full Board",
        "rooms": [
            {"room": "101", "adults": 1, "rate": 80},
            {"room": "102", "adults": 2, "rate": 120},
        ],
        "families": [
            {"family_type": "Single", "adults": 1, "children": 0, "infants": 0},
            {"family_type": "Couple", "adults": 2, "children": 0, "infants": 0},
        ],
        "notes": "Group multi-room reservation"
    }, submit=True)

    # 5. Active stay (check-in already done)
    res5 = _create_reservation({
        "customer": c4,
        "booking_date": add_days(t, -3),
        "arrival_date": add_days(t, -1),
        "departure_date": add_days(t, 3),
        "status": "Confirmed",
        "package": "Family Weekend",
        "rooms": [{"room": "204", "adults": 2, "children": 2, "rate": 180}],
        "families": [{"family_type": "Family", "adults": 2, "children": 2, "infants": 1}],
        "notes": "Currently active stay"
    }, submit=True)
    if res5:
        _do_checkin(res5, c4, add_spa_charge=True)

    print("  Reservations created.")


def _create_reservation(data, submit=False):
    # Check if already exists for this customer and arrival
    existing = frappe.db.get_value("Hotel Reservation", {
        "customer": data["customer"],
        "arrival_date": str(data["arrival_date"])
    }, "name")
    if existing:
        return existing

    rooms_data = data.pop("rooms", [])
    families_data = data.pop("families", [])

    doc = frappe.get_doc({
        "doctype": "Hotel Reservation",
        **data,
        "rooms": [{"doctype": "Hotel Reservation Room", **r} for r in rooms_data],
        "families": [{"doctype": "Hotel Reservation Guest", **f} for f in families_data],
    })
    doc.insert(ignore_permissions=True)

    if submit and doc.status == "Draft":
        doc.submit()

    return doc.name


def _add_advance_payment(reservation, customer, amount):
    if frappe.db.exists("Hotel Payment", {"reservation": reservation, "payment_type": "Advance Payment", "docstatus": 1}):
        return
    payment = frappe.get_doc({
        "doctype": "Hotel Payment",
        "reservation": reservation,
        "customer": customer,
        "payment_date": today(),
        "payment_method": "Card",
        "payment_type": "Advance Payment",
        "amount": amount,
        "notes": "Advance payment - demo"
    })
    payment.insert(ignore_permissions=True)
    payment.submit()


def _do_checkin(reservation, customer, add_spa_charge=False):
    if frappe.db.exists("Hotel Stay", {"reservation": reservation}):
        return
    from hotel_pms.api.checkin import checkin
    result = checkin(reservation)
    if add_spa_charge and result.get("stays"):
        stay_name = result["stays"][0]
        folio = frappe.db.get_value("Hotel Folio", {"stay": stay_name}, "name")
        if folio:
            folio_doc = frappe.get_doc("Hotel Folio", folio)
            folio_doc.append("items", {
                "date": today(),
                "service": "Spa",
                "description": "Spa - demo charge",
                "quantity": 1,
                "rate": 60,
                "amount": 60
            })
            folio_doc.save(ignore_permissions=True)
