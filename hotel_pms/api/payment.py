import frappe
from frappe import _

@frappe.whitelist()
def add_payment(folio=None, reservation=None, customer=None,
                amount=0, payment_method="Cash", payment_type="Full Payment",
                reference=None, notes=None):
    """Record a payment."""
    if not customer:
        if folio:
            customer = frappe.db.get_value("Hotel Folio", folio, "customer")
        elif reservation:
            customer = frappe.db.get_value("Hotel Reservation", reservation, "customer")

    payment = frappe.get_doc({
        "doctype": "Hotel Payment",
        "folio": folio,
        "reservation": reservation,
        "customer": customer,
        "payment_date": frappe.utils.today(),
        "payment_method": payment_method,
        "payment_type": payment_type,
        "amount": float(amount),
        "reference": reference,
        "notes": notes
    })
    payment.insert(ignore_permissions=True)
    payment.submit()
    return {"success": True, "payment": payment.name}
