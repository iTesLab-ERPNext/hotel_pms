"""
Automated tests for Hotel PMS.

Run with: bench run-tests --app hotel_pms --module hotel_pms.tests.test_hotel_pms
"""

import frappe
import unittest
from frappe.utils import nowdate, add_days

from hotel_pms.hotel import lifecycle


class TestHotelPMS(unittest.TestCase):

    def setUp(self):
        frappe.set_user("Administrator")
        self._test_records = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for doctype, name in reversed(self._test_records):
            try:
                frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
            except Exception:
                pass
        frappe.db.commit()

    def _track(self, doctype, name):
        self._test_records.append((doctype, name))
        return name

    # ── Fixtures ───────────────────────────────────────────────────────────────

    def _make_room_type(self, name="Test Room Type"):
        if not frappe.db.exists("Hotel Room Type", name):
            doc = frappe.get_doc({
                "doctype": "Hotel Room Type",
                "room_type": name,
                "code": "TST",
                "active": 1,
            }).insert(ignore_permissions=True)
            self._track("Hotel Room Type", doc.name)
        return name

    def _make_room(self, room_number="T99", room_type=None):
        room_type = room_type or self._make_room_type()
        existing = frappe.db.get_value("Hotel Room", {"room_number": room_number}, "name")
        if existing:
            return existing
        doc = frappe.get_doc({
            "doctype": "Hotel Room",
            "room_number": room_number,
            "room_name": f"Room {room_number}",
            "room_type": room_type,
            "floor": "1",
            "capacity": 2,
            "rate": 500,
            "status": "Available",
            "housekeeping_status": "Clean",
            "active": 1,
        }).insert(ignore_permissions=True)
        self._track("Hotel Room", doc.name)
        return doc.name

    def _make_customer(self, email="test.guest@hotel.test"):
        existing = frappe.db.get_value("Hotel Customer", {"email": email}, "name")
        if existing:
            return existing
        doc = frappe.get_doc({
            "doctype": "Hotel Customer",
            "full_name": "Test Guest",
            "email": email,
            "customer_category": "Individual",
            "active": 1,
        }).insert(ignore_permissions=True)
        self._track("Hotel Customer", doc.name)
        return doc.name

    def _make_reservation(self, customer=None, room=None,
                          arrival=None, departure=None, status="Confirmed"):
        customer  = customer  or self._make_customer()
        room      = room      or self._make_room()
        arrival   = arrival   or add_days(nowdate(), 1)
        departure = departure or add_days(nowdate(), 3)
        doc = frappe.get_doc({
            "doctype": "Hotel Reservation",
            "customer": customer,
            "booking_date": nowdate(),
            "arrival_date": arrival,
            "departure_date": departure,
            "status": status,
            "rooms": [{"room": room, "rate": 500, "nights": 2}],
            "families": [{"adults": 2, "children": 0, "infants": 0, "family_type": "Couple"}],
        })
        doc.insert(ignore_permissions=True)
        self._track("Hotel Reservation", doc.name)
        return doc.name

    # ── Tests ──────────────────────────────────────────────────────────────────

    def test_reservation_validates_dates(self):
        """Departure before arrival should raise."""
        customer = self._make_customer()
        room     = self._make_room()
        doc = frappe.get_doc({
            "doctype": "Hotel Reservation",
            "customer": customer,
            "booking_date": nowdate(),
            "arrival_date": add_days(nowdate(), 5),
            "departure_date": add_days(nowdate(), 3),  # before arrival
            "status": "Draft",
            "rooms": [{"room": room, "rate": 500}],
            "families": [{"adults": 1, "family_type": "Single"}],
        })
        with self.assertRaises(frappe.ValidationError):
            doc.insert(ignore_permissions=True)

    def test_check_in_creates_stay_and_folio(self):
        """Check-in should create Hotel Stay + Hotel Folio."""
        room = self._make_room(room_number="T98")
        res  = self._make_reservation(room=room)

        result = lifecycle.check_in(res)
        stay_name = result["stays"][0]
        self._track("Hotel Stay", stay_name)

        # Stay created
        stay = frappe.get_doc("Hotel Stay", stay_name)
        self.assertEqual(stay.status, "Active")
        self.assertEqual(stay.room, room)

        # Room marked Occupied
        room_status = frappe.db.get_value("Hotel Room", room, "status")
        self.assertEqual(room_status, "Occupied")

        # Folio created
        folio = frappe.db.get_value("Hotel Folio", {"stay": stay_name}, "name")
        self.assertIsNotNone(folio)
        self._track("Hotel Folio", folio)

    def test_check_out(self):
        """Check-out should free the room and mark the reservation Completed."""
        room = self._make_room(room_number="T97")
        res  = self._make_reservation(room=room)

        check_in_result = lifecycle.check_in(res)
        stay_name       = check_in_result["stays"][0]
        self._track("Hotel Stay", stay_name)

        folio = frappe.db.get_value("Hotel Folio", {"stay": stay_name}, "name")
        if folio:
            self._track("Hotel Folio", folio)

        lifecycle.check_out(stay_name)

        self.assertEqual(frappe.db.get_value("Hotel Stay", stay_name, "status"), "Checked Out")
        self.assertEqual(frappe.db.get_value("Hotel Room", room, "status"), "Cleaning")
        self.assertEqual(
            frappe.db.get_value("Hotel Reservation", res, "status"), "Completed")

    def test_move_room(self):
        """Moving a guest should update stay.room and create a movement record."""
        room1 = self._make_room(room_number="T96")
        room2 = self._make_room(room_number="T95")
        res   = self._make_reservation(room=room1)

        check_in_result = lifecycle.check_in(res)
        stay_name       = check_in_result["stays"][0]
        self._track("Hotel Stay", stay_name)

        folio = frappe.db.get_value("Hotel Folio", {"stay": stay_name}, "name")
        if folio:
            self._track("Hotel Folio", folio)

        mv_result = lifecycle.move_room(stay_name, room2, reason="Upgrade")
        self._track("Hotel Room Movement", mv_result["movement"])

        self.assertEqual(frappe.db.get_value("Hotel Stay", stay_name, "room"), room2)
        self.assertEqual(frappe.db.get_value("Hotel Room", room1, "status"), "Cleaning")
        self.assertEqual(frappe.db.get_value("Hotel Room", room2, "status"), "Occupied")

    def test_folio_payment(self):
        """Payment should update folio balance."""
        room = self._make_room(room_number="T94")
        res  = self._make_reservation(room=room)
        ci   = lifecycle.check_in(res)
        stay = ci["stays"][0]
        self._track("Hotel Stay", stay)

        folio_name = frappe.db.get_value("Hotel Folio", {"stay": stay}, "name")
        self.assertIsNotNone(folio_name)
        self._track("Hotel Folio", folio_name)

        # Add a charge
        lifecycle.add_folio_charge(folio_name, "Breakfast", "Breakfast x 2",
                                   quantity=2, rate=120)

        # Pay it
        pay_result = lifecycle.create_payment(
            customer=frappe.db.get_value("Hotel Folio", folio_name, "customer"),
            amount=240,
            payment_method="Cash",
            folio=folio_name,
        )
        self._track("Hotel Payment", pay_result["payment"])

        folio_doc = frappe.get_doc("Hotel Folio", folio_name)
        self.assertAlmostEqual(float(folio_doc.total_payments), 240.0, places=1)


if __name__ == "__main__":
    unittest.main()
