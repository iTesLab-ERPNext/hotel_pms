"""
hotel_pms.api.hotel_api
~~~~~~~~~~~~~~~~~~~~~~~~
Backward-compatibility shim — all logic has moved to hotel_pms.hotel.api.
Existing clients calling hotel_pms.api.hotel_api.* continue to work.
"""
from hotel_pms.hotel.api import (  # noqa: F401
    get_dashboard_data,
    get_room_availability,
    get_room_calendar,
    get_planning_board,
    get_folio_details,
    check_in,
    check_out,
    move_room,
    add_folio_charge,
    create_payment,
    update_housekeeping_status,
)
