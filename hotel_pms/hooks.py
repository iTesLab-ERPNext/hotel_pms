app_name = "hotel_pms"
app_title = "Hotel PMS"
app_publisher = "Hotel PMS"
app_description = "Hotel Property Management System"
app_email = "admin@hotelpms.com"
app_license = "MIT"
app_version = "0.0.1"

# Fixtures
fixtures = [
    {"dt": "Role", "filters": [["name", "in", ["Hotel Manager", "Front Desk", "Housekeeping", "Cashier"]]]},
    {"dt": "Workspace", "filters": [["name", "=", "Hotel PMS"]]},
    {"dt": "Hotel Customer Category"},
    {"dt": "Hotel Family Type"},
    {"dt": "Hotel Room Type"},
    {"dt": "Hotel Service"},
]

# DocTypes owned by this app (for permission setup)
doctype_roles = {
    "Hotel Customer": ["Hotel Manager", "Front Desk"],
    "Hotel Reservation": ["Hotel Manager", "Front Desk"],
    "Hotel Stay": ["Hotel Manager", "Front Desk"],
    "Hotel Folio": ["Hotel Manager", "Cashier"],
    "Hotel Payment": ["Hotel Manager", "Cashier"],
    "Hotel Room": ["Hotel Manager", "Front Desk", "Housekeeping"],
    "Hotel Housekeeping": ["Hotel Manager", "Housekeeping"],
}

# Website route rules
website_route_rules = []

# Scheduled tasks
scheduler_events = {}

# after_install hook
after_install = "hotel_pms.setup.install.after_install"
