import frappe
from frappe.utils import getdate, date_diff


def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date") or frappe.utils.add_months(frappe.utils.nowdate(), -1)
    to_date = filters.get("to_date") or frappe.utils.nowdate()

    columns = [
        {"label": "Room", "fieldname": "room", "fieldtype": "Link", "options": "Hotel Room", "width": 100},
        {"label": "Room Type", "fieldname": "room_type", "fieldtype": "Data", "width": 120},
        {"label": "Floor", "fieldname": "floor", "fieldtype": "Data", "width": 70},
        {"label": "Nights Occupied", "fieldname": "nights_occupied", "fieldtype": "Int", "width": 120},
        {"label": "Occupancy %", "fieldname": "occupancy_pct", "fieldtype": "Percent", "width": 110},
        {"label": "Total Revenue", "fieldname": "total_revenue", "fieldtype": "Currency", "width": 130},
        {"label": "ADR", "fieldname": "adr", "fieldtype": "Currency", "width": 100},
        {"label": "RevPAR", "fieldname": "revpar", "fieldtype": "Currency", "width": 100},
    ]

    total_days = date_diff(to_date, from_date) or 1

    data = frappe.db.sql(
        """
        SELECT
            hr.name AS room,
            hrt.room_type_name AS room_type,
            hr.floor,
            SUM(DATEDIFF(
                LEAST(COALESCE(hs.actual_checkout, hs.expected_checkout), %s),
                GREATEST(hs.checkin_date, %s)
            )) AS nights_occupied,
            SUM(hfi.amount) AS total_revenue
        FROM `tabHotel Room` hr
        LEFT JOIN `tabHotel Room Type` hrt ON hrt.name = hr.room_type
        LEFT JOIN `tabHotel Stay` hs
            ON hs.room = hr.name
            AND hs.checkin_date <= %s
            AND COALESCE(hs.actual_checkout, hs.expected_checkout) >= %s
        LEFT JOIN `tabHotel Folio` hf ON hf.stay = hs.name
        LEFT JOIN `tabHotel Folio Item` hfi ON hfi.parent = hf.name
        WHERE hr.is_active = 1
        GROUP BY hr.name, hrt.room_type_name, hr.floor
        ORDER BY hr.floor, hr.room_number
        """,
        (to_date, from_date, to_date, from_date),
        as_dict=True,
    )

    result = []
    for row in data:
        nights = max(int(row.nights_occupied or 0), 0)
        revenue = float(row.total_revenue or 0)
        occ_pct = round(nights / total_days * 100, 1)
        adr = round(revenue / nights, 2) if nights else 0
        revpar = round(revenue / total_days, 2)
        result.append({
            "room": row.room,
            "room_type": row.room_type,
            "floor": row.floor,
            "nights_occupied": nights,
            "occupancy_pct": occ_pct,
            "total_revenue": revenue,
            "adr": adr,
            "revpar": revpar,
        })

    return columns, result
