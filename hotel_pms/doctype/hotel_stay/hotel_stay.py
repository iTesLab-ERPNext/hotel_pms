import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, now_datetime, today, getdate


class HotelStay(Document):
    def validate(self):
        self._calculate_nights()
        self._sync_financials()

    def _calculate_nights(self):
        if self.checkin_date and self.expected_checkout:
            from frappe.utils import get_datetime
            ci = get_datetime(self.checkin_date)
            co = get_datetime(self.expected_checkout)
            self.number_of_nights = (co.date() - ci.date()).days

    def _sync_financials(self):
        """Pull live totals from the linked folio."""
        if not self.folio:
            return
        try:
            folio = frappe.get_doc("Hotel Folio", self.folio)
            self.total_room_charges  = folio.room_charges
            self.total_extra_charges = folio.extra_charges
            self.total_charges       = folio.total_charges
            self.total_paid          = folio.total_payments
            self.balance_due         = folio.balance_due
        except frappe.DoesNotExistError:
            pass

    def checkout(self):
        """Perform checkout — close folio, free room."""
        if self.stay_status == "Checked Out":
            frappe.throw(_("Stay is already checked out"))

        self.stay_status    = "Checked Out"
        self.actual_checkout = now_datetime()

        # Free the room
        room = frappe.get_doc("Hotel Room", self.room)
        room.set_dirty()

        # Close folio
        if self.folio:
            folio = frappe.get_doc("Hotel Folio", self.folio)
            folio.folio_status = "Closed"
            folio.save(ignore_permissions=True)

        # Update reservation
        if self.reservation:
            res = frappe.get_doc("Hotel Reservation", self.reservation)
            res.reservation_status = "Checked Out"
            res.save(ignore_permissions=True)

        self.save(ignore_permissions=True)
