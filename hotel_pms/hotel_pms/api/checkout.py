import frappe
from frappe.utils import nowdate


@frappe.whitelist()
def checkout_stay(stay_name, force=False):
    """Check out a stay. Fails if folio has unpaid balance unless force=True."""
    stay = frappe.get_doc("Hotel Stay", stay_name)

    if stay.status != "Checked In":
        frappe.throw(f"Stay {stay_name} is not checked in (status: {stay.status})")

    folio_name = frappe.get_value("Hotel Folio", {"stay": stay_name}, "name")
    if folio_name:
        folio = frappe.get_doc("Hotel Folio", folio_name)
        balance = (folio.total_charges or 0) - (folio.total_payments or 0)
        if balance > 0 and not frappe.utils.cint(force):
            frappe.throw(f"Folio has outstanding balance of {balance}. Settle before checkout or use force=True.")
        folio.status = "Closed"
        folio.closing_date = nowdate()
        folio.save()

    stay.status = "Checked Out"
    stay.actual_checkout = nowdate()
    stay.save()

    frappe.db.set_value("Hotel Room", stay.room, "status", "Dirty")
    frappe.db.commit()
    return {"status": "success", "stay": stay_name}


@frappe.whitelist()
def get_checkout_summary(stay_name):
    """Return full folio details for checkout summary dialog."""
    stay = frappe.get_doc("Hotel Stay", stay_name)
    folio_name = frappe.get_value("Hotel Folio", {"stay": stay_name}, "name")
    if not folio_name:
        return {"stay": stay.as_dict(), "items": [], "payments": [], "balance": 0}

    folio = frappe.get_doc("Hotel Folio", folio_name)
    items = folio.items or []
    payments = frappe.get_all(
        "Hotel Payment Allocation",
        filters={"folio": folio_name, "docstatus": 1},
        fields=["payment_method", "amount", "posting_date"],
    )
    balance = (folio.total_charges or 0) - (folio.total_payments or 0)
    return {
        "stay": stay.as_dict(),
        "folio": folio.as_dict(),
        "items": [i.as_dict() for i in items],
        "payments": payments,
        "balance": balance,
    }
