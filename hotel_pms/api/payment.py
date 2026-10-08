import frappe
from frappe import _
from frappe.utils import today


@frappe.whitelist()
def post_payment(folio_name, amount, payment_type, reference=None, notes=None):
    """Create and submit a Hotel Payment Allocation against a folio."""
    folio = frappe.get_doc("Hotel Folio", folio_name)
    if folio.folio_status == "Closed":
        frappe.throw(_("Cannot add payments to a closed folio"))

    payment = frappe.new_doc("Hotel Payment Allocation")
    payment.folio = folio_name
    payment.stay = folio.stay
    payment.payment_date = today()
    payment.payment_type = payment_type
    payment.amount = float(amount)
    payment.reference = reference
    payment.notes = notes
    payment.received_by = frappe.session.user
    payment.insert(ignore_permissions=True)
    payment.submit()

    # Refresh folio totals
    folio.reload()
    folio.calculate_totals()
    folio.save(ignore_permissions=True)

    return {
        "payment": payment.name,
        "balance_due": float(folio.balance_due or 0),
    }


@frappe.whitelist()
def get_payment_methods():
    """Return list of accepted payment methods."""
    return [
        "Cash", "Card", "Bank Transfer", "Online",
        "Voucher", "City Ledger", "Deposit", "Refund"
    ]
