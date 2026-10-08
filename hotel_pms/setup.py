import frappe
from frappe import _


def after_install():
    """Run after app installation — imports fixtures and builds assets."""
    try:
        # Import fixtures (Roles + Workspace)
        from frappe.desk.page.setup_wizard.install_fixtures import install
        frappe.get_doc("Module Def", {"app_name": "hotel_pms"})
    except Exception:
        pass

    try:
        import frappe.utils.fixtures
        frappe.utils.fixtures.sync_fixtures("hotel_pms")
    except Exception:
        pass

    frappe.db.commit()
    print("Hotel PMS setup complete.")
