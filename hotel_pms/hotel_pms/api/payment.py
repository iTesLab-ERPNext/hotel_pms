import frappe
from frappe.utils import nowdate, flt


@frappe.whitelist()
def post_payment(folio_name, payment_method, amount, reference=None):
    """Create and submit a Hotel Payment Allocation."""
    folio = frappe.get_doc("Hotel Folio", folio_name)
    if folio.status == "Closed":
        frappe.throw("Cannot post payment to a closed folio")

    alloc = frappe.new_doc("Hotel Payment Allocation")
    alloc.folio = folio_name
    alloc.stay = folio.stay
    alloc.payment_method = payment_method
    alloc.amount = flt(amount)
    alloc.posting_date = nowdate()
    alloc.reference = reference or ""
    alloc.insert()
    alloc.submit()

    # Refresh folio totals
    from hotel_pms.hotel_pms.api.folio import _recalc_totals
    _recalc_totals(folio)
    folio.save()
    frappe.db.commit()
    return alloc.name


@frappe.whitelist()
def get_payment_methods():
    return ["Cash", "Credit Card", "Debit Card", "Bank Transfer", "Cheque", "Online"]
