import frappe
from frappe.utils import getdate, date_diff, add_days


def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date") or frappe.utils.add_months(frappe.utils.today(), -1)
    to_date   = filters.get("to_date")   or frappe.utils.today()

    columns = [
        {"label": "Room",       "fieldname": "room",       "fieldtype": "Link",    "options": "Hotel Room",     "width": 100},
        {"label": "Room Type",  "fieldname": "room_type",  "fieldtype": "Link",    "options": "Hotel Room Type","width": 140},
        {"label": "Floor",      "fieldname": "floor",      "fieldtype": "Data",    "width": 60},
        {"label": "Nights Occupied","fieldname":"nights_occupied","fieldtype":"Int","width": 120},
        {"label": "Occupancy %","fieldname":"occupancy_pct","fieldtype":"Percent", "width": 110},
        {"label": "Total Revenue","fieldname":"total_revenue","fieldtype":"Currency","width": 130},
        {"label": "ADR",        "fieldname": "adr",        "fieldtype": "Currency","width": 100},
        {"label": "RevPAR",     "fieldname": "revpar",     "fieldtype": "Currency","width": 100},
    ]

    total_days = date_diff(to_date, from_date) or 1

    rows = frappe.db.sql(
        """
        SELECT
            r.name AS room,
            r.room_type,
            r.floor,
            COALESCE(SUM(
                LEAST(DATE(s.expected_checkout), %s)
                - GREATEST(DATE(s.checkin_date), %s)
            ), 0) AS nights_occupied,
            COALESCE(SUM(f.total_charges), 0) AS total_revenue
        FROM `tabHotel Room` r
        LEFT JOIN `tabHotel Stay` s
            ON s.room = r.name
            AND s.stay_status IN ('In House','Extended','Checked Out')
            AND DATE(s.checkin_date) <= %s
            AND DATE(s.expected_checkout) >= %s
        LEFT JOIN `tabHotel Folio` f ON f.stay = s.name
        WHERE r.active = 1
        GROUP BY r.name, r.room_type, r.floor
        ORDER BY r.floor, r.name
        """,
        (to_date, from_date, to_date, from_date),
        as_dict=True,
    )

    data = []
    for row in rows:
        nights = max(int(row.nights_occupied or 0), 0)
        revenue = float(row.total_revenue or 0)
        occ_pct = round(nights / total_days * 100, 1)
        adr = round(revenue / nights, 2) if nights else 0
        revpar = round(revenue / total_days, 2)
        data.append({
            "room": row.room,
            "room_type": row.room_type,
            "floor": row.floor,
            "nights_occupied": nights,
            "occupancy_pct": occ_pct,
            "total_revenue": revenue,
            "adr": adr,
            "revpar": revpar,
        })

    return columns, data
