import frappe
from frappe.model.document import Document
from frappe.utils import date_diff


class HotelReservation(Document):
    def validate(self):
        if self.arrival_date and self.departure_date:
            nights = date_diff(self.departure_date, self.arrival_date)
            if nights <= 0:
                frappe.throw("Departure date must be after arrival date")
            self.number_of_nights = nights

    def on_submit(self):
        frappe.db.set_value("Hotel Reservation", self.name, "status", "Confirmed")
