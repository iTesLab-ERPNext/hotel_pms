"""
Hotel PMS Tests
Run: bench run-tests --app hotel_pms
"""

import frappe
import unittest
from frappe.utils import add_days, today, getdate


class TestHotelReservation(unittest.TestCase):

    def setUp(self):
        # Ensure test customer exists
        if not frappe.db.exists("Hotel Customer Category", "Individual"):
            frappe.get_doc({"doctype": "Hotel Customer Category", "category_name": "Individual"}).insert()

        if not frappe.db.exists("Hotel Room Type", "Test Single"):
            frappe.get_doc({
                "doctype": "Hotel Room Type",
                "room_type": "Test Single",
                "code": "TST",
                "base_price": 100,
                "active": 1
            }).insert()

        if not frappe.db.exists("Hotel Room", "TEST-001"):
            frappe.get_doc({
                "doctype": "Hotel Room",
                "room_number": "TEST-001",
                "room_type": "Test Single",
                "floor": 1,
                "capacity": 1,
                "status": "Available",
                "active": 1
            }).insert()

        if not frappe.db.exists("Hotel Customer", {"first_name": "Test", "last_name": "Guest"}):
            self.customer = frappe.get_doc({
                "doctype": "Hotel Customer",
                "first_name": "Test",
                "last_name": "Guest",
                "customer_category": "Individual"
            }).insert()
        else:
            self.customer = frappe.get_doc("Hotel Customer",
                frappe.db.get_value("Hotel Customer", {"first_name": "Test", "last_name": "Guest"}, "name"))

    def _make_reservation(self, arrival_offset=5, nights=3):
        t = getdate(today())
        arrival = add_days(t, arrival_offset)
        departure = add_days(t, arrival_offset + nights)
        res = frappe.get_doc({
            "doctype": "Hotel Reservation",
            "customer": self.customer.name,
            "booking_date": today(),
            "arrival_date": arrival,
            "departure_date": departure,
            "status": "Draft",
            "rooms": [{"doctype": "Hotel Reservation Room", "room": "TEST-001", "adults": 1, "rate": 100}],
            "families": [{"doctype": "Hotel Reservation Guest", "adults": 1}]
        })
        res.insert()
        return res

    def test_reservation_date_calculation(self):
        res = self._make_reservation(nights=3)
        self.assertEqual(res.number_of_nights, 3)
        self.assertEqual(res.number_of_days, 4)
        res.delete()

    def test_invalid_dates(self):
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc({
                "doctype": "Hotel Reservation",
                "customer": self.customer.name,
                "booking_date": today(),
                "arrival_date": add_days(today(), 5),
                "departure_date": add_days(today(), 3),  # before arrival
                "rooms": [],
                "families": []
            }).insert()

    def test_customer_full_name(self):
        c = frappe.get_doc("Hotel Customer", self.customer.name)
        self.assertEqual(c.full_name, "Test Guest")

    def test_reservation_guest_total(self):
        res = self._make_reservation()
        self.assertGreaterEqual(res.total_guests, 0)
        res.delete()

    def tearDown(self):
        # Clean up test reservations
        for res in frappe.get_all("Hotel Reservation", filters={"customer": self.customer.name}):
            try:
                doc = frappe.get_doc("Hotel Reservation", res.name)
                if doc.docstatus == 1:
                    doc.cancel()
                doc.delete()
            except Exception:
                pass


class TestHotelRoom(unittest.TestCase):

    def test_room_status_values(self):
        valid_statuses = ["Available", "Reserved", "Occupied", "Cleaning", "Maintenance", "Blocked", "Out of Service"]
        meta = frappe.get_meta("Hotel Room")
        field = next((f for f in meta.fields if f.fieldname == "status"), None)
        self.assertIsNotNone(field)
        for status in valid_statuses:
            self.assertIn(status, field.options)


class TestHotelPackage(unittest.TestCase):

    def test_package_total(self):
        if frappe.db.exists("Hotel Package", "Test Package"):
            frappe.delete_doc("Hotel Package", "Test Package", force=True)

        if not frappe.db.exists("Hotel Service", "Test Service"):
            frappe.get_doc({
                "doctype": "Hotel Service",
                "service_name": "Test Service",
                "rate": 50,
                "active": 1
            }).insert()

        pkg = frappe.get_doc({
            "doctype": "Hotel Package",
            "package_name": "Test Package",
            "active": 1,
            "items": [
                {"doctype": "Hotel Package Item", "service": "Test Service", "quantity": 2, "rate": 50}
            ]
        })
        pkg.insert()
        self.assertEqual(pkg.total_price, 100)
        pkg.delete()
        frappe.delete_doc("Hotel Service", "Test Service", force=True)
