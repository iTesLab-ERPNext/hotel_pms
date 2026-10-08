import frappe
from frappe import _
from frappe.utils import now_datetime

@frappe.whitelist()
def checkin(reservation):
    """Process check-in for a reservation."""
    res = frappe.get_doc("Hotel Reservation", reservation)

    if res.status != "Confirmed":
        frappe.throw(_("Reservation must be Confirmed to check in. Current status: {0}").format(res.status))

    if not res.rooms:
        frappe.throw(_("No rooms assigned to this reservation"))

    stays = []
    for room_row in res.rooms:
        # Create stay
        stay = frappe.get_doc({
            "doctype": "Hotel Stay",
            "reservation": reservation,
            "customer": res.customer,
            "room": room_row.room,
            "checkin_date": now_datetime(),
            "expected_checkout": res.departure_date,
            "status": "Active"
        })
        stay.insert(ignore_permissions=True)

        # Create folio
        folio = frappe.get_doc({
            "doctype": "Hotel Folio",
            "reservation": reservation,
            "stay": stay.name,
            "customer": res.customer,
            "room": room_row.room,
            "folio_date": frappe.utils.today(),
            "status": "Open"
        })

        # Add room charge
        folio.append("items", {
            "date": frappe.utils.today(),
            "service": None,
            "description": f"Room {room_row.room} - {room_row.number_of_nights} Night(s)",
            "quantity": room_row.number_of_nights or 1,
            "rate": room_row.rate or 0,
            "amount": room_row.amount or 0
        })
        folio.insert(ignore_permissions=True)

        # Set room to Occupied
        frappe.db.set_value("Hotel Room", room_row.room, "status", "Occupied")
        stays.append(stay.name)

    # Update reservation status
    res.db_set("status", "Checked In")

    return {"success": True, "stays": stays}
