app_name = "hotel_pms"
app_title = "Hotel PMS"
app_publisher = "Hotel PMS"
app_description = "Hotel Property Management System"
app_email = "info@hotelpms.com"
app_license = "MIT"
app_version = "1.0.0"

# Includes in <head>
# ------------------
app_include_css = []
app_include_js = ["/assets/hotel_pms/js/hotel_pms.js"]

# Fixtures
fixtures = [
    {
        "doctype": "Role",
        "filters": [["name", "in", ["Hotel Manager", "Front Desk", "Housekeeping Staff", "Hotel Cashier"]]]
    }
]

# Document Events
doc_events = {
    "Hotel Stay": {
        "on_submit": "hotel_pms.hotel_pms.doctype.hotel_stay.hotel_stay.on_submit"
    }
}
