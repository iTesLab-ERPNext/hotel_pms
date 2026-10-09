"""
In-House Guest Folio Summary
-----------------------------
Cashier / front-desk view of every active stay with its folio totals.
Flags unpaid balances so staff can follow up before checkout.
"""
import frappe
from hotel_pms.hotel.report_utils import col, summary


def execute(filters=None):
    filters = filters or {}
    columns = _columns()
    rows    = _data(filters)

    total_charges  = sum(r["total_charges"]  for r in rows)
    total_payments = sum(r["total_payments"] for r in rows)
    total_balance  = sum(r["balance"]        for r in rows)

    report_summary = [
        summary(len(rows),       "Active Stays",    "Int",      "Blue"),
        summary(total_charges,   "Total Charges",   "Currency", "Blue"),
        summary(total_payments,  "Total Payments",  "Currency", "Green"),
        summary(total_balance,   "Outstanding",     "Currency",
                "Red" if total_balance > 0 else "Green"),
    ]
    return columns, rows, None, None, report_summary


def _columns():
    return [
        col("stay",            "Stay",         "Link",     options="Hotel Stay",     width=130),
        col("reservation",     "Reservation",  "Link",     options="Hotel Reservation", width=130),
        col("guest_name",      "Guest",        "Data",     width=180),
        col("room_number",     "Room",         "Data",     width=80),
        col("room_type",       "Room Type",    "Data",     width=120),
        col("floor",           "Floor",        "Int",      width=60),
        col("checkin_date",    "Check-In",     "Datetime", width=140),
        col("expected_checkout","Checkout",    "Date",     width=100),
        col("nights_so_far",   "Nights",       "Int",      width=65),
        col("folio",           "Folio",        "Link",     options="Hotel Folio",    width=130),
        col("folio_status",    "Folio Status", "Data",     width=110),
        col("total_charges",   "Charges",      "Currency", width=110),
        col("total_payments",  "Payments",     "Currency", width=110),
        col("balance",         "Balance",      "Currency", width=110),
    ]


def _data(filters):
    room_type  = filters.get("room_type")
    floor      = filters.get("floor")
    bal_only   = filters.get("balance_due")

    conds = ["hs.status = 'Active'"]
    args  = {}

    if room_type:
        conds.append("hr.room_type = %(room_type)s")
        args["room_type"] = room_type
    if floor:
        conds.append("hr.floor = %(floor)s")
        args["floor"] = floor

    where = " AND ".join(conds)

    rows = frappe.db.sql("""
        SELECT
            hs.name            AS stay,
            hs.reservation,
            hc.full_name       AS guest_name,
            hr.room_number,
            hrt.room_type      AS room_type,
            hr.floor,
            hs.checkin_date,
            hs.expected_checkout,
            DATEDIFF(CURDATE(), DATE(hs.checkin_date)) AS nights_so_far,
            hf.name            AS folio,
            hf.status          AS folio_status,
            COALESCE(hf.total_charges, 0) AS total_charges,
            COALESCE(hf.total_payments, 0) AS total_payments,
            COALESCE(hf.balance,      0) AS balance
        FROM `tabHotel Stay` hs
        LEFT JOIN `tabHotel Customer` hc  ON hc.name  = hs.customer
        LEFT JOIN `tabHotel Room`     hr  ON hr.name  = hs.room
        LEFT JOIN `tabHotel Room Type` hrt ON hrt.name = hr.room_type
        LEFT JOIN `tabHotel Folio`    hf  ON hf.stay  = hs.name
        WHERE {where}
        ORDER BY hr.floor ASC, hr.room_number ASC
    """.format(where=where), args, as_dict=True)

    if bal_only:
        rows = [r for r in rows if (r.get("balance") or 0) > 0]

    return rows
