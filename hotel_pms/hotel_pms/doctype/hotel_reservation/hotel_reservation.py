import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, add_days, getdate, today

class HotelReservation(Document):
    def validate(self):
        self.validate_dates()
        self.calculate_nights()
        self.calculate_guests()
        self.calculate_room_charges()
        self.check_room_availability()

    def validate_dates(self):
        if self.arrival_date and self.departure_date:
            if getdate(self.departure_date) <= getdate(self.arrival_date):
                frappe.throw("Departure Date must be after Arrival Date")

    def calculate_nights(self):
        if self.arrival_date and self.departure_date:
            self.number_of_nights = date_diff(self.departure_date, self.arrival_date)
            self.number_of_days = self.number_of_nights + 1

    def calculate_guests(self):
        self.number_of_families = len(self.families) if self.families else 0
        self.total_adults = sum(f.adults or 0 for f in self.families) if self.families else 0
        self.total_children = sum(f.children or 0 for f in self.families) if self.families else 0
        self.total_infants = sum(f.infants or 0 for f in self.families) if self.families else 0
        self.total_guests = self.total_adults + self.total_children + self.total_infants

        for f in self.families:
            f.total_guests = (f.adults or 0) + (f.children or 0) + (f.infants or 0)

    def calculate_room_charges(self):
        nights = self.number_of_nights or 0
        total = 0
        for room in self.rooms:
            room.number_of_nights = nights
            room.amount = (room.rate or 0) * nights
            total += room.amount
        self.total_room_charges = total
        self.total_amount = total
        self.balance = self.total_amount - (self.advance_payment or 0)

    def check_room_availability(self):
        if self.status in ("Draft",):
            return
        for room_row in self.rooms:
            if not room_row.room:
                continue
            self._validate_room_available(room_row.room)

    def _validate_room_available(self, room):
        conflicts = frappe.db.sql("""
            SELECT r.parent
            FROM `tabHotel Reservation Room` r
            JOIN `tabHotel Reservation` res ON res.name = r.parent
            WHERE r.room = %(room)s
            AND res.name != %(name)s
            AND res.status NOT IN ('Cancelled', 'Checked Out')
            AND res.arrival_date < %(departure)s
            AND res.departure_date > %(arrival)s
        """, {
            "room": room,
            "name": self.name,
            "arrival": self.arrival_date,
            "departure": self.departure_date
        }, as_dict=True)

        if conflicts:
            frappe.throw(f"Room {room} is already booked for the selected dates (Reservation: {conflicts[0].parent})")

    def on_submit(self):
        self.status = "Confirmed"
        self.db_set("status", "Confirmed")
        for room_row in self.rooms:
            if room_row.room:
                frappe.db.set_value("Hotel Room", room_row.room, "status", "Reserved")

    def on_cancel(self):
        self.status = "Cancelled"
        for room_row in self.rooms:
            if room_row.room:
                frappe.db.set_value("Hotel Room", room_row.room, "status", "Available")
