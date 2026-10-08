"""
hotel_pms.compat
~~~~~~~~~~~~~~~~
Version compatibility shims for Frappe v15 / v16+.
Mirrors the pattern from erpnext_lmd/compat.py so the rest of the codebase
never imports frappe internals directly.
"""
import frappe


def frappe_major_version() -> int:
    """Return the running Frappe major version as an int."""
    try:
        import frappe as _frappe
        return int(_frappe.__version__.split(".")[0])
    except Exception:
        return 15


def is_v16_or_later() -> bool:
    return frappe_major_version() >= 16


def get_cache():
    """Return the active cache object regardless of Frappe version."""
    if is_v16_or_later():
        return frappe.cache
    return frappe.cache()


def clear_module_cache(app_name: str = "hotel_pms") -> None:
    """Clear the Frappe module/app cache — API changed between v15 and v16."""
    try:
        if is_v16_or_later():
            frappe.clear_cache()
        else:
            frappe.clear_cache()
    except Exception:
        pass
