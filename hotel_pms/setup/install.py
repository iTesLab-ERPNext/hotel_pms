import json
import os
import frappe


def after_install():
    """Runs immediately after the app is installed.
    Keep this minimal — DocType tables are NOT yet created at this point.
    Only create Role records (which use existing Frappe DocTypes).
    """
    create_roles()
    print("Hotel PMS installed successfully. Run 'bench migrate' to complete setup.")


def after_migrate():
    """Runs after every 'bench migrate'.
    All DocType tables exist by this point, so it's safe to insert records.
    """
    create_default_categories()
    sync_workspace()
    frappe.db.commit()
    print("Hotel PMS default data ready.")


def create_roles():
    for role in ["Hotel Manager", "Front Desk", "Housekeeping", "Cashier"]:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)
            print(f"  Created role: {role}")


def create_default_categories():
    """Create seed data for lookup tables. Safe to call multiple times."""
    for cat in ["Individual", "Family", "Corporate", "VIP", "Agency", "Group"]:
        if not frappe.db.exists("Hotel Customer Category", cat):
            frappe.get_doc({
                "doctype": "Hotel Customer Category",
                "customer_category": cat,
                "active": 1
            }).insert(ignore_permissions=True)

    for ft in ["Single", "Couple", "Family", "Large Family", "Group"]:
        if not frappe.db.exists("Hotel Family Type", ft):
            frappe.get_doc({
                "doctype": "Hotel Family Type",
                "family_type": ft,
                "active": 1
            }).insert(ignore_permissions=True)

    for rt in ["Single", "Double", "Twin", "Triple", "Family", "Suite", "Deluxe", "Villa"]:
        if not frappe.db.exists("Hotel Room Type", rt):
            frappe.get_doc({
                "doctype": "Hotel Room Type",
                "room_type": rt,
                "code": rt[:3].upper(),
                "active": 1
            }).insert(ignore_permissions=True)

    for svc in ["Breakfast", "Lunch", "Dinner", "Restaurant", "Spa",
                "Horse Riding", "Transport", "Laundry", "Extra Bed", "Other"]:
        if not frappe.db.exists("Hotel Service", svc):
            frappe.get_doc({
                "doctype": "Hotel Service",
                "service_name": svc,
                "code": svc[:3].upper(),
                "active": 1
            }).insert(ignore_permissions=True)


def sync_workspace():
    """Explicitly import the Hotel PMS workspace from JSON.

    bench migrate doesn't always auto-sync workspace files in v15, so we do it
    here to guarantee the workspace is present after every migrate.
    """
    ws_path = os.path.join(
        frappe.get_app_path("hotel_pms"),
        "hotel", "workspace", "hotel_pms", "hotel_pms.json"
    )
    if not os.path.exists(ws_path):
        print("  WARNING: workspace JSON not found, skipping workspace sync")
        return

    with open(ws_path) as f:
        ws_data = json.load(f)

    ws_data["doctype"] = "Workspace"

    if frappe.db.exists("Workspace", "Hotel PMS"):
        doc = frappe.get_doc("Workspace", "Hotel PMS")
        doc.update(ws_data)
        doc.flags.ignore_permissions = True
        doc.save()
        print("  Updated workspace: Hotel PMS")
    else:
        frappe.get_doc(ws_data).insert(ignore_permissions=True)
        print("  Created workspace: Hotel PMS")
