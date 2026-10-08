"""
Demo seed data for Hotel PMS.
All functions are idempotent — safe to run multiple times.
"""
import frappe
from frappe.utils import today, add_days


@frappe.whitelist()
def seed_all():
    results = []
    results += seed_room_types()
    results += seed_rooms()
    results += seed_services()
    results += seed_booking_sources()
    results += seed_customers()
    results += seed_reservations()
    return results


def _created(doctype, name):
    return {"doctype": doctype, "name": name, "action": "created"}


def _skipped(doctype, name):
    return {"doctype": doctype, "name": name, "action": "skipped"}


def seed_room_types():
    results = []
    room_types = [
        {"name": "Standard Single", "code": "STD1", "base_price": 80,  "capacity_adults": 1},
        {"name": "Standard Double", "code": "STD2", "base_price": 120, "capacity_adults": 2},
        {"name": "Superior Double", "code": "SUP2", "base_price": 150, "capacity_adults": 2},
        {"name": "Deluxe Double",   "code": "DEL2", "base_price": 200, "capacity_adults": 2},
        {"name": "Junior Suite",    "code": "JSU",  "base_price": 280, "capacity_adults": 2},
        {"name": "Executive Suite", "code": "ESU",  "base_price": 400, "capacity_adults": 2},
        {"name": "Presidential Suite","code":"PSU", "base_price": 800, "capacity_adults": 4},
    ]
    for rt in room_types:
        if frappe.db.exists("Hotel Room Type", rt["name"]):
            results.append(_skipped("Hotel Room Type", rt["name"]))
            continue
        doc = frappe.new_doc("Hotel Room Type")
        doc.update(rt)
        doc.active = 1
        doc.currency = "USD"
        doc.insert(ignore_permissions=True)
        results.append(_created("Hotel Room Type", doc.name))
    return results


def seed_rooms():
    results = []
    floors = [
        (1, ["101","102","103","104","105"], ["Standard Single","Standard Double","Standard Double","Superior Double","Superior Double"]),
        (2, ["201","202","203","204","205"], ["Standard Double","Standard Double","Deluxe Double","Deluxe Double","Junior Suite"]),
        (3, ["301","302","303","304","305"], ["Deluxe Double","Deluxe Double","Junior Suite","Executive Suite","Presidential Suite"]),
        (4, ["401","402","403","404"],       ["Junior Suite","Junior Suite","Executive Suite","Presidential Suite"]),
    ]
    for floor, numbers, types in floors:
        for num, rtype in zip(numbers, types):
            if frappe.db.exists("Hotel Room", num):
                results.append(_skipped("Hotel Room", num))
                continue
            doc = frappe.new_doc("Hotel Room")
            doc.room_number = num
            doc.room_name = f"Room {num}"
            doc.room_type = rtype
            doc.floor = floor
            doc.status = "Available"
            doc.housekeeping_status = "Clean"
            doc.active = 1
            doc.insert(ignore_permissions=True)
            results.append(_created("Hotel Room", doc.name))
    return results


def seed_services():
    results = []
    services = [
        {"service_name": "Airport Transfer", "charge_type": "Transport", "rate": 45},
        {"service_name": "Breakfast",        "charge_type": "Food",      "rate": 18},
        {"service_name": "Full Board",       "charge_type": "Food",      "rate": 55},
        {"service_name": "Mini Bar",         "charge_type": "Bar",       "rate": 25},
        {"service_name": "Laundry",          "charge_type": "Laundry",   "rate": 12},
        {"service_name": "Spa Treatment",    "charge_type": "Spa",       "rate": 90},
        {"service_name": "City Tour",        "charge_type": "Activity",  "rate": 65},
        {"service_name": "Extra Bed",        "charge_type": "Extra Bed", "rate": 30},
        {"service_name": "Late Checkout",    "charge_type": "Late Checkout","rate": 50},
        {"service_name": "Room Service",     "charge_type": "Food",      "rate": 0},
    ]
    for s in services:
        if frappe.db.exists("Hotel Service", s["service_name"]):
            results.append(_skipped("Hotel Service", s["service_name"]))
            continue
        doc = frappe.new_doc("Hotel Service")
        doc.update(s)
        doc.active = 1
        doc.insert(ignore_permissions=True)
        results.append(_created("Hotel Service", doc.name))
    return results


def seed_booking_sources():
    results = []
    sources = ["Walk-in","Phone","Email","Website","Booking.com","Expedia","Airbnb","Travel Agent","Corporate","GDS"]
    for src in sources:
        if frappe.db.exists("Hotel Booking Source", src):
            results.append(_skipped("Hotel Booking Source", src))
            continue
        doc = frappe.new_doc("Hotel Booking Source")
        doc.source_name = src
        doc.active = 1
        doc.insert(ignore_permissions=True)
        results.append(_created("Hotel Booking Source", doc.name))
    return results


def seed_customers():
    results = []
    customers = [
        {"customer_name": "Alice Johnson",  "customer_type": "Individual", "customer_group": "Individual"},
        {"customer_name": "Bob Smith",      "customer_type": "Individual", "customer_group": "Individual"},
        {"customer_name": "Carol White",    "customer_type": "Individual", "customer_group": "Individual"},
        {"customer_name": "David Brown",    "customer_type": "Individual", "customer_group": "Individual"},
        {"customer_name": "Eva Martinez",   "customer_type": "Individual", "customer_group": "Individual"},
        {"customer_name": "Acme Corp",      "customer_type": "Company",    "customer_group": "Commercial"},
        {"customer_name": "Globex Ltd",     "customer_type": "Company",    "customer_group": "Commercial"},
    ]
    for c in customers:
        if frappe.db.exists("Customer", c["customer_name"]):
            results.append(_skipped("Customer", c["customer_name"]))
            continue
        doc = frappe.new_doc("Customer")
        doc.update(c)
        doc.insert(ignore_permissions=True)
        results.append(_created("Customer", doc.name))
    return results


def seed_reservations():
    results = []
    t = today()
    reservations = [
        {
            "customer": "Alice Johnson",
            "arrival_date": add_days(t, 1),
            "departure_date": add_days(t, 4),
            "reservation_status": "Confirmed",
            "source": "Website",
            "room": "201",
        },
        {
            "customer": "Bob Smith",
            "arrival_date": add_days(t, 2),
            "departure_date": add_days(t, 5),
            "reservation_status": "Deposit Paid",
            "source": "Phone",
            "room": "301",
        },
        {
            "customer": "Carol White",
            "arrival_date": t,
            "departure_date": add_days(t, 3),
            "reservation_status": "Confirmed",
            "source": "Booking.com",
            "room": "102",
        },
    ]
    for r in reservations:
        room = r.pop("room", None)
        if frappe.db.exists("Hotel Reservation", {"customer": r["customer"], "arrival_date": ["like", str(r["arrival_date"])+"%"]}):
            results.append(_skipped("Hotel Reservation", r["customer"]))
            continue
        doc = frappe.new_doc("Hotel Reservation")
        doc.update(r)
        if room:
            doc.append("rooms", {
                "room": room,
                "checkin": r["arrival_date"],
                "checkout": r["departure_date"],
                "adults": 2,
            })
        doc.insert(ignore_permissions=True)
        results.append(_created("Hotel Reservation", doc.name))
    return results
