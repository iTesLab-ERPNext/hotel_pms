import frappe


def after_install():
    create_roles()
    create_default_categories()
    print("Hotel PMS installed successfully.")


def create_roles():
    for role in ["Hotel Manager", "Front Desk", "Housekeeping", "Cashier"]:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role}).insert()
            print(f"  Created role: {role}")
        else:
            print(f"  Role already exists: {role}")


def create_default_categories():
    for cat in ["Individual", "Family", "Corporate", "VIP", "Agency", "Group"]:
        if not frappe.db.exists("Hotel Customer Category", cat):
            frappe.get_doc({
                "doctype": "Hotel Customer Category",
                "customer_category": cat,
                "active": 1
            }).insert(ignore_permissions=True)
            print(f"  Created customer category: {cat}")

    for ft in ["Single", "Couple", "Family", "Large Family", "Group"]:
        if not frappe.db.exists("Hotel Family Type", ft):
            frappe.get_doc({
                "doctype": "Hotel Family Type",
                "family_type": ft,
                "active": 1
            }).insert(ignore_permissions=True)
            print(f"  Created family type: {ft}")
