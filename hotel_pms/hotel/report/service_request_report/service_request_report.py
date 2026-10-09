"""
Service Request Report
-----------------------
Lists all non-room folio charges (services, F&B, laundry, etc.)
for a date range — useful for tracking service delivery and revenue.
"""
import frappe
from hotel_pms.hotel.report_utils import col, summary, normalize_dates


def execute(filters=None):
    filters = filters or {}
    from_date, to_date = normalize_dates(filters, default_days=30)
    columns = _columns()
    rows    = _data(from_date, to_date, filters)

    total_amount = sum(r["amount"] for r in rows)
    total_qty    = sum(r["quantity"] for r in rows)

    # Group by charge type for summary
    by_type = {}
    for r in rows:
        k = r.get("charge_type") or "Other"
        by_type[k] = by_type.get(k, 0.0) + r["amount"]

    report_summary = [
        summary(len(rows),     "Total Items",   "Int",      "Blue"),
        summary(total_qty,     "Total Qty",     "Float",    "Blue"),
        summary(total_amount,  "Total Revenue", "Currency", "Green" if total_amount else "Grey"),
    ]
    return columns, rows, None, None, report_summary


def _columns():
    return [
        col("folio_item",    "Item",          "Link",     options="Hotel Folio Item", width=130),
        col("date",          "Date",          "Date",     width=100),
        col("folio",         "Folio",         "Link",     options="Hotel Folio",      width=130),
        col("stay",          "Stay",          "Link",     options="Hotel Stay",       width=130),
        col("room_number",   "Room",          "Data",     width=80),
        col("guest_name",    "Guest",         "Data",     width=170),
        col("charge_type",   "Charge Type",   "Data",     width=110),
        col("service",       "Service",       "Link",     options="Hotel Service",    width=130),
        col("description",   "Description",   "Data",     width=200),
        col("quantity",      "Qty",           "Float",    width=70),
        col("rate",          "Rate",          "Currency", width=100),
        col("amount",        "Amount",        "Currency", width=110),
    ]


def _data(from_date, to_date, filters):
    svc_filter  = filters.get("service")
    type_filter = filters.get("charge_type")

    conds = [
        "fi.date BETWEEN %(from_date)s AND %(to_date)s",
        "fi.charge_type != 'Room'",           # room charges belong to occupancy report
    ]
    args = {"from_date": str(from_date), "to_date": str(to_date)}

    if svc_filter:
        conds.append("fi.service = %(service)s")
        args["service"] = svc_filter
    if type_filter:
        conds.append("fi.charge_type = %(charge_type)s")
        args["charge_type"] = type_filter

    where = " AND ".join(conds)

    return frappe.db.sql("""
        SELECT
            fi.name          AS folio_item,
            fi.date,
            fi.parent        AS folio,
            hf.stay,
            hr.room_number,
            hc.full_name     AS guest_name,
            fi.charge_type,
            fi.service,
            fi.description,
            fi.quantity,
            fi.rate,
            fi.amount
        FROM `tabHotel Folio Item` fi
        JOIN `tabHotel Folio`    hf ON hf.name = fi.parent
        LEFT JOIN `tabHotel Stay` hs ON hs.name = hf.stay
        LEFT JOIN `tabHotel Customer` hc ON hc.name = COALESCE(hs.customer, hf.customer)
        LEFT JOIN `tabHotel Room`    hr ON hr.name = hs.room
        WHERE {where}
        ORDER BY fi.date DESC, fi.name DESC
    """.format(where=where), args, as_dict=True)
