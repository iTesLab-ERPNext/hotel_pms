import frappe
from frappe import _
from frappe.utils import today


@frappe.whitelist()
def add_charge(folio_name, charge_type, description, amount, service=None, reference=None):
    """Add a charge line to a folio."""
    folio = frappe.get_doc("Hotel Folio", folio_name)
    if folio.folio_status == "Closed":
        frappe.throw(_("Cannot add charges to a closed folio"))
    folio.add_charge(charge_type, description, float(amount), service, reference)
    return {"success": True, "balance_due": folio.balance_due}


@frappe.whitelist()
def void_charge(folio_name, item_idx):
    """Void a folio line item by its idx."""
    folio = frappe.get_doc("Hotel Folio", folio_name)
    for item in folio.items:
        if item.idx == int(item_idx):
            item.voided = 1
            break
    else:
        frappe.throw(_("Folio line item not found"))
    folio.calculate_totals()
    folio.save(ignore_permissions=True)
    return {"success": True}


@frappe.whitelist()
def get_folio_details(folio_name):
    """Return full folio detail including items and payments."""
    folio = frappe.get_doc("Hotel Folio", folio_name)
    items = []
    for item in folio.items or []:
        items.append({
            "idx": item.idx,
            "date": str(item.date or ""),
            "charge_type": item.charge_type,
            "description": item.description,
            "quantity": float(item.quantity or 1),
            "unit_price": float(item.unit_price or 0),
            "amount": float(item.amount or 0),
            "voided": item.voided,
        })

    payments = frappe.get_all(
        "Hotel Payment Allocation",
        filters={"folio": folio_name, "docstatus": 1},
        fields=["name", "payment_date", "payment_type", "amount", "reference"],
        order_by="payment_date asc",
    )

    return {
        "folio_name": folio.name,
        "folio_status": folio.folio_status,
        "customer": folio.customer,
        "room": folio.room,
        "room_charges": float(folio.room_charges or 0),
        "extra_charges": float(folio.extra_charges or 0),
        "total_charges": float(folio.total_charges or 0),
        "total_payments": float(folio.total_payments or 0),
        "balance_due": float(folio.balance_due or 0),
        "items": items,
        "payments": [dict(p) for p in payments],
    }


@frappe.whitelist()
def post_room_charge(stay_name, date=None, description=None):
    """Post a daily room charge to the folio for a given stay."""
    stay = frappe.get_doc("Hotel Stay", stay_name)
    if not stay.folio:
        frappe.throw(_("Stay has no linked folio"))
    if not date:
        date = today()

    # Check if charge already posted for this date
    folio = frappe.get_doc("Hotel Folio", stay.folio)
    for item in folio.items or []:
        if str(item.date) == str(date) and item.charge_type == "Room" and not item.voided:
            frappe.throw(_(f"Room charge already posted for {date}"))

    rate = float(stay.rate_per_night or 0)
    if not rate:
        # Try to get rate from room type
        room_type = frappe.db.get_value("Hotel Room", stay.room, "room_type")
        if room_type:
            rate = float(frappe.db.get_value("Hotel Room Type", room_type, "base_price") or 0)

    folio.add_charge(
        "Room",
        description or f"Room charge - {stay.room} ({date})",
        rate,
        reference=stay.room,
    )
    return {"success": True, "amount": rate}
