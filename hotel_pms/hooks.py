app_name        = "hotel_pms"
commands        = ["hotel_pms.hotel.commands"]
app_title       = "Hotel PMS"
app_publisher   = "Hotel PMS"
app_description = "Hotel Property Management System"
app_email       = "admin@hotelpms.com"
app_license     = "MIT"
app_version     = "1.0.0"

# ── App screen card ─────────────────────────────────────────────────────────────
add_to_apps_screen = [
    {
        "name":        "hotel_pms",
        "logo":        "/assets/hotel_pms/images/hotel_pms_logo.png",
        "title":       "Hotel PMS",
        "route":       "/hotel-pms-dashboard",
        "has_permission": "hotel_pms.hotel.access.has_permission",
    }
]

# ── Navbar shortcut (top bar) ───────────────────────────────────────────────────
# Adds a "Hotel" link in the Frappe navbar pointing straight to the dashboard.
standard_navbar_items = [
    {
        "item_label":  "Hotel Dashboard",
        "item_type":   "Route",
        "route":       "/hotel-pms-dashboard",
        "is_standard": 1,
    }
]

# ── Fixtures — exported/imported by bench export-fixtures / import-fixtures ────
fixtures = [
    {"dt": "Role",       "filters": [["name", "in", ["Hotel Manager", "Front Desk", "Housekeeping", "Cashier"]]]},
    {"dt": "Workspace",  "filters": [["name", "=", "Hotel PMS"]]},
    {"dt": "Hotel Customer Category"},
    {"dt": "Hotel Family Type"},
    {"dt": "Hotel Room Type"},
    {"dt": "Hotel Service"},
]

# ── Lifecycle hooks ─────────────────────────────────────────────────────────────
after_install    = "hotel_pms.setup.install.after_install"
before_migrate   = "hotel_pms.setup.install.before_migrate"
after_migrate    = "hotel_pms.setup.install.after_migrate"
before_uninstall = "hotel_pms.setup.install.before_uninstall"

# ── Jinja helpers (available in Print Formats) ─────────────────────────────────
jinja = {
    "methods": [
        "hotel_pms.hotel.jinja.get_folio_items",
        "hotel_pms.hotel.jinja.format_currency_hotel",
    ]
}

# ── Scheduled tasks ─────────────────────────────────────────────────────────────
scheduler_events = {
    "daily": [
        "hotel_pms.hotel.tasks.daily_auto_checkout",
        "hotel_pms.hotel.tasks.daily_flag_no_shows",
    ],
}

# ── Permission hooks ────────────────────────────────────────────────────────────
permission_query_conditions = {
    "Hotel Reservation":   "hotel_pms.hotel.access.reservation_query",
    "Hotel Stay":          "hotel_pms.hotel.access.stay_query",
    "Hotel Folio":         "hotel_pms.hotel.access.folio_query",
    "Hotel Payment":       "hotel_pms.hotel.access.payment_query",
}

has_permission = {
    "Hotel Reservation":   "hotel_pms.hotel.access.has_permission",
    "Hotel Stay":          "hotel_pms.hotel.access.has_permission",
    "Hotel Folio":         "hotel_pms.hotel.access.has_permission",
    "Hotel Payment":       "hotel_pms.hotel.access.has_permission",
    "Hotel Room":          "hotel_pms.hotel.access.has_permission",
    "Hotel Housekeeping":  "hotel_pms.hotel.access.has_permission",
}

# ── Extend boot info (data sent to every browser session) ──────────────────────
extend_bootinfo = "hotel_pms.hotel.boot.extend_bootinfo"

# ── JS / CSS bundles ─────────────────────────────────────────────────────────────
# These are resolved by Frappe's asset bundler; the files must exist.
app_include_js  = ["/assets/hotel_pms/js/hotel_pms.js"]
app_include_css = ["/assets/hotel_pms/css/hotel_pms.css"]
