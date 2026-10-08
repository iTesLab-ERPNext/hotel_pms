import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def checkout_stay(stay_name, force=False):
    """
    Perform checkout for a stay.
    Validates no outstanding balance unless force=True.
    """
    stay = frappe.get_doc("Hotel Stay", stay_name)
    if stay.stay_status == "Checked Out":
        frappe.throw(_("Stay is already checked out"))

    # Sync financials before checking balance
    stay._sync_financials()
    balance = float(stay.balance_due or 0)
    if balance > 0 and not force:
        frappe.throw(_(f"Outstanding balance of {balance:.2f} must be settled before checkout. Use force=True to override."))

    stay.checkout()
    return {"status": "success", "actual_checkout": str(stay.actual_checkout)}


@frappe.whitelist()
def get_checkout_summary(stay_name):
    """Return a summary dict for the checkout confirmation screen."""
    stay = frappe.get_doc("Hotel Stay", stay_name)
    stay._sync_financials()

    folio_items = []
    if stay.folio:
        folio = frappe.get_doc("Hotel Folio", stay.folio)
        for item in folio.items or []:
            if not item.voided:
                folio_items.append({
                    "date": str(item.date),
                    "charge_type": item.charge_type,
                    "description": item.description,
                    "amount": float(item.amount or 0),
                })

    payments = frappe.get_all(
        "Hotel Payment Allocation",
        filters={"folio": stay.folio, "docstatus": 1},
        fields=["payment_date", "payment_type", "amount", "reference"],
    )

    return {
        "stay": stay_name,
        "guest": stay.guest,
        "guest_name": stay.guest_name,
        "room": stay.room,
        "checkin_date": str(stay.checkin_date),
        "expected_checkout": str(stay.expected_checkout),
        "number_of_nights": stay.number_of_nights,
        "folio_items": folio_items,
        "payments": [dict(p) for p in payments],
        "total_charges": float(stay.total_charges or 0),
        "total_paid": float(stay.total_paid or 0),
        "balance_due": float(stay.balance_due or 0),
    }
