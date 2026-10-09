"""
Revenue by Charge Type
-----------------------
Aggregated revenue breakdown — by Charge Type (default), by Day, or by Month.
Essential for management reporting and identifying top revenue streams.
"""
import frappe
from hotel_pms.hotel.report_utils import col, summary, normalize_dates


def execute(filters=None):
    filters  = filters or {}
    from_date, to_date = normalize_dates(filters, default_days=30)
    group_by = filters.get("group_by") or "Charge Type"

    columns = _columns(group_by)
    rows    = _data(from_date, to_date, group_by)

    grand_total = sum(r.get("total_revenue", 0) for r in rows)
    room_rev    = sum(r.get("total_revenue", 0) for r in rows
                      if r.get("charge_type") == "Room")
    svc_rev     = grand_total - room_rev

    report_summary = [
        summary(grand_total, "Grand Total",    "Currency", "Blue"),
        summary(room_rev,    "Room Revenue",   "Currency", "Green"),
        summary(svc_rev,     "Service Revenue","Currency", "Orange"),
    ]
    return columns, rows, None, None, report_summary


def _columns(group_by):
    base = []
    if group_by == "Day":
        base = [
            col("period",        "Date",          "Date",     width=120),
            col("charge_type",   "Charge Type",   "Data",     width=120),
        ]
    elif group_by == "Month":
        base = [
            col("period",        "Month",         "Data",     width=120),
            col("charge_type",   "Charge Type",   "Data",     width=120),
        ]
    else:  # Charge Type
        base = [
            col("charge_type",   "Charge Type",   "Data",     width=150),
        ]

    return base + [
        col("item_count",    "Items",          "Int",      width=80),
        col("total_qty",     "Total Qty",      "Float",    width=90),
        col("total_revenue", "Revenue",        "Currency", width=130),
        col("total_payments","Payments",       "Currency", width=130),
        col("outstanding",   "Outstanding",    "Currency", width=120),
        col("pct_of_total",  "% of Total",     "Percent",  width=110),
    ]


def _data(from_date, to_date, group_by):
    base_cond = "fi.date BETWEEN %(from_date)s AND %(to_date)s"
    args = {"from_date": str(from_date), "to_date": str(to_date)}

    if group_by == "Day":
        group_expr  = "fi.date, fi.charge_type"
        select_extra = "fi.date AS period, fi.charge_type,"
        order_by     = "fi.date, fi.charge_type"
    elif group_by == "Month":
        group_expr   = "DATE_FORMAT(fi.date, '%%Y-%%m'), fi.charge_type"
        select_extra = "DATE_FORMAT(fi.date, '%%Y-%%m') AS period, fi.charge_type,"
        order_by     = "period, fi.charge_type"
    else:
        group_expr   = "fi.charge_type"
        select_extra = "fi.charge_type,"
        order_by     = "total_revenue DESC"

    rows = frappe.db.sql("""
        SELECT
            {select_extra}
            COUNT(*)                    AS item_count,
            SUM(fi.quantity)            AS total_qty,
            SUM(fi.amount)              AS total_revenue,
            0                           AS total_payments,
            0                           AS outstanding,
            0                           AS pct_of_total
        FROM `tabHotel Folio Item` fi
        WHERE {base_cond}
        GROUP BY {group_expr}
        ORDER BY {order_by}
    """.format(
        select_extra=select_extra,
        base_cond=base_cond,
        group_expr=group_expr,
        order_by=order_by,
    ), args, as_dict=True)

    # Enrich with payments per charge_type (approximation: allocate proportionally)
    grand = sum(float(r.get("total_revenue") or 0) for r in rows) or 1

    # Total payments in the period
    total_paid = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0)
        FROM `tabHotel Payment`
        WHERE payment_date BETWEEN %(from_date)s AND %(to_date)s
          AND docstatus != 2
    """, args)[0][0] or 0

    for r in rows:
        rev  = float(r.get("total_revenue") or 0)
        pct  = rev / grand
        paid = float(total_paid) * pct
        r["total_revenue"]  = rev
        r["total_payments"] = round(paid, 2)
        r["outstanding"]    = round(rev - paid, 2)
        r["pct_of_total"]   = round(pct * 100, 1)

    return rows
