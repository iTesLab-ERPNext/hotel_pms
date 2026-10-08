import frappe
from frappe.utils import nowdate, flt


@frappe.whitelist()
def add_charge(folio_name, charge_type, description, amount, qty=1):
    """Add a charge line to a folio."""
    folio = frappe.get_doc("Hotel Folio", folio_name)
    if folio.status == "Closed":
        frappe.throw("Cannot add charges to a closed folio")

    folio.append("items", {
        "charge_type": charge_type,
        "description": description,
        "qty": flt(qty),
        "rate": flt(amount),
        "amount": flt(qty) * flt(amount),
        "posting_date": nowdate(),
    })
    _recalc_totals(folio)
    folio.save()
    frappe.db.commit()
    return folio.name


@frappe.whitelist()
def void_charge(folio_name, row_name):
    """Remove a charge line from a folio."""
    folio = frappe.get_doc("Hotel Folio", folio_name)
    folio.items = [i for i in folio.items if i.name != row_name]
    _recalc_totals(folio)
    folio.save()
    frappe.db.commit()
    return folio.name


@frappe.whitelist()
def get_folio_details(folio_name):
    folio = frappe.get_doc("Hotel Folio", folio_name)
    balance = (folio.total_charges or 0) - (folio.total_payments or 0)
    return {"folio": folio.as_dict(), "balance": balance}


def post_room_charge(folio_name):
    """Post today's room charge to folio (idempotent)."""
    folio = frappe.get_doc("Hotel Folio", folio_name)
    if folio.status == "Closed":
        return

    already_posted = any(
        i.charge_type == "Room Charge" and i.posting_date == nowdate()
        for i in (folio.items or [])
    )
    if already_posted:
        return

    stay = frappe.get_doc("Hotel Stay", folio.stay)
    rate = flt(stay.rate_per_night)
    if rate <= 0:
        return

    folio.append("items", {
        "charge_type": "Room Charge",
        "description": f"Room charge - {nowdate()}",
        "qty": 1,
        "rate": rate,
        "amount": rate,
        "posting_date": nowdate(),
    })
    _recalc_totals(folio)
    folio.save()
    frappe.db.commit()


def _recalc_totals(folio):
    folio.total_charges = sum(flt(i.amount) for i in (folio.items or []))
    payments = frappe.get_all(
        "Hotel Payment Allocation",
        filters={"folio": folio.name, "docstatus": 1},
        fields=["amount"],
    )
    folio.total_payments = sum(flt(p.amount) for p in payments)
