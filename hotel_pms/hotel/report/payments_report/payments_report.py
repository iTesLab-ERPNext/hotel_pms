import frappe
from frappe.utils import nowdate, add_days


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Payment", "fieldname": "name", "fieldtype": "Link", "options": "Hotel Payment", "width": 120},
        {"label": "Date", "fieldname": "payment_date", "fieldtype": "Date", "width": 100},
        {"label": "Customer", "fieldname": "customer_name", "fieldtype": "Data", "width": 160},
        {"label": "Reservation", "fieldname": "reservation", "fieldtype": "Link", "options": "Hotel Reservation", "width": 130},
        {"label": "Folio", "fieldname": "folio", "fieldtype": "Link", "options": "Hotel Folio", "width": 110},
        {"label": "Payment Type", "fieldname": "payment_type", "fieldtype": "Data", "width": 110},
        {"label": "Method", "fieldname": "payment_method", "fieldtype": "Data", "width": 120},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 110},
        {"label": "Reference", "fieldname": "reference", "fieldtype": "Data", "width": 130},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 90},
    ]


def get_data(filters):
    conditions = ""
    args = {}

    if filters.get("from_date"):
        conditions += " AND p.payment_date >= %(from_date)s"
        args["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions += " AND p.payment_date <= %(to_date)s"
        args["to_date"] = filters["to_date"]
    if filters.get("payment_method"):
        conditions += " AND p.payment_method = %(payment_method)s"
        args["payment_method"] = filters["payment_method"]
    if filters.get("customer"):
        conditions += " AND p.customer = %(customer)s"
        args["customer"] = filters["customer"]

    rows = frappe.db.sql("""
        SELECT
            p.name,
            p.payment_date,
            hc.full_name as customer_name,
            p.reservation,
            p.folio,
            p.payment_type,
            p.payment_method,
            p.amount,
            p.reference,
            CASE p.docstatus
                WHEN 0 THEN 'Draft'
                WHEN 1 THEN 'Submitted'
                WHEN 2 THEN 'Cancelled'
            END as status
        FROM `tabHotel Payment` p
        LEFT JOIN `tabHotel Customer` hc ON hc.name = p.customer
        WHERE 1=1 {conditions}
        ORDER BY p.payment_date DESC, p.name DESC
    """.format(conditions=conditions), args, as_dict=True)

    return rows
