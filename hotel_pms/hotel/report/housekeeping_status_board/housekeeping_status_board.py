"""
Housekeeping Status Board
--------------------------
Complete view of every room's housekeeping state — who is cleaning,
which rooms are ready, and which need inspection.
"""
import frappe
from hotel_pms.hotel.report_utils import col, summary


def execute(filters=None):
    filters = filters or {}
    columns = _columns()
    rows    = _data(filters)

    # Summary counters
    counts = {}
    for r in rows:
        k = r.get("housekeeping_status") or "Unknown"
        counts[k] = counts.get(k, 0) + 1

    report_summary = [
        summary(counts.get("Dirty",        0), "Dirty",        "Int", "Red"),
        summary(counts.get("Cleaning",     0), "Cleaning",     "Int", "Orange"),
        summary(counts.get("Inspected",    0), "Inspected",    "Int", "Blue"),
        summary(counts.get("Clean",        0), "Clean",        "Int", "Green"),
        summary(counts.get("Out of Service",0),"Out of Service","Int","Grey"),
    ]
    return columns, rows, None, None, report_summary


def _columns():
    return [
        col("room",                 "Room",           "Link", options="Hotel Room", width=100),
        col("room_number",          "Room No.",       "Data", width=80),
        col("floor",                "Floor",          "Int",  width=60),
        col("room_type",            "Room Type",      "Data", width=130),
        col("room_status",          "Room Status",    "Data", width=110),
        col("housekeeping_status",  "HK Status",      "Data", width=110),
        col("guest_name",           "Current Guest",  "Data", width=160),
        col("expected_checkout",    "Checkout",       "Date", width=100),
        col("last_hk",              "Last HK Task",   "Link", options="Hotel Housekeeping", width=130),
        col("last_hk_date",         "HK Date",        "Datetime", width=140),
        col("last_hk_assignee",     "Assigned To",    "Data", width=130),
        col("last_hk_notes",        "Notes",          "Data", width=200),
    ]


def _data(filters):
    floor    = filters.get("floor")
    hk_stat  = filters.get("housekeeping_status")
    rm_stat  = filters.get("room_status")

    conds = ["1=1"]
    args  = {}
    if floor:
        conds.append("hr.floor = %(floor)s")
        args["floor"] = floor
    if hk_stat:
        conds.append("hr.housekeeping_status = %(hk_stat)s")
        args["hk_stat"] = hk_stat
    if rm_stat:
        conds.append("hr.status = %(rm_stat)s")
        args["rm_stat"] = rm_stat

    where = " AND ".join(conds)

    rooms = frappe.db.sql("""
        SELECT
            hr.name            AS room,
            hr.room_number,
            hr.floor,
            hrt.room_type      AS room_type,
            hr.status          AS room_status,
            hr.housekeeping_status
        FROM `tabHotel Room` hr
        LEFT JOIN `tabHotel Room Type` hrt ON hrt.name = hr.room_type
        WHERE hr.active = 1 AND {where}
        ORDER BY hr.floor ASC, hr.room_number ASC
    """.format(where=where), args, as_dict=True)

    room_names = [r["room"] for r in rooms]
    if not room_names:
        return []

    # Active stay info (guest + checkout)
    stays = frappe.db.sql("""
        SELECT hs.room, hc.full_name AS guest_name, hs.expected_checkout
        FROM `tabHotel Stay` hs
        LEFT JOIN `tabHotel Customer` hc ON hc.name = hs.customer
        WHERE hs.status = 'Active' AND hs.room IN %(rooms)s
    """, {"rooms": room_names}, as_dict=True)
    stay_map = {s.room: s for s in stays}

    # Latest housekeeping task per room
    hk_tasks = frappe.db.sql("""
        SELECT hk.room, hk.name AS last_hk, hk.modified AS last_hk_date,
               hk.assigned_to AS last_hk_assignee, hk.notes AS last_hk_notes
        FROM `tabHotel Housekeeping` hk
        WHERE hk.room IN %(rooms)s
          AND hk.modified = (
              SELECT MAX(hk2.modified)
              FROM `tabHotel Housekeeping` hk2
              WHERE hk2.room = hk.room
          )
    """, {"rooms": room_names}, as_dict=True)
    hk_map = {t.room: t for t in hk_tasks}

    for r in rooms:
        stay = stay_map.get(r["room"]) or frappe._dict()
        hk   = hk_map.get(r["room"])  or frappe._dict()
        r.update({
            "guest_name":        stay.get("guest_name")     or "",
            "expected_checkout": stay.get("expected_checkout") or "",
            "last_hk":           hk.get("last_hk")          or "",
            "last_hk_date":      hk.get("last_hk_date")     or "",
            "last_hk_assignee":  hk.get("last_hk_assignee") or "",
            "last_hk_notes":     hk.get("last_hk_notes")    or "",
        })

    return rooms
