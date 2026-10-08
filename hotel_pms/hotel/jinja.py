"""
hotel_pms.hotel.jinja
~~~~~~~~~~~~~~~~~~~~~
Helper functions available inside Frappe Print Formats.
Registered in hooks.py under jinja.methods.
"""
import frappe


def get_folio_items(folio_name: str) -> list:
    """Return folio charge lines for use in a print format."""
    return frappe.get_all(
        "Hotel Folio Item",
        filters={"parent": folio_name},
        fields=["date", "charge_type", "description", "quantity", "rate", "amount", "service"],
        order_by="date, idx",
    )


def format_currency_hotel(amount, currency=None) -> str:
    """Format a monetary value using the system currency."""
    if not currency:
        currency = frappe.defaults.get_global_default("currency") or "USD"
    return frappe.utils.fmt_money(amount or 0, currency=currency)
