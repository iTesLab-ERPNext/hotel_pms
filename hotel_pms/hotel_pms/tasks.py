import frappe
from frappe.utils import today, nowdate


def auto_no_show():
    """Mark overdue Confirmed reservations as No Show."""
    reservations = frappe.get_all(
        "Hotel Reservation",
        filters={"status": "Confirmed", "arrival_date": ["<", today()]},
        fields=["name"],
    )
    for r in reservations:
        frappe.db.set_value("Hotel Reservation", r.name, "status", "No Show")
    if reservations:
        frappe.db.commit()


def auto_post_room_charges():
    """Post daily room charges to all in-house folios."""
    from hotel_pms.hotel_pms.api.folio import post_room_charge

    stays = frappe.get_all(
        "Hotel Stay",
        filters={"status": "Checked In"},
        fields=["name"],
    )
    for stay in stays:
        try:
            folio = frappe.get_value("Hotel Folio", {"stay": stay.name}, "name")
            if folio:
                post_room_charge(folio)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Room charge failed for stay {stay.name}")


def update_room_statuses():
    """Sync room status: mark Occupied rooms as Available if stay checked out."""
    checked_out_rooms = frappe.db.sql(
        """
        SELECT DISTINCT hr.name
        FROM `tabHotel Room` hr
        WHERE hr.status = 'Occupied'
          AND NOT EXISTS (
              SELECT 1 FROM `tabHotel Stay` hs
              WHERE hs.room = hr.name AND hs.status = 'Checked In'
          )
        """,
        as_dict=True,
    )
    for room in checked_out_rooms:
        frappe.db.set_value("Hotel Room", room.name, "status", "Available")
    if checked_out_rooms:
        frappe.db.commit()
