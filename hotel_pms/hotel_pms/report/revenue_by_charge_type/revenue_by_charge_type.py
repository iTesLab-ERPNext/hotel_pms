import frappe


def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date") or frappe.utils.add_months(frappe.utils.nowdate(), -1)
    to_date = filters.get("to_date") or frappe.utils.nowdate()

    columns = [
        {"label": "Charge Type", "fieldname": "charge_type", "fieldtype": "Data", "width": 160},
        {"label": "Total Revenue", "fieldname": "total", "fieldtype": "Currency", "width": 140},
        {"label": "% of Total", "fieldname": "pct", "fieldtype": "Percent", "width": 110},
        {"label": "Transactions", "fieldname": "txn_count", "fieldtype": "Int", "width": 110},
    ]

    rows = frappe.db.sql(
        """
        SELECT charge_type, SUM(amount) AS total, COUNT(*) AS txn_count
        FROM `tabHotel Folio Item`
        WHERE posting_date BETWEEN %s AND %s AND (voided IS NULL OR voided = 0)
        GROUP BY charge_type
        ORDER BY total DESC
        """,
        (from_date, to_date),
        as_dict=True,
    )

    grand_total = sum(float(r.total or 0) for r in rows) or 1
    data = []
    for r in rows:
        total = float(r.total or 0)
        data.append({
            "charge_type": r.charge_type,
            "total": total,
            "pct": round(total / grand_total * 100, 1),
            "txn_count": r.txn_count,
        })

    return columns, data
