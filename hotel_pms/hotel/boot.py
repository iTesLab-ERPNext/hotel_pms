"""
hotel_pms.hotel.boot
~~~~~~~~~~~~~~~~~~~~~
Injects Hotel PMS configuration into every Frappe boot payload
so the browser doesn't need an extra round-trip for lookup data.
"""
import frappe


def extend_bootinfo(bootinfo) -> None:
    """Called by Frappe for every authenticated page load."""
    bootinfo.hotel_pms = {
        "room_statuses": [
            "Available", "Reserved", "Occupied",
            "Cleaning", "Maintenance", "Blocked", "Out of Service",
        ],
        "housekeeping_statuses": ["Clean", "Dirty", "Inspected", "In Progress"],
        "payment_methods": ["Cash", "Card", "Bank Transfer", "Cheque", "Online", "Other"],
    }
