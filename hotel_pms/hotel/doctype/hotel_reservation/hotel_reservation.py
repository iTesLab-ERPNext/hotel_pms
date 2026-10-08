import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, getdate, nowdate


class HotelReservation(Document):
    def validate(self):
        self.validate_dates()
        self.calculate_nights()
        self.calculate_family_totals()
        self.calculate_room_totals()
        self.check_room_availability()

    def validate_dates(self):
        if self.arrival_date and self.departure_date:
            if getdate(self.departure_date) <= getdate(self.arrival_date):
                frappe.throw(_("Departure date must be after arrival date"))

    def calculate_nights(self):
        if self.arrival_date and self.departure_date:
            self.number_of_nights = date_diff(self.departure_date, self.arrival_date)
            if self.number_of_nights <= 0:
                frappe.throw(_("Number of nights must be greater than zero"))
            self.number_of_days = self.number_of_nights + 1

    def calculate_family_totals(self):
        total_adults = 0
        total_children = 0
        total_infants = 0
        num_families = 0
        if self.families:
            for f in self.families:
                f.total_guests = (f.adults or 0) + (f.children or 0) + (f.infants or 0)
                total_adults += f.adults or 0
                total_children += f.children or 0
                total_infants += f.infants or 0
                num_families += 1
        self.number_of_families = num_families
        self.total_adults = total_adults
        self.total_children = total_children
        self.total_infants = total_infants
        self.total_guests = total_adults + total_children + total_infants

    def calculate_room_totals(self):
        for r in (self.rooms or []):
            r.total_guests = (r.adults or 0) + (r.children or 0) + (r.infants or 0)
            r.amount = (r.rate or 0) * (r.nights or self.number_of_nights or 0)
            if r.room and not r.room_type:
                r.room_type = frappe.db.get_value("Hotel Room", r.room, "room_type")

    def check_room_availability(self):
        if not self.rooms or self.status in ("Cancelled", "No Show"):
            return

        for res_room in self.rooms:
            if not res_room.room:
                continue

            conflicts = frappe.db.sql("""
                SELECT r.name
                FROM `tabHotel Reservation Room` rr
                JOIN `tabHotel Reservation` r ON r.name = rr.parent
                WHERE rr.room = %s
                  AND r.name != %s
                  AND r.status NOT IN ('Cancelled', 'No Show', 'Completed')
                  AND r.arrival_date < %s
                  AND r.departure_date > %s
            """, (res_room.room, self.name or "NEW", self.departure_date, self.arrival_date))

            if conflicts:
                frappe.throw(_(
                    "Room {0} is already reserved for the selected dates"
                ).format(res_room.room))
