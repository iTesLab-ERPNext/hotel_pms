import frappe
from frappe import _
from frappe.utils import today, add_days

@frappe.whitelist()
def get_dashboard_stats():
    """Return KPI data for the Hotel PMS dashboard."""
    t = today()

    stats = {
        "available_rooms": frappe.db.count("Hotel Room", {"status": "Available", "active": 1}),
        "occupied_rooms": frappe.db.count("Hotel Room", {"status": "Occupied", "active": 1}),
        "reserved_rooms": frappe.db.count("Hotel Room", {"status": "Reserved", "active": 1}),
        "cleaning_rooms": frappe.db.count("Hotel Room", {"status": "Cleaning", "active": 1}),
        "maintenance_rooms": frappe.db.count("Hotel Room", {"status": "Maintenance", "active": 1}),
        "total_rooms": frappe.db.count("Hotel Room", {"active": 1}),
        "today_arrivals": frappe.db.count("Hotel Reservation", {
            "arrival_date": t,
            "status": ["in", ["Confirmed", "Checked In"]]
        }),
        "today_departures": frappe.db.count("Hotel Stay", {
            "expected_checkout": t,
            "status": "Active"
        }),
        "active_stays": frappe.db.count("Hotel Stay", {"status": "Active"}),
        "total_reservations": frappe.db.count("Hotel Reservation", {
            "status": ["not in", ["Cancelled"]]
        }),
        "pending_housekeeping": frappe.db.count("Hotel Housekeeping", {
            "status": ["in", ["Dirty", "Cleaning"]]
        }),
        "outstanding_balance": _get_outstanding_balance(),
    }
    return stats


def _get_outstanding_balance():
    result = frappe.db.sql("SELECT COALESCE(SUM(balance),0) FROM `tabHotel Folio` WHERE status='Open'")
    return float(result[0][0]) if result else 0.0


@frappe.whitelist()
def get_room_board():
    """Return all rooms with current stay/reservation info for Room Board."""
    rooms = frappe.db.sql("""
        SELECT
            r.name, r.room_number, r.room_type, r.floor, r.status, r.capacity,
            s.name as stay_name,
            s.customer as stay_customer,
            hc.full_name as guest_name,
            s.checkin_date,
            s.expected_checkout,
            f.balance as folio_balance,
            hk.status as housekeeping_status
        FROM `tabHotel Room` r
        LEFT JOIN `tabHotel Stay` s ON s.room = r.name AND s.status = 'Active'
        LEFT JOIN `tabHotel Customer` hc ON hc.name = s.customer
        LEFT JOIN `tabHotel Folio` f ON f.stay = s.name AND f.status = 'Open'
        LEFT JOIN `tabHotel Housekeeping` hk ON hk.room = r.name
            AND hk.status IN ('Dirty','Cleaning')
            AND hk.date = CURDATE()
        WHERE r.active = 1
        ORDER BY r.floor ASC, r.room_number ASC
    """, as_dict=True)
    return rooms


@frappe.whitelist()
def get_room_planner(from_date=None, to_date=None, room_type=None):
    """Return data for room planning board (rooms x dates grid)."""
    if not from_date:
        from_date = frappe.utils.today()
    if not to_date:
        to_date = frappe.utils.add_days(from_date, 13)

    room_filters = {"active": 1}
    if room_type:
        room_filters["room_type"] = room_type

    rooms = frappe.get_all("Hotel Room",
        filters=room_filters,
        fields=["name", "room_number", "room_type", "floor", "status"],
        order_by="floor asc, room_number asc")

    # Get all reservations in range
    reservations = frappe.db.sql("""
        SELECT
            rr.room,
            res.name as reservation,
            res.customer,
            hc.full_name as guest_name,
            res.arrival_date,
            res.departure_date,
            res.status,
            res.number_of_nights
        FROM `tabHotel Reservation Room` rr
        JOIN `tabHotel Reservation` res ON res.name = rr.parent
        LEFT JOIN `tabHotel Customer` hc ON hc.name = res.customer
        WHERE res.status NOT IN ('Cancelled')
        AND res.arrival_date <= %(to_date)s
        AND res.departure_date > %(from_date)s
        ORDER BY res.arrival_date
    """, {"from_date": from_date, "to_date": to_date}, as_dict=True)

    # Get housekeeping statuses
    hk_statuses = frappe.db.sql("""
        SELECT room, status, date FROM `tabHotel Housekeeping`
        WHERE date BETWEEN %(from_date)s AND %(to_date)s
        AND status IN ('Dirty','Cleaning','Maintenance')
    """, {"from_date": from_date, "to_date": to_date}, as_dict=True)

    return {
        "rooms": rooms,
        "reservations": reservations,
        "housekeeping": hk_statuses,
        "from_date": from_date,
        "to_date": to_date
    }


@frappe.whitelist()
def get_room_calendar(room, from_date=None, to_date=None):
    """Return reservation calendar for a single room."""
    if not from_date:
        from_date = frappe.utils.add_days(frappe.utils.today(), -7)
    if not to_date:
        to_date = frappe.utils.add_days(frappe.utils.today(), 30)

    reservations = frappe.db.sql("""
        SELECT
            rr.room,
            res.name as reservation,
            res.customer,
            hc.full_name as guest_name,
            res.arrival_date,
            res.departure_date,
            res.status,
            res.number_of_nights,
            res.package
        FROM `tabHotel Reservation Room` rr
        JOIN `tabHotel Reservation` res ON res.name = rr.parent
        LEFT JOIN `tabHotel Customer` hc ON hc.name = res.customer
        WHERE rr.room = %(room)s
        AND res.status NOT IN ('Cancelled')
        AND res.arrival_date <= %(to_date)s
        AND res.departure_date > %(from_date)s
        ORDER BY res.arrival_date
    """, {"room": room, "from_date": from_date, "to_date": to_date}, as_dict=True)

    room_doc = frappe.get_doc("Hotel Room", room)
    return {
        "room": room_doc.as_dict(),
        "reservations": reservations,
        "from_date": from_date,
        "to_date": to_date
    }
