import frappe
from frappe import _
from frappe.utils import now_datetime

@frappe.whitelist()
def checkout(stay):
    """Process checkout for a stay."""
    stay_doc = frappe.get_doc("Hotel Stay", stay)

    if stay_doc.status != "Active":
        frappe.throw(_("Stay must be Active to check out. Current status: {0}").format(stay_doc.status))

    # Get folio and check balance
    folios = frappe.get_all("Hotel Folio",
        filters={"stay": stay, "status": "Open"},
        fields=["name", "balance", "total_charges", "total_payments"])

    total_balance = sum(f.balance or 0 for f in folios)

    # Close folio
    for folio in folios:
        if (folio.balance or 0) == 0:
            frappe.db.set_value("Hotel Folio", folio.name, "status", "Settled")

    # Update stay
    stay_doc.status = "Checked Out"
    stay_doc.actual_checkout = now_datetime()
    stay_doc.save(ignore_permissions=True)

    # Update room status
    frappe.db.set_value("Hotel Room", stay_doc.room, "status", "Cleaning")

    # Update reservation
    if stay_doc.reservation:
        frappe.db.set_value("Hotel Reservation", stay_doc.reservation, "status", "Checked Out")

    # Create housekeeping
    from hotel_pms.hotel_pms.doctype.hotel_stay.hotel_stay import create_housekeeping
    create_housekeeping(stay_doc.room)

    return {
        "success": True,
        "balance": total_balance,
        "message": "Checkout complete. Room assigned for housekeeping."
    }


@frappe.whitelist()
def get_checkout_summary(stay):
    """Return checkout summary for display."""
    stay_doc = frappe.get_doc("Hotel Stay", stay)
    folios = frappe.get_all("Hotel Folio",
        filters={"stay": stay},
        fields=["name", "total_charges", "total_payments", "balance", "status"])

    items = []
    for folio in folios:
        folio_items = frappe.get_all("Hotel Folio Item",
            filters={"parent": folio.name},
            fields=["date", "service", "description", "quantity", "rate", "amount"])
        items.extend(folio_items)

    payments = frappe.get_all("Hotel Payment",
        filters={"folio": ["in", [f.name for f in folios]], "docstatus": 1},
        fields=["payment_date", "payment_method", "amount", "payment_type"])

    return {
        "stay": stay_doc.as_dict(),
        "folios": folios,
        "items": items,
        "payments": payments,
        "total_charges": sum(f.total_charges or 0 for f in folios),
        "total_payments": sum(f.total_payments or 0 for f in folios),
        "balance": sum(f.balance or 0 for f in folios)
    }
