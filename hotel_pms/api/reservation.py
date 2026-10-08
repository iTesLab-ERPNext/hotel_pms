import frappe
from frappe import _
from frappe.utils import today, getdate


@frappe.whitelist()
def confirm_reservation(reservation_name):
    res = frappe.get_doc("Hotel Reservation", reservation_name)
    res.confirm()
    return {"status": res.reservation_status}


@frappe.whitelist()
def cancel_reservation(reservation_name, reason, charge=0):
    res = frappe.get_doc("Hotel Reservation", reservation_name)
    res.cancel_reservation(reason, float(charge))
    return {"status": res.reservation_status}


@frappe.whitelist()
def mark_no_show(reservation_name):
    res = frappe.get_doc("Hotel Reservation", reservation_name)
    res.mark_no_show()
    return {"status": res.reservation_status}


@frappe.whitelist()
def get_arrivals(date=None):
    """Return all reservations arriving on a given date."""
    if not date:
        date = today()
    date = str(getdate(date))

    results = frappe.db.sql(
        """
        SELECT res.name, res.customer, res.customer_name,
               res.arrival_date, res.departure_date,
               res.number_of_nights, res.total_guests,
               res.reservation_status, res.number_of_families
        FROM `tabHotel Reservation` res
        WHERE DATE(res.arrival_date) = %s
          AND res.reservation_status IN ('Confirmed','Deposit Paid')
        ORDER BY res.checkin_time
        """,
        date,
        as_dict=True,
    )
    return results


@frappe.whitelist()
def get_departures(date=None):
    """Return all stays due to check out on a given date."""
    if not date:
        date = today()
    date = str(getdate(date))

    results = frappe.db.sql(
        """
        SELECT stay.name, stay.guest, stay.guest_name, stay.room,
               stay.checkin_date, stay.expected_checkout,
               stay.balance_due, stay.folio, stay.stay_status
        FROM `tabHotel Stay` stay
        WHERE DATE(stay.expected_checkout) = %s
          AND stay.stay_status IN ('In House','Extended')
        ORDER BY stay.expected_checkout
        """,
        date,
        as_dict=True,
    )
    return results


@frappe.whitelist()
def get_in_house(date=None):
    """Return all stays currently in-house on a given date."""
    if not date:
        date = today()

    results = frappe.db.sql(
        """
        SELECT stay.name, stay.guest, stay.guest_name, stay.room,
               stay.checkin_date, stay.expected_checkout,
               stay.number_of_nights, stay.balance_due, stay.folio
        FROM `tabHotel Stay` stay
        WHERE stay.stay_status IN ('In House','Extended')
          AND DATE(stay.checkin_date) <= %s
          AND DATE(stay.expected_checkout) >= %s
        ORDER BY stay.room
        """,
        (date, date),
        as_dict=True,
    )
    return results
