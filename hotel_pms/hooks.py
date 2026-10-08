from . import __version__ as app_version

app_name = "hotel_pms"
app_title = "Hotel PMS"
app_publisher = "Your Company"
app_description = "Hotel Property Management System for ERPNext"
app_email = "info@yourcompany.com"
app_license = "MIT"
app_version = app_version

# ─── Required apps ───────────────────────────────────────────────────────────
required_apps = ["erpnext"]

# ─── DocType JS ──────────────────────────────────────────────────────────────
doctype_js = {
    "Hotel Reservation": "hotel_pms/doctype/hotel_reservation/hotel_reservation_ext.js",
    "Hotel Stay":        "hotel_pms/doctype/hotel_stay/hotel_stay_ext.js",
    "Hotel Room":        "hotel_pms/doctype/hotel_room/hotel_room_ext.js",
}

# ─── Scheduled tasks ─────────────────────────────────────────────────────────
scheduler_events = {
    "daily": [
        "hotel_pms.tasks.auto_no_show",
        "hotel_pms.tasks.auto_post_room_charges",
    ],
    "hourly": [
        "hotel_pms.tasks.update_room_statuses",
    ],
}

# ─── Fixtures ────────────────────────────────────────────────────────────────
fixtures = [
    {"dt": "Role", "filters": [["role_name", "in", [
        "Hotel Administrator", "Front Desk", "Hotel Manager", "Housekeeping",
        "Cashier", "Night Audit", "Revenue Manager", "Food & Beverage", "Concierge"
    ]]]},
]

# ─── Website ─────────────────────────────────────────────────────────────────
# None needed for PMS

# ─── Translations ────────────────────────────────────────────────────────────
# Translation files: hotel_pms/translations/fr.csv, ar.csv
