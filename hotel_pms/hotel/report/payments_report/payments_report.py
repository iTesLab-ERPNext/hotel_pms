"""Payments Report — payment transactions for a date range."""
import frappe
from hotel_pms.hotel.report_utils import col, summary, normalize_dates


def execute(filters=None):
    filters = filters or {}
    from_date, to_date = normalize_dates(filters, default_days=30)
    columns = _columns()
    rows = _data(from_date, to_date, filters)

    total = sum(r["amount"] for r in rows)
    report_summary = [
        summary(total,     "Total Collected", "Currency", "Green" if total > 0 else "Grey"),
        summary(len(rows), "Transactions",    "Int"),
    ]
    return columns, rows, None, None, report_summary


def _columns():
    return [
        col("name",           "Payment",        "Link",     options="Hotel Payment", width=130),
        col("payment_date",   "Date",           "Date",     width=100),
        col("customer_name",  "Customer",       "Data",     width=160),
        col("payment_type",   "Type",           "Data",     width=100),
        col("payment_method", "Method",         "Data",     width=110),
        col("amount",         "Amount",         "Currency", width=110),
        col("reference",      "Reference",      "Data",     width=130),
        col("folio",          "Folio",          "Link",     options="Hotel Folio", width=130),
    ]


def _data(from_date, to_date, filters):
    conditions = "p.payment_date BETWEEN %(from_date)s AND %(to_date)s"
    args = {"from_date": str(from_date), "to_date": str(to_date)}

    if filters.get("payment_method"):
        conditions += " AND p.payment_method = %(payment_method)s"
        args["payment_method"] = filters["payment_method"]
    if filters.get("customer"):
        conditions += " AND p.customer = %(customer)s"
        args["customer"] = filters["customer"]

    return frappe.db.sql("""
        SELECT p.name, p.payment_date, hc.full_name as customer_name,
               p.payment_type, p.payment_method, p.amount, p.reference, p.folio
        FROM `tabHotel Payment` p
        LEFT JOIN `tabHotel Customer` hc ON hc.name = p.customer
        WHERE p.docstatus != 2 AND {conditions}
        ORDER BY p.payment_date DESC, p.name DESC
    """.format(conditions=conditions), args, as_dict=True)
