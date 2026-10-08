import frappe
from frappe.utils import nowdate, add_days, getdate
from datetime import timedelta


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
        {"label": "Room Revenue", "fieldname": "room_revenue", "fieldtype": "Currency", "width": 130},
        {"label": "Service Revenue", "fieldname": "service_revenue", "fieldtype": "Currency", "width": 130},
        {"label": "Total Revenue", "fieldname": "total_revenue", "fieldtype": "Currency", "width": 130},
        {"label": "Payments Received", "fieldname": "payments", "fieldtype": "Currency", "width": 150},
        {"label": "Folios Count", "fieldname": "folio_count", "fieldtype": "Int", "width": 110},
    ]


def get_data(filters):
    from_date = getdate(filters.get("from_date") or add_days(nowdate(), -30))
    to_date = getdate(filters.get("to_date") or nowdate())

    data = []
    current = from_date
    while current <= to_date:
        date_str = str(current)

        charges = frappe.db.sql("""
            SELECT
                fi.charge_type,
                COALESCE(SUM(fi.amount), 0) as total
            FROM `tabHotel Folio Item` fi
            WHERE fi.date = %s
            GROUP BY fi.charge_type
        """, date_str, as_dict=True)

        room_rev = sum(c.total for c in charges if c.charge_type == "Room")
        service_rev = sum(c.total for c in charges if c.charge_type != "Room")
        total_rev = room_rev + service_rev

        payments = frappe.db.sql("""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM `tabHotel Payment`
            WHERE payment_date = %s AND docstatus = 1
        """, date_str, as_dict=True)[0].total or 0

        folio_count = frappe.db.sql("""
            SELECT COUNT(DISTINCT fi.parent) as cnt
            FROM `tabHotel Folio Item` fi
            WHERE fi.date = %s
        """, date_str, as_dict=True)[0].cnt or 0

        if total_rev > 0 or float(payments) > 0:
            data.append({
                "date": current,
                "room_revenue": room_rev,
                "service_revenue": service_rev,
                "total_revenue": total_rev,
                "payments": float(payments),
                "folio_count": folio_count,
            })

        current += timedelta(days=1)

    return data
