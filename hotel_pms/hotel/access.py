"""
hotel_pms.hotel.access
~~~~~~~~~~~~~~~~~~~~~~~
Permission helpers wired into hooks.py via
permission_query_conditions / has_permission.

Keeps all access-control logic in one place so it is easy to audit
and change without touching individual DocType controllers.
"""
import frappe


# ── Permission query conditions ────────────────────────────────────────────────
# These functions are called by Frappe when building list-view queries.
# They return a SQL WHERE fragment (empty string == no extra restriction).

def reservation_query(user=None):
    if not user:
        user = frappe.session.user
    if frappe.db.get_value("User", user, "user_type") == "System User":
        return ""
    return "1=0"


def stay_query(user=None):
    return reservation_query(user)


def folio_query(user=None):
    return reservation_query(user)


def payment_query(user=None):
    return reservation_query(user)


# ── Document-level has_permission ─────────────────────────────────────────────
# Return True/False/None (None → fall through to Frappe default).

def has_permission(doc, ptype="read", user=None):  # noqa: ARG001
    """All Hotel PMS documents follow the same rule:
    System Users have full access; portal/guest users have none.
    """
    if not user:
        user = frappe.session.user
    if frappe.db.get_value("User", user, "user_type") == "System User":
        return True
    return False
