import frappe
from frappe.utils import today, add_months


def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date") or add_months(today(), -1)
    to_date   = filters.get("to_date")   or today()

    columns = [
        {"label": "Charge Type",  "fieldname": "charge_type",  "fieldtype": "Data",    "width": 150},
        {"label": "Transactions", "fieldname": "transactions",  "fieldtype": "Int",     "width": 120},
        {"label": "Total Amount", "fieldname": "total_amount",  "fieldtype": "Currency","width": 140},
        {"label": "% of Revenue", "fieldname": "pct_revenue",   "fieldtype": "Percent", "width": 120},
    ]

    rows = frappe.db.sql(
        """
        SELECT fi.charge_type,
               COUNT(*) AS transactions,
               SUM(fi.amount) AS total_amount
        FROM `tabHotel Folio Item` fi
        JOIN `tabHotel Folio` f ON f.name = fi.parent
        WHERE fi.voided = 0
          AND f.folio_status != 'Voided'
          AND fi.date BETWEEN %s AND %s
        GROUP BY fi.charge_type
        ORDER BY total_amount DESC
        """,
        (from_date, to_date),
        as_dict=True,
    )

    grand_total = sum(float(r.total_amount or 0) for r in rows)

    data = []
    for row in rows:
        amt = float(row.total_amount or 0)
        data.append({
            "charge_type": row.charge_type,
            "transactions": int(row.transactions or 0),
            "total_amount": amt,
            "pct_revenue": round(amt / grand_total * 100, 1) if grand_total else 0,
        })

    return columns, data
