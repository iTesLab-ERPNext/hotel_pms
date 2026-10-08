"""
hotel_pms.setup.install
~~~~~~~~~~~~~~~~~~~~~~~
Frappe lifecycle hooks wired up in hooks.py.
Keeps business logic out of here — delegates to hotel.setup.
"""
import json
import os
import frappe


def after_install():
    """Runs immediately after bench install-app.
    DocType tables do NOT exist yet — only create Role records.
    """
    from hotel_pms.hotel.setup import ensure_roles
    ensure_roles()
    print("Hotel PMS installed. Run 'bench migrate' to complete setup.")


def before_migrate():
    """Clear module cache so Frappe picks up any changed DocType/module metadata."""
    from hotel_pms.compat import clear_module_cache
    clear_module_cache()


def after_migrate():
    """Runs after every bench migrate — all tables exist at this point."""
    from hotel_pms.hotel import setup as hotel_setup
    hotel_setup.run()
    _sync_workspace()
    print("Hotel PMS: default data ready.")


def before_uninstall():
    from hotel_pms.hotel.setup import before_uninstall as _bu
    _bu()


# ── Workspace sync ─────────────────────────────────────────────────────────────

def _sync_workspace():
    """Explicitly upsert the Hotel PMS workspace from its JSON file.

    bench migrate in Frappe v15 does not always auto-sync workspace files,
    so we do it here after every migrate.
    """
    ws_path = os.path.join(
        frappe.get_app_path("hotel_pms"),
        "hotel", "workspace", "hotel_pms", "hotel_pms.json",
    )
    if not os.path.exists(ws_path):
        print("  WARNING: workspace JSON not found — skipping workspace sync")
        return

    with open(ws_path) as f:
        ws_data = json.load(f)

    ws_data["doctype"] = "Workspace"
    # Strip timestamp/owner fields so optimistic locking never rejects the save
    # when the DB record is newer than the static JSON file.
    for field in ("modified", "modified_by", "creation", "owner"):
        ws_data.pop(field, None)

    if frappe.db.exists("Workspace", "Hotel PMS"):
        doc = frappe.get_doc("Workspace", "Hotel PMS")
        doc.update(ws_data)
        doc.flags.ignore_permissions = True
        doc.flags.ignore_version = True
        doc.save()
        print("  Updated workspace: Hotel PMS")
    else:
        frappe.get_doc(ws_data).insert(ignore_permissions=True)
        print("  Created workspace: Hotel PMS")
