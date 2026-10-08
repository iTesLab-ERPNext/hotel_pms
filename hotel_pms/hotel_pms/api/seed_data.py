import frappe
from frappe.utils import add_days, nowdate


def seed_all():
    results = {}
    results["room_types"] = seed_room_types()
    results["rooms"] = seed_rooms()
    results["services"] = seed_services()
    results["booking_sources"] = seed_booking_sources()
    results["customers"] = seed_customers()
    results["reservations"] = seed_reservations()
    return results


def _exists(doctype, name):
    return frappe.db.exists(doctype, name)


def seed_room_types():
    types = [
        {"name": "STD", "room_type_name": "Standard Room", "base_rate": 80, "max_occupancy": 2, "description": "Comfortable standard room with all amenities"},
        {"name": "DLX", "room_type_name": "Deluxe Room", "base_rate": 120, "max_occupancy": 2, "description": "Spacious deluxe room with premium furnishings"},
        {"name": "SUP", "room_type_name": "Superior Room", "base_rate": 100, "max_occupancy": 2, "description": "Superior room with garden or pool view"},
        {"name": "JRS", "room_type_name": "Junior Suite", "base_rate": 180, "max_occupancy": 3, "description": "Junior suite with separate seating area"},
        {"name": "STE", "room_type_name": "Suite", "base_rate": 250, "max_occupancy": 4, "description": "Luxury suite with lounge and premium amenities"},
        {"name": "FML", "room_type_name": "Family Room", "base_rate": 160, "max_occupancy": 5, "description": "Spacious family room with extra beds"},
        {"name": "ACC", "room_type_name": "Accessible Room", "base_rate": 85, "max_occupancy": 2, "description": "Fully accessible room with adapted facilities"},
    ]
    created, skipped = 0, 0
    for t in types:
        if not _exists("Hotel Room Type", t["name"]):
            doc = frappe.new_doc("Hotel Room Type")
            doc.update(t)
            doc.insert()
            created += 1
        else:
            skipped += 1
    return {"created": created, "skipped": skipped}


def seed_rooms():
    rooms = [
        # Floor 1
        {"name": "101", "room_number": "101", "room_type": "STD", "floor": "1", "rate": 80, "status": "Available", "is_active": 1},
        {"name": "102", "room_number": "102", "room_type": "STD", "floor": "1", "rate": 80, "status": "Available", "is_active": 1},
        {"name": "103", "room_number": "103", "room_type": "ACC", "floor": "1", "rate": 85, "status": "Available", "is_active": 1},
        {"name": "104", "room_number": "104", "room_type": "FML", "floor": "1", "rate": 160, "status": "Available", "is_active": 1},
        # Floor 2
        {"name": "201", "room_number": "201", "room_type": "STD", "floor": "2", "rate": 80, "status": "Available", "is_active": 1},
        {"name": "202", "room_number": "202", "room_type": "DLX", "floor": "2", "rate": 120, "status": "Available", "is_active": 1},
        {"name": "203", "room_number": "203", "room_type": "DLX", "floor": "2", "rate": 120, "status": "Available", "is_active": 1},
        {"name": "204", "room_number": "204", "room_type": "SUP", "floor": "2", "rate": 100, "status": "Available", "is_active": 1},
        {"name": "205", "room_number": "205", "room_type": "SUP", "floor": "2", "rate": 100, "status": "Available", "is_active": 1},
        # Floor 3
        {"name": "301", "room_number": "301", "room_type": "DLX", "floor": "3", "rate": 120, "status": "Available", "is_active": 1},
        {"name": "302", "room_number": "302", "room_type": "DLX", "floor": "3", "rate": 120, "status": "Available", "is_active": 1},
        {"name": "303", "room_number": "303", "room_type": "JRS", "floor": "3", "rate": 180, "status": "Available", "is_active": 1},
        {"name": "304", "room_number": "304", "room_type": "JRS", "floor": "3", "rate": 180, "status": "Available", "is_active": 1},
        # Floor 4
        {"name": "401", "room_number": "401", "room_type": "SUP", "floor": "4", "rate": 110, "status": "Available", "is_active": 1},
        {"name": "402", "room_number": "402", "room_type": "STE", "floor": "4", "rate": 250, "status": "Available", "is_active": 1},
        {"name": "403", "room_number": "403", "room_type": "STE", "floor": "4", "rate": 280, "status": "Available", "is_active": 1},
        # Penthouse
        {"name": "PH1", "room_number": "PH1", "room_type": "STE", "floor": "5", "rate": 450, "status": "Available", "is_active": 1},
        {"name": "PH2", "room_number": "PH2", "room_type": "STE", "floor": "5", "rate": 500, "status": "Available", "is_active": 1},
        {"name": "PH3", "room_number": "PH3", "room_type": "FML", "floor": "5", "rate": 300, "status": "Available", "is_active": 1},
    ]
    created, skipped = 0, 0
    for r in rooms:
        if not _exists("Hotel Room", r["name"]):
            doc = frappe.new_doc("Hotel Room")
            doc.update(r)
            doc.insert()
            created += 1
        else:
            skipped += 1
    return {"created": created, "skipped": skipped}


def seed_services():
    services = [
        {"name": "BKFT", "service_name": "Breakfast", "charge_type": "F&B", "rate": 15, "is_active": 1},
        {"name": "LNCH", "service_name": "Lunch", "charge_type": "F&B", "rate": 20, "is_active": 1},
        {"name": "DNNE", "service_name": "Dinner", "charge_type": "F&B", "rate": 35, "is_active": 1},
        {"name": "MNBR", "service_name": "Mini Bar", "charge_type": "F&B", "rate": 10, "is_active": 1},
        {"name": "LAUN", "service_name": "Laundry", "charge_type": "Laundry", "rate": 25, "is_active": 1},
        {"name": "IRNG", "service_name": "Ironing", "charge_type": "Laundry", "rate": 10, "is_active": 1},
        {"name": "TRNS", "service_name": "Airport Transfer", "charge_type": "Transport", "rate": 50, "is_active": 1},
        {"name": "PRKG", "service_name": "Parking", "charge_type": "Parking", "rate": 10, "is_active": 1},
        {"name": "SPSS", "service_name": "Spa Session", "charge_type": "Spa", "rate": 80, "is_active": 1},
        {"name": "POOL", "service_name": "Pool Access", "charge_type": "Recreation", "rate": 20, "is_active": 1},
    ]
    created, skipped = 0, 0
    for s in services:
        if not _exists("Hotel Service", s["name"]):
            doc = frappe.new_doc("Hotel Service")
            doc.update(s)
            doc.insert()
            created += 1
        else:
            skipped += 1
    return {"created": created, "skipped": skipped}


def seed_booking_sources():
    sources = [
        {"name": "DRCT", "source_name": "Direct", "commission_pct": 0},
        {"name": "WLKN", "source_name": "Walk-In", "commission_pct": 0},
        {"name": "BKNG", "source_name": "Booking.com", "commission_pct": 15},
        {"name": "EXPR", "source_name": "Expedia", "commission_pct": 18},
        {"name": "AIRB", "source_name": "Airbnb", "commission_pct": 3},
        {"name": "AGDA", "source_name": "Agoda", "commission_pct": 12},
        {"name": "TRVA", "source_name": "TripAdvisor", "commission_pct": 10},
        {"name": "CORP", "source_name": "Corporate", "commission_pct": 0},
        {"name": "TVLA", "source_name": "Travel Agency", "commission_pct": 10},
    ]
    created, skipped = 0, 0
    for s in sources:
        if not _exists("Hotel Booking Source", s["name"]):
            doc = frappe.new_doc("Hotel Booking Source")
            doc.update(s)
            doc.insert()
            created += 1
        else:
            skipped += 1
    return {"created": created, "skipped": skipped}


def seed_customers():
    customers = [
        {"first_name": "Ahmed", "last_name": "Ben Ali", "nationality": "Tunisian"},
        {"first_name": "Marie", "last_name": "Dupont", "nationality": "French"},
        {"first_name": "John", "last_name": "Smith", "nationality": "British"},
        {"first_name": "Fatima", "last_name": "Al-Rashid", "nationality": "Emirati"},
        {"first_name": "Carlos", "last_name": "Garcia", "nationality": "Spanish"},
    ]
    created, skipped = 0, 0
    for c in customers:
        full_name = f"{c['first_name']} {c['last_name']}"
        if not frappe.db.exists("Customer", {"customer_name": full_name}):
            doc = frappe.new_doc("Customer")
            doc.customer_name = full_name
            doc.customer_type = "Individual"
            doc.customer_group = frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "All Customer Groups"
            doc.territory = frappe.db.get_value("Territory", {"is_group": 0}, "name") or "All Territories"
            doc.insert()
            created += 1
        else:
            skipped += 1
    return {"created": created, "skipped": skipped}


def seed_reservations():
    reservations_data = [
        {
            "guest_name": "Ahmed Ben Ali",
            "arrival_date": add_days(nowdate(), 1),
            "departure_date": add_days(nowdate(), 4),
            "room_type": "DLX",
            "number_of_guests": 2,
            "status": "Confirmed",
            "booking_source": "DRCT",
        },
        {
            "guest_name": "Marie Dupont",
            "arrival_date": add_days(nowdate(), 2),
            "departure_date": add_days(nowdate(), 5),
            "room_type": "STE",
            "number_of_guests": 2,
            "status": "Confirmed",
            "booking_source": "BKNG",
        },
        {
            "guest_name": "John Smith",
            "arrival_date": nowdate(),
            "departure_date": add_days(nowdate(), 3),
            "room_type": "STD",
            "number_of_guests": 1,
            "status": "Confirmed",
            "booking_source": "CORP",
        },
        {
            "guest_name": "Fatima Al-Rashid",
            "arrival_date": add_days(nowdate(), 3),
            "departure_date": add_days(nowdate(), 7),
            "room_type": "JRS",
            "number_of_guests": 3,
            "status": "Pending",
            "booking_source": "EXPR",
        },
        {
            "guest_name": "Carlos Garcia",
            "arrival_date": add_days(nowdate(), -1),
            "departure_date": add_days(nowdate(), 2),
            "room_type": "STD",
            "number_of_guests": 2,
            "status": "Checked In",
            "booking_source": "DRCT",
        },
    ]

    created, skipped = 0, 0
    for rd in reservations_data:
        if frappe.db.exists("Hotel Reservation", {"guest_name": rd["guest_name"], "arrival_date": rd["arrival_date"]}):
            skipped += 1
            continue
        doc = frappe.new_doc("Hotel Reservation")
        doc.update(rd)
        doc.insert()
        created += 1

    return {"created": created, "skipped": skipped}
