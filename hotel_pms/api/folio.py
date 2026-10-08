import frappe
from frappe import _

@frappe.whitelist()
def add_charge(folio, service, description=None, quantity=1, rate=None):
    """Add a charge to a folio."""
    folio_doc = frappe.get_doc("Hotel Folio", folio)
    if folio_doc.status != "Open":
        frappe.throw(_("Folio is not open"))

    if not rate and service:
        rate = frappe.db.get_value("Hotel Service", service, "rate") or 0

    folio_doc.append("items", {
        "date": frappe.utils.today(),
        "service": service,
        "description": description or service,
        "quantity": float(quantity),
        "rate": float(rate or 0),
        "amount": float(quantity) * float(rate or 0)
    })
    folio_doc.save(ignore_permissions=True)
    return {"success": True, "folio": folio_doc.name, "balance": folio_doc.balance}


@frappe.whitelist()
def get_folio(stay=None, reservation=None):
    """Get folio for a stay or reservation."""
    filters = {}
    if stay:
        filters["stay"] = stay
    elif reservation:
        filters["reservation"] = reservation

    folios = frappe.get_all("Hotel Folio", filters=filters,
        fields=["name", "customer", "room", "total_charges", "total_payments", "balance", "status"])
    return folios
