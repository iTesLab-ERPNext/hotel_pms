import frappe
from frappe.utils import nowdate, getdate


@frappe.whitelist()
def confirm_reservation(reservation_name):
    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    if doc.status not in ("Pending", "Tentative"):
        frappe.throw(f"Cannot confirm reservation with status {doc.status}")
    frappe.db.set_value("Hotel Reservation", reservation_name, "status", "Confirmed")
    frappe.db.commit()
    return "Confirmed"


@frappe.whitelist()
def cancel_reservation(reservation_name, reason=None):
    doc = frappe.get_doc("Hotel Reservation", reservation_name)
    if doc.status in ("Checked In", "Checked Out"):
        frappe.throw(f"Cannot cancel a reservation that is {doc.status}")
    frappe.db.set_value("Hotel Reservation", reservation_name, {
        "status": "Cancelled",
        "cancellation_reason": reason or "",
    })
    frappe.db.commit()
    return "Cancelled"


@frappe.whitelist()
def mark_no_show(reservation_name):
    frappe.db.set_value("Hotel Reservation", reservation_name, "status", "No Show")
    frappe.db.commit()
    return "No Show"


@frappe.whitelist()
def get_arrivals(date=None):
    date = date or nowdate()
    return frappe.db.sql(
        """
        SELECT name, guest_name, arrival_date, departure_date, status, number_of_guests
        FROM `tabHotel Reservation`
        WHERE arrival_date = %s AND status IN ('Confirmed', 'Pending')
        ORDER BY guest_name
        """,
        date,
        as_dict=True,
    )


@frappe.whitelist()
def get_departures(date=None):
    date = date or nowdate()
    return frappe.db.sql(
        """
        SELECT hs.name, hs.guest_name, hs.room, hs.checkin_date, hs.expected_checkout
        FROM `tabHotel Stay` hs
        WHERE hs.expected_checkout = %s AND hs.status = 'Checked In'
        ORDER BY hs.guest_name
        """,
        date,
        as_dict=True,
    )


@frappe.whitelist()
def get_in_house(date=None):
    date = date or nowdate()
    return frappe.db.sql(
        """
        SELECT hs.name, hs.guest_name, hs.room, hs.checkin_date, hs.expected_checkout,
               hrt.room_type_name
        FROM `tabHotel Stay` hs
        LEFT JOIN `tabHotel Room` hr ON hr.name = hs.room
        LEFT JOIN `tabHotel Room Type` hrt ON hrt.name = hr.room_type
        WHERE hs.status = 'Checked In'
        ORDER BY hs.room
        """,
        as_dict=True,
    )
