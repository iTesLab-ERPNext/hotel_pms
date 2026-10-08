# Hotel PMS — Frappe / ERPNext Custom App

A full-featured **Property Management System** built as a Frappe custom app,
deeply integrated with ERPNext 15/16 (Customers, Items, Payment Entries).

---

## Features

| Area | Highlights |
|---|---|
| **Reservations** | Draft → Confirm → Deposit Paid → Check-in lifecycle; room availability conflict detection; family & room child tables |
| **Front Desk** | One-click check-in from reservation or walk-in; folio auto-created; real-time Room Board page |
| **Folio & Billing** | Itemised charge posting by type (Room, Food, Spa, Bar…); void support; daily auto-post of room charges |
| **Payments** | Hotel Payment Allocation (submittable); Cash, Card, Bank Transfer, Voucher, City Ledger, Deposit |
| **Housekeeping** | Task assignment with status flow (Pending → In Progress → Done → Inspected); auto-syncs room status |
| **Configuration** | Room Types, Rate Plans, Seasons, Services, Packages, Booking Sources, Customer Categories |
| **Reports** | Room Occupancy (ADR, RevPAR), Arrivals & Departures, Revenue by Charge Type |
| **Demo Data** | Seed page at `/hotel-pms/seed-demo-data` |

---

## DocTypes

```
Hotel Room Type          Hotel Room              Hotel Booking Source
Hotel Customer Category  Hotel Family Type       Hotel Service
Hotel Reservation Package  Hotel Package Item
Hotel Reservation        Hotel Reservation Room  Hotel Reservation Family
Hotel Stay               Hotel Folio             Hotel Folio Item
Hotel Payment Allocation Hotel Housekeeping      Hotel Room Movement
Hotel Rate Plan          Hotel Season
```

---

## Installation

### Prerequisites
- Frappe Framework v15 or v16
- ERPNext v15 or v16

### Steps

```bash
# 1. Get the app
bench get-app hotel_pms /path/to/hotel_pms
# or from GitHub:
# bench get-app hotel_pms https://github.com/your-org/hotel_pms

# 2. Install on your site
bench --site your-site.localhost install-app hotel_pms

# 3. Run migrations
bench --site your-site.localhost migrate

# 4. (Optional) Seed demo data
# Log in as Administrator, navigate to Hotel PMS → Seed Demo Data
```

### Manual install (no bench get-app)

```bash
# Copy the hotel_pms folder into your apps directory
cp -r hotel_pms /path/to/frappe-bench/apps/

# Register with pip
pip install -e /path/to/frappe-bench/apps/hotel_pms --break-system-packages

# Then install & migrate as above
```

---

## Workflow

```
Hotel Reservation (Confirmed)
        │
        ▼  checkin_from_reservation()
Hotel Stay (In House)  +  Hotel Folio (Open)
        │                       │
        │                       ├── Hotel Folio Item (charges)
        │                       └── Hotel Payment Allocation (payments)
        │
        ▼  stay.checkout()
Hotel Stay (Checked Out)
Hotel Folio (Closed)
Hotel Room (Dirty → Cleaning → Clean)
```

---

## API Endpoints (all `@frappe.whitelist()`)

| Module | Method |
|---|---|
| `hotel_pms.api.availability` | `get_available_rooms`, `check_availability` |
| `hotel_pms.api.checkin` | `checkin_from_reservation`, `walkin_checkin` |
| `hotel_pms.api.checkout` | `checkout_stay`, `get_checkout_summary` |
| `hotel_pms.api.folio` | `add_charge`, `void_charge`, `get_folio_details`, `post_room_charge` |
| `hotel_pms.api.payment` | `post_payment`, `get_payment_methods` |
| `hotel_pms.api.reservation` | `confirm_reservation`, `cancel_reservation`, `get_arrivals`, `get_departures`, `get_in_house` |
| `hotel_pms.api.room_board` | `get_room_board`, `get_room_stats` |
| `hotel_pms.api.seed_data` | `seed_all` |

---

## Roles

`Hotel Administrator`, `Front Desk`, `Hotel Manager`, `Housekeeping`,
`Cashier`, `Night Audit`, `Revenue Manager`, `Food & Beverage`, `Concierge`

---

## Scheduled Tasks

| Frequency | Task |
|---|---|
| Daily | Auto No-Show overdue reservations |
| Daily | Auto-post room charges to in-house folios |
| Hourly | Sync room status after checkouts |

---

## License

MIT
# hotel_pms
