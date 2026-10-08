"""
Automated tests for Hotel PMS.

Run with: bench run-tests --app hotel_pms --module hotel_pms.tests.test_hotel_pms
"""

import frappe
import unittest
from frappe.utils import nowdate, add_days, now_datetime


class TestHotelPMS(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        frappe.set_user("Administrator")
        self._test_records = []

    def tearDown(self):
        """Delete test records created during tests."""
        frappe.set_user("Administrator")
        for doctype, name in reversed(self._test_records):
            try:
                frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
            except Exception:
                pass
        frappe.db.commit()

    def _track(self, doctype, name):
        """Register a record for cleanup."""
        self._test_records.append((doctype, name))
        return name

    # ─── Setup Helpers ────────────────────────────────────────────────────────

    def _make_room_type(self, name="Test Room Type"):
        if frappe.db.exists("Hotel Room Type", name):
            return name
        doc = frappe.get_doc({
            "doctype": "Hotel Room Type",
            "room_type": name,
            "code": "TST",
            "capacity_adults": 2,
            "base_price": 500,
            "active": 1,
        }).insert(ignore_permissions=True)
        self._track("Hotel Room Type", doc.name)
        return doc.name

    def _make_room(self, room_number, room_type=None):
        if room_type is None:
            room_type = self._make_room_type()
        if frappe.db.exists("Hotel Room", room_number):
            return room_number
        doc = frappe.get_doc({
            "doctype": "Hotel Room",
            "room_number": room_number,
            "room_type": room_type,
            "floor": "1",
            "status": "Available",
            "housekeeping_status": "Clean",
            "active": 1,
        }).insert(ignore_permissions=True)
        self._track("Hotel Room", doc.name)
        return doc.name

    def _make_customer(self, first_name="Test", last_name="Guest"):
        doc = frappe.get_doc({
            "doctype": "Hotel Customer",
            "first_name": first_name,
            "last_name": last_name,
            "active": 1,
        }).insert(ignore_permissions=True)
        self._track("Hotel Customer", doc.name)
        return doc.name

    def _make_reservation(self, customer=None, room=None, arrival=None, departure=None, status="Confirmed"):
        if customer is None:
            customer = self._make_customer()
        if room is None:
            room = self._make_room(f"T{len(self._test_records):03d}")
        if arrival is None:
            arrival = add_days(nowdate(), 1)
        if departure is None:
            departure = add_days(nowdate(), 4)

        room_type = frappe.db.get_value("Hotel Room", room, "room_type")
        doc = frappe.get_doc({
            "doctype": "Hotel Reservation",
            "customer": customer,
            "booking_date": nowdate(),
            "arrival_date": arrival,
            "departure_date": departure,
            "status": status,
            "rooms": [{"room": room, "room_type": room_type, "adults": 2, "rate": 500}],
            "families": [{"family_type": None, "adults": 2}],
        }).insert(ignore_permissions=True)
        self._track("Hotel Reservation", doc.name)
        return doc.name

    # ─── Tests ────────────────────────────────────────────────────────────────

    def test_create_customer(self):
        """Customer creation sets full_name correctly."""
        cust_name = self._make_customer("Ali", "Hassan")
        doc = frappe.get_doc("Hotel Customer", cust_name)
        self.assertEqual(doc.full_name, "Ali Hassan")

    def test_create_room_type(self):
        """Room type can be created with required fields."""
        rt_name = self._make_room_type("Superior Test Room")
        self.assertTrue(frappe.db.exists("Hotel Room Type", rt_name))

    def test_create_room(self):
        """Room creation links to room type correctly."""
        rt = self._make_room_type()
        room_num = "T001"
        room_name = self._make_room(room_num, rt)
        doc = frappe.get_doc("Hotel Room", room_name)
        self.assertEqual(doc.room_number, room_num)
        self.assertEqual(doc.room_type, rt)
        self.assertEqual(doc.status, "Available")

    def test_reservation_nights_calculation(self):
        """Reservation auto-calculates number of nights."""
        customer = self._make_customer()
        room = self._make_room("T002")
        arrival = add_days(nowdate(), 2)
        departure = add_days(nowdate(), 5)
        res_name = self._make_reservation(customer, room, arrival, departure)
        doc = frappe.get_doc("Hotel Reservation", res_name)
        self.assertEqual(doc.number_of_nights, 3)
        self.assertEqual(doc.number_of_days, 4)

    def test_reservation_date_validation(self):
        """Reservation rejects departure before arrival."""
        customer = self._make_customer()
        room = self._make_room("T003")
        room_type = frappe.db.get_value("Hotel Room", room, "room_type")

        with self.assertRaises(frappe.exceptions.ValidationError):
            doc = frappe.get_doc({
                "doctype": "Hotel Reservation",
                "customer": customer,
                "booking_date": nowdate(),
                "arrival_date": add_days(nowdate(), 5),
                "departure_date": add_days(nowdate(), 2),  # departure before arrival
                "status": "Confirmed",
                "rooms": [{"room": room, "room_type": room_type, "adults": 1, "rate": 500}],
            })
            doc.insert(ignore_permissions=True)

    def test_double_booking_prevention(self):
        """Reservations for overlapping dates on same room are rejected."""
        customer1 = self._make_customer("Guest", "One")
        customer2 = self._make_customer("Guest", "Two")
        room = self._make_room("T004")
        room_type = frappe.db.get_value("Hotel Room", room, "room_type")

        # First reservation
        arrival1 = add_days(nowdate(), 10)
        departure1 = add_days(nowdate(), 15)
        self._make_reservation(customer1, room, arrival1, departure1)

        # Overlapping second reservation should fail
        with self.assertRaises(frappe.exceptions.ValidationError):
            doc = frappe.get_doc({
                "doctype": "Hotel Reservation",
                "customer": customer2,
                "booking_date": nowdate(),
                "arrival_date": add_days(nowdate(), 12),
                "departure_date": add_days(nowdate(), 17),
                "status": "Confirmed",
                "rooms": [{"room": room, "room_type": room_type, "adults": 1, "rate": 500}],
            })
            doc.insert(ignore_permissions=True)

    def test_check_in(self):
        """Check-in creates stay, updates room status, creates folio."""
        customer = self._make_customer()
        room = self._make_room("T005")
        arrival = add_days(nowdate(), -1)
        departure = add_days(nowdate(), 3)
        res_name = self._make_reservation(customer, room, arrival, departure, "Confirmed")

        result = frappe.call(
            "hotel_pms.api.hotel_api.check_in",
            reservation=res_name
        )
        self.assertTrue(result.get("success"))
        self.assertTrue(len(result.get("stays", [])) > 0)

        stay_name = result["stays"][0]
        self._track("Hotel Stay", stay_name)

        # Room should be occupied
        room_status = frappe.db.get_value("Hotel Room", room, "status")
        self.assertEqual(room_status, "Occupied")

        # Reservation should be checked in
        res_status = frappe.db.get_value("Hotel Reservation", res_name, "status")
        self.assertEqual(res_status, "Checked In")

        # Folio should exist
        folio = frappe.db.exists("Hotel Folio", {"stay": stay_name})
        self.assertTrue(folio)
        if folio:
            self._track("Hotel Folio", folio)

    def test_check_out(self):
        """Check-out updates stay, room, and reservation status."""
        customer = self._make_customer()
        room = self._make_room("T006")
        arrival = add_days(nowdate(), -2)
        departure = add_days(nowdate(), 2)
        res_name = self._make_reservation(customer, room, arrival, departure, "Confirmed")

        ci_result = frappe.call("hotel_pms.api.hotel_api.check_in", reservation=res_name)
        stay_name = ci_result["stays"][0]
        self._track("Hotel Stay", stay_name)

        folio = frappe.db.get_value("Hotel Folio", {"stay": stay_name}, "name")
        if folio:
            self._track("Hotel Folio", folio)

        co_result = frappe.call("hotel_pms.api.hotel_api.check_out", stay_name=stay_name)
        self.assertTrue(co_result.get("success"))

        stay_status = frappe.db.get_value("Hotel Stay", stay_name, "status")
        self.assertEqual(stay_status, "Checked Out")

        room_status = frappe.db.get_value("Hotel Room", room, "status")
        self.assertEqual(room_status, "Cleaning")

    def test_room_movement(self):
        """Room movement record is created and rooms are updated correctly."""
        customer = self._make_customer()
        room1 = self._make_room("T007")
        room2 = self._make_room("T008")
        arrival = add_days(nowdate(), -1)
        departure = add_days(nowdate(), 3)
        res_name = self._make_reservation(customer, room1, arrival, departure, "Confirmed")

        ci_result = frappe.call("hotel_pms.api.hotel_api.check_in", reservation=res_name)
        stay_name = ci_result["stays"][0]
        self._track("Hotel Stay", stay_name)

        folio = frappe.db.get_value("Hotel Folio", {"stay": stay_name}, "name")
        if folio:
            self._track("Hotel Folio", folio)

        mv_result = frappe.call(
            "hotel_pms.api.hotel_api.move_room",
            stay_name=stay_name,
            new_room=room2,
            reason="Test move"
        )
        self.assertTrue(mv_result.get("success"))
        self._track("Hotel Room Movement", mv_result["movement"])

        new_room_for_stay = frappe.db.get_value("Hotel Stay", stay_name, "room")
        self.assertEqual(new_room_for_stay, room2)

        room2_status = frappe.db.get_value("Hotel Room", room2, "status")
        self.assertEqual(room2_status, "Occupied")

    def test_folio_charges(self):
        """Charges can be added to a folio and balance updates."""
        customer = self._make_customer()
        room = self._make_room("T009")
        arrival = add_days(nowdate(), -1)
        departure = add_days(nowdate(), 3)
        res_name = self._make_reservation(customer, room, arrival, departure, "Confirmed")

        ci_result = frappe.call("hotel_pms.api.hotel_api.check_in", reservation=res_name)
        stay_name = ci_result["stays"][0]
        self._track("Hotel Stay", stay_name)

        folio_name = frappe.db.get_value("Hotel Folio", {"stay": stay_name}, "name")
        self._track("Hotel Folio", folio_name)

        result = frappe.call(
            "hotel_pms.api.hotel_api.add_folio_charge",
            folio=folio_name,
            charge_type="Breakfast",
            description="Breakfast for 2",
            quantity=2,
            rate=120,
        )
        self.assertTrue(result.get("success"))

        folio_doc = frappe.get_doc("Hotel Folio", folio_name)
        charges = [i for i in folio_doc.items if i.charge_type == "Breakfast"]
        self.assertTrue(len(charges) > 0)
        self.assertEqual(charges[-1].amount, 240)

    def test_payment_creation(self):
        """Payment creation updates folio balance and status."""
        customer = self._make_customer()
        room = self._make_room("T010")
        arrival = add_days(nowdate(), -1)
        departure = add_days(nowdate(), 3)
        res_name = self._make_reservation(customer, room, arrival, departure, "Confirmed")

        ci_result = frappe.call("hotel_pms.api.hotel_api.check_in", reservation=res_name)
        stay_name = ci_result["stays"][0]
        self._track("Hotel Stay", stay_name)

        folio_name = frappe.db.get_value("Hotel Folio", {"stay": stay_name}, "name")
        self._track("Hotel Folio", folio_name)

        # Add a charge first
        frappe.call(
            "hotel_pms.api.hotel_api.add_folio_charge",
            folio=folio_name,
            charge_type="Room",
            description="Room charge",
            quantity=1,
            rate=500,
        )

        pay_result = frappe.call(
            "hotel_pms.api.hotel_api.create_payment",
            customer=customer,
            amount=500,
            payment_method="Cash",
            payment_type="Full",
            reservation=res_name,
            stay=stay_name,
            folio=folio_name,
        )
        self.assertTrue(pay_result.get("success"))
        self._track("Hotel Payment", pay_result["payment"])

        folio = frappe.get_doc("Hotel Folio", folio_name)
        self.assertGreaterEqual(folio.total_payments, 500)

    def test_seed_idempotency(self):
        """Seed function can be called twice without error or duplication."""
        from hotel_pms.setup.seed_demo_data import seed, delete_test_data

        seed()
        count_after_first = frappe.db.count("Hotel Room", {"is_test_data": 1})

        seed()
        count_after_second = frappe.db.count("Hotel Room", {"is_test_data": 1})

        self.assertEqual(count_after_first, count_after_second,
            "Second seed() call should not create duplicate rooms")

        delete_test_data()
        count_after_delete = frappe.db.count("Hotel Room", {"is_test_data": 1})
        self.assertEqual(count_after_delete, 0, "All test rooms should be deleted")


if __name__ == "__main__":
    unittest.main()
