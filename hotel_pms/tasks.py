"""Scheduled tasks for Hotel PMS."""
import frappe
from frappe.utils import today, now_datetime, getdate, add_days


def auto_no_show():
    """Mark overdue Confirmed reservations as No Show."""
    yesterday = str(add_days(today(), -1))
    overdue = frappe.get_all(
        "Hotel Reservation",
        filters={
            "reservation_status": ["in", ["Confirmed", "Deposit Paid"]],
            "arrival_date": ["<=", yesterday],
        },
        fields=["name"],
    )
    for res in overdue:
        try:
            doc = frappe.get_doc("Hotel Reservation", res.name)
            doc.mark_no_show()
            frappe.logger().info(f"Auto No Show: {res.name}")
        except Exception as e:
            frappe.logger().error(f"Auto No Show failed for {res.name}: {e}")


def auto_post_room_charges():
    """Post daily room charges to all in-house folios."""
    today_date = today()
    stays = frappe.get_all(
        "Hotel Stay",
        filters={"stay_status": ["in", ["In House", "Extended"]]},
        fields=["name", "folio", "room", "rate_per_night"],
    )
    for stay in stays:
        if not stay.folio:
            continue
        # Check if charge already posted today
        already_posted = frappe.db.exists(
            "Hotel Folio Item",
            {
                "parent": stay.folio,
                "charge_type": "Room",
                "date": today_date,
                "voided": 0,
            },
        )
        if already_posted:
            continue
        try:
            from hotel_pms.api.folio import post_room_charge
            post_room_charge(stay.name, date=today_date)
        except Exception as e:
            frappe.logger().error(f"Room charge post failed for stay {stay.name}: {e}")


def update_room_statuses():
    """Hourly: mark rooms as Dirty if their stay checked out since last run."""
    # Rooms that are Occupied but their stay checked out
    checked_out = frappe.db.sql(
        """
        SELECT r.name
        FROM `tabHotel Room` r
        WHERE r.status = 'Occupied'
          AND NOT EXISTS (
              SELECT 1 FROM `tabHotel Stay` s
              WHERE s.room = r.name AND s.stay_status IN ('In House','Extended')
          )
        """,
        as_dict=True,
    )
    for room in checked_out:
        frappe.db.set_value("Hotel Room", room.name, {
            "status": "Dirty",
            "housekeeping_status": "Dirty",
            "current_guest": None,
            "current_reservation": None,
        })
