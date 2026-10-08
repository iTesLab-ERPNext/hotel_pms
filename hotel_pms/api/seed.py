import frappe
from frappe import _
from frappe.utils import add_days, today, getdate

# Tag used to identify demo data
DEMO_TAG = "__hotel_pms_demo__"

@frappe.whitelist()
def add_test_data():
    """Create complete Hotel PMS demo data. Safe to run multiple times."""
    created = []
    errors = []

    try:
        _create_customer_categories(created)
        _create_family_types(created)
        _create_room_types(created)
        _create_rooms(created)
        _create_services(created)
        _create_packages(created)
        _create_customers(created)
        _create_reservations(created)
        frappe.db.commit()
        return {"success": True, "created": created, "message": f"Created {len(created)} records successfully"}
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Hotel PMS Seed Data Error")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def delete_test_data():
    """Delete only demo data tagged with DEMO_TAG. Safe — never touches user data."""
    deleted = []
    errors = []

    # Delete in reverse dependency order
    doctypes_to_clean = [
        "Hotel Payment",
        "Hotel Folio",
        "Hotel Stay",
        "Hotel Housekeeping",
        "Hotel Reservation",
        "Hotel Package",
        "Hotel Customer",
        "Hotel Room",
        "Hotel Service",
        "Hotel Room Type",
        "Hotel Family Type",
        "Hotel Customer Category",
    ]

    for doctype in doctypes_to_clean:
        try:
            records = frappe.get_all(doctype, filters={"_user_tags": ["like", f"%{DEMO_TAG}%"]}, pluck="name")
            for name in records:
                try:
                    doc = frappe.get_doc(doctype, name)
                    if doc.docstatus == 1:
                        doc.cancel()
                    frappe.delete_doc(doctype, name, ignore_missing=True, force=True)
                    deleted.append(f"{doctype}: {name}")
                except Exception as e:
                    errors.append(f"{doctype} {name}: {str(e)}")
        except Exception as e:
            errors.append(f"Listing {doctype}: {str(e)}")

    frappe.db.commit()
    return {
        "success": True,
        "deleted": deleted,
        "errors": errors,
        "message": f"Deleted {len(deleted)} demo records"
    }


def _tag(doc):
    """Add demo tag to a document."""
    try:
        tags = (doc.get("_user_tags") or "").strip()
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if DEMO_TAG not in tag_list:
            tag_list.append(DEMO_TAG)
            frappe.db.set_value(doc.doctype, doc.name, "_user_tags", ",".join(tag_list))
    except Exception:
        pass


def _exists(doctype, name):
    return frappe.db.exists(doctype, name)


def _create_customer_categories(created):
    for cat in ["Individual", "Family", "Corporate", "VIP", "Agency", "Group"]:
        if not _exists("Hotel Customer Category", cat):
            doc = frappe.get_doc({"doctype": "Hotel Customer Category", "category_name": cat})
            doc.insert(ignore_permissions=True)
            _tag(doc)
            created.append(f"Hotel Customer Category: {cat}")


def _create_family_types(created):
    for ft in ["Single", "Couple", "Family", "Large Family", "Group"]:
        if not _exists("Hotel Family Type", ft):
            doc = frappe.get_doc({"doctype": "Hotel Family Type", "type_name": ft})
            doc.insert(ignore_permissions=True)
            _tag(doc)
            created.append(f"Hotel Family Type: {ft}")


def _create_room_types(created):
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
            doc = frappe.get_doc({"doctype": "Hotel Room Type", "active": 1, **t})
            doc.insert(ignore_permissions=True)
            _tag(doc)
            created.append(f"Hotel Room Type: {t['room_type']}")


def _create_rooms(created):
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
            doc = frappe.get_doc({"doctype": "Hotel Room", "status": "Available", "active": 1, **r})
            doc.insert(ignore_permissions=True)
            _tag(doc)
            created.append(f"Hotel Room: {r['room_number']}")


def _create_services(created):
    services = [
        {"service_name": "Breakfast",   "service_category": "Food & Beverage", "rate": 15},
        {"service_name": "Lunch",        "service_category": "Food & Beverage", "rate": 20},
        {"service_name": "Dinner",       "service_category": "Food & Beverage", "rate": 25},
        {"service_name": "Restaurant",   "service_category": "Food & Beverage", "rate": 0},
        {"service_name": "Spa",          "service_category": "Spa & Wellness",  "rate": 60},
        {"service_name": "Laundry",      "service_category": "Laundry",         "rate": 10},
        {"service_name": "Transport",    "service_category": "Transport",        "rate": 30},
        {"service_name": "Horse Riding", "service_category": "Activities",       "rate": 45},
        {"service_name": "Extra Bed",    "service_category": "Accommodation",    "rate": 20},
    ]
    for s in services:
        if not _exists("Hotel Service", s["service_name"]):
            doc = frappe.get_doc({"doctype": "Hotel Service", "active": 1, **s})
            doc.insert(ignore_permissions=True)
            _tag(doc)
            created.append(f"Hotel Service: {s['service_name']}")


def _create_packages(created):
    packages = [
        {"package_name": "Room Only",        "package_code": "RO",  "items": []},
        {"package_name": "Bed & Breakfast",  "package_code": "BB",  "items": [{"service": "Breakfast", "quantity": 1, "rate": 15}]},
        {"package_name": "Half Board",       "package_code": "HB",  "items": [{"service": "Breakfast", "quantity": 1, "rate": 15}, {"service": "Dinner", "quantity": 1, "rate": 25}]},
        {"package_name": "Full Board",       "package_code": "FB",  "items": [{"service": "Breakfast", "quantity": 1, "rate": 15}, {"service": "Lunch", "quantity": 1, "rate": 20}, {"service": "Dinner", "quantity": 1, "rate": 25}]},
        {"package_name": "Family Weekend",   "package_code": "FW",  "items": [{"service": "Breakfast", "quantity": 1, "rate": 15}, {"service": "Dinner", "quantity": 1, "rate": 25}, {"service": "Horse Riding", "quantity": 1, "rate": 45}]},
        {"package_name": "Adventure Package","package_code": "ADV", "items": [{"service": "Breakfast", "quantity": 1, "rate": 15}, {"service": "Horse Riding", "quantity": 2, "rate": 45}, {"service": "Transport", "quantity": 1, "rate": 30}]},
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
            _tag(doc)
            created.append(f"Hotel Package: {p['package_name']}")


def _create_customers(created):
    customers = [
        {"first_name": "Ahmed",  "last_name": "Ben Ali",   "phone": "+216 22 000 001", "email": "ahmed@demo.com",   "nationality": "Tunisian",  "customer_category": "Individual"},
        {"first_name": "Sophie", "last_name": "Martin",    "phone": "+33 6 00 000 002","email": "sophie@demo.com",  "nationality": "French",    "customer_category": "Family",    "family_type": "Family"},
        {"first_name": "John",   "last_name": "Smith",     "phone": "+1 555 000 003",  "email": "john@demo.com",    "nationality": "American",  "customer_category": "VIP"},
        {"first_name": "Fatima", "last_name": "Al Rashid", "phone": "+971 50 000 004", "email": "fatima@demo.com",  "nationality": "Emirati",   "customer_category": "Corporate"},
        {"first_name": "Carlos", "last_name": "Rodriguez", "phone": "+34 600 000 005", "email": "carlos@demo.com",  "nationality": "Spanish",   "customer_category": "Agency"},
    ]
    for c in customers:
        if not frappe.db.exists("Hotel Customer", {"first_name": c["first_name"], "last_name": c["last_name"]}):
            doc = frappe.get_doc({"doctype": "Hotel Customer", **c})
            doc.insert(ignore_permissions=True)
            _tag(doc)
            created.append(f"Hotel Customer: {c['first_name']} {c['last_name']}")


def _get_customer(first_name, last_name):
    return frappe.db.get_value("Hotel Customer", {"first_name": first_name, "last_name": last_name}, "name")


def _create_reservations(created):
    t = getdate(today())

    c1 = _get_customer("Ahmed", "Ben Ali")
    c2 = _get_customer("Sophie", "Martin")
    c3 = _get_customer("John", "Smith")
    c4 = _get_customer("Fatima", "Al Rashid")
    c5 = _get_customer("Carlos", "Rodriguez")

    reservations = [
        {
            "customer": c1, "arrival_date": add_days(t, 10), "departure_date": add_days(t, 13),
            "status": "Draft", "package": "Room Only",
            "rooms": [{"room": "103", "adults": 1, "rate": 110}],
            "families": [{"family_type": "Single", "adults": 1}],
            "submit": False
        },
        {
            "customer": c2, "arrival_date": add_days(t, 3), "departure_date": add_days(t, 7),
            "status": "Draft", "package": "Bed & Breakfast",
            "rooms": [{"room": "105", "adults": 2, "children": 2, "rate": 180}],
            "families": [{"family_type": "Family", "adults": 2, "children": 2}],
            "submit": True
        },
        {
            "customer": c3, "arrival_date": add_days(t, 5), "departure_date": add_days(t, 8),
            "status": "Draft", "package": "Half Board",
            "rooms": [{"room": "203", "adults": 2, "rate": 300}],
            "families": [{"family_type": "Couple", "adults": 2}],
            "submit": True, "advance": 300
        },
        {
            "customer": c5, "arrival_date": add_days(t, 15), "departure_date": add_days(t, 20),
            "status": "Draft", "package": "Full Board",
            "rooms": [{"room": "101", "adults": 1, "rate": 80}, {"room": "102", "adults": 2, "rate": 120}],
            "families": [{"family_type": "Single", "adults": 1}, {"family_type": "Couple", "adults": 2}],
            "submit": True
        },
        {
            "customer": c4, "arrival_date": add_days(t, -1), "departure_date": add_days(t, 3),
            "status": "Draft", "package": "Family Weekend",
            "rooms": [{"room": "204", "adults": 2, "children": 2, "rate": 180}],
            "families": [{"family_type": "Family", "adults": 2, "children": 2, "infants": 1}],
            "submit": True, "checkin": True
        },
    ]

    for res_data in reservations:
        submit = res_data.pop("submit", False)
        advance = res_data.pop("advance", None)
        do_checkin = res_data.pop("checkin", False)
        rooms = res_data.pop("rooms", [])
        families = res_data.pop("families", [])

        # Check duplicate
        existing = frappe.db.get_value("Hotel Reservation", {
            "customer": res_data["customer"],
            "arrival_date": str(res_data["arrival_date"])
        }, "name")
        if existing:
            continue

        doc = frappe.get_doc({
            "doctype": "Hotel Reservation",
            "booking_date": today(),
            **res_data,
            "rooms": [{"doctype": "Hotel Reservation Room", **r} for r in rooms],
            "families": [{"doctype": "Hotel Reservation Guest", **f} for f in families],
        })
        doc.insert(ignore_permissions=True)
        _tag(doc)
        created.append(f"Hotel Reservation: {doc.name}")

        if submit:
            doc.submit()

        if advance and doc.docstatus == 1:
            pay = frappe.get_doc({
                "doctype": "Hotel Payment",
                "reservation": doc.name,
                "customer": doc.customer,
                "payment_date": today(),
                "payment_method": "Card",
                "payment_type": "Advance Payment",
                "amount": advance,
            })
            pay.insert(ignore_permissions=True)
            pay.submit()
            _tag(pay)
            created.append(f"Hotel Payment: {pay.name}")

        if do_checkin and doc.docstatus == 1:
            from hotel_pms.api.checkin import checkin
            result = checkin(doc.name)
            if result.get("stays"):
                stay_name = result["stays"][0]
                # Tag the stay
                stay_doc = frappe.get_doc("Hotel Stay", stay_name)
                _tag(stay_doc)
                created.append(f"Hotel Stay: {stay_name}")
                # Add a folio charge
                folio = frappe.db.get_value("Hotel Folio", {"stay": stay_name}, "name")
                if folio:
                    folio_doc = frappe.get_doc("Hotel Folio", folio)
                    _tag(folio_doc)
                    folio_doc.append("items", {
                        "date": today(), "service": "Spa",
                        "description": "Spa - demo", "quantity": 1, "rate": 60, "amount": 60
                    })
                    folio_doc.save(ignore_permissions=True)
