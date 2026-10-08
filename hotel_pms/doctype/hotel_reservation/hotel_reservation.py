import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, add_days, today, getdate


class HotelReservation(Document):
    # ── Lifecycle ────────────────────────────────────────────────────────────

    def validate(self):
        self._validate_dates()
        self._calculate_nights()
        self._calculate_guest_totals()
        self._calculate_room_totals()
        self._validate_room_availability()

    def before_submit(self):
        if self.reservation_status not in ("Confirmed", "Deposit Paid", "Checked In", "In House", "Checked Out", "Completed"):
            frappe.throw(_("Cannot submit a reservation in status: {0}").format(self.reservation_status))

    # ── Validation helpers ───────────────────────────────────────────────────

    def _validate_dates(self):
        if not self.arrival_date or not self.departure_date:
            return
        if getdate(self.departure_date) <= getdate(self.arrival_date):
            frappe.throw(_("Departure Date must be after Arrival Date"))

    def _calculate_nights(self):
        if self.arrival_date and self.departure_date:
            nights = date_diff(self.departure_date, self.arrival_date)
            self.number_of_nights = nights
            self.number_of_days = nights + 1

    def _calculate_guest_totals(self):
        total_adults = total_children = total_infants = 0
        for fam in self.families or []:
            total_adults   += int(fam.adults   or 0)
            total_children += int(fam.children or 0)
            total_infants  += int(fam.infants  or 0)
        if total_adults or total_children:
            self.total_adults   = total_adults
            self.total_children = total_children
            self.total_infants  = total_infants
            self.total_guests   = total_adults + total_children + total_infants

    def _calculate_room_totals(self):
        nights = self.number_of_nights or 0
        total = 0.0
        for room in self.rooms or []:
            room.guests = int(room.adults or 0) + int(room.children or 0) + int(room.infants or 0)
            room_nights = nights
            if room.checkin and room.checkout:
                room_nights = date_diff(room.checkout, room.checkin)
            room.nights = room_nights
            gross = float(room.rate or 0) * room_nights
            disc  = gross * float(room.discount or 0) / 100
            room.total = gross - disc
            total += room.total
        self.total_room_charges = total
        self.total_amount = total
        advance = float(self.advance_paid or 0)
        self.balance_due = self.total_amount - advance

    def _validate_room_availability(self):
        from hotel_pms.api.availability import check_room_conflict
        for room_row in self.rooms or []:
            if not room_row.room:
                continue
            conflict = check_room_conflict(
                room=room_row.room,
                arrival=self.arrival_date,
                departure=self.departure_date,
                exclude_reservation=self.name,
            )
            if conflict:
                frappe.throw(
                    _("Room {0} is already booked from {1} to {2} (Reservation {3})").format(
                        room_row.room, conflict["arrival_date"], conflict["departure_date"], conflict["name"]
                    )
                )

    # ── Business actions ─────────────────────────────────────────────────────

    def confirm(self):
        self.reservation_status = "Confirmed"
        self.save()

    def cancel_reservation(self, reason=None, charge=0):
        self.reservation_status = "Cancelled"
        self.cancellation_date   = today()
        self.cancellation_reason = reason or ""
        self.cancellation_charge = charge
        for room_row in self.rooms or []:
            room_row.status = "Cancelled"
            room_doc = frappe.get_doc("Hotel Room", room_row.room)
            if room_doc.status == "Reserved":
                room_doc.set_available()
        self.save()

    def mark_no_show(self):
        self.reservation_status = "No Show"
        for room_row in self.rooms or []:
            room_row.status = "Cancelled"
            try:
                room_doc = frappe.get_doc("Hotel Room", room_row.room)
                if room_doc.status == "Reserved":
                    room_doc.set_available()
            except frappe.DoesNotExistError:
                pass
        self.save()
