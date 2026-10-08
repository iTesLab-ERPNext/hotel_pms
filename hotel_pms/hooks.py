app_name = "hotel_pms"
app_title = "Hotel PMS"
app_publisher = "iTesLab"
app_description = "Hotel Property Management System for ERPNext"
app_email = "info@iteslab.com"
app_license = "MIT"
app_version = "1.0.0"

required_apps = ["erpnext"]

# DocType JS extensions – paths are relative to the app package directory (hotel_pms/)
doctype_js = {
    "Hotel Reservation": "hotel_pms/doctype/hotel_reservation/hotel_reservation_ext.js",
    "Hotel Stay":        "hotel_pms/doctype/hotel_stay/hotel_stay_ext.js",
    "Hotel Room":        "hotel_pms/doctype/hotel_room/hotel_room_ext.js",
}

fixtures = [
    {
        "dt": "Role",
        "filters": [["role_name", "in", [
            "Hotel Administrator", "Front Desk", "Hotel Manager",
            "Housekeeping", "Cashier", "Night Audit",
            "Revenue Manager", "Food & Beverage", "Concierge"
        ]]]
    }
]

scheduler_events = {
    "daily": [
        "hotel_pms.hotel_pms.tasks.auto_no_show",
        "hotel_pms.hotel_pms.tasks.auto_post_room_charges",
    ],
    "hourly": [
        "hotel_pms.hotel_pms.tasks.update_room_statuses",
    ],
}
