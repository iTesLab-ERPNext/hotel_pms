# Hotel PMS

![Frappe](https://img.shields.io/badge/Frappe-v15-blue) ![ERPNext](https://img.shields.io/badge/ERPNext-v15-green) ![License](https://img.shields.io/badge/license-MIT-yellow)

A full-featured **Hotel Property Management System** built as a custom Frappe/ERPNext app. Covers reservations, check-in/out, folio billing, housekeeping, and reporting.

---

## Features

- **Reservations** — Multi-room bookings, tentative/confirmed/cancelled states, booking source tracking, family member records, special requests
- **Check-In / Check-Out** — Walk-in and reservation-based check-in, automated folio creation, force-checkout with balance override
- **Folio & Billing** — Per-stay folios, charge posting by type (Room, F&B, Laundry, Spa, …), void charges, payment allocation (Cash, Card, Transfer, …)
- **Room Board** — Live colour-coded grid by floor, KPI header (occupancy %, arrivals, departures), auto-refreshes every 60 s
- **Housekeeping** — Task management (Daily Cleaning, Deep Clean, Turndown, Inspection), assignment to staff, status tracking
- **Rate Plans & Seasons** — Seasonal rate multipliers, meal-plan variants (BB, HB, FB, AI)
- **Reports** — Room Occupancy (ADR, RevPAR), Arrival/Departure, Revenue by Charge Type
- **Scheduler** — Auto no-show, nightly room-charge posting, hourly room status sync
- **Seed Demo Data** — One-click page that creates room types, rooms, services, booking sources and sample reservations

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | ≥ 3.10 |
| Node.js | ≥ 18 |
| Frappe Framework | v15 |
| ERPNext | v15 |
| MariaDB | ≥ 10.6 |

---

## Installation

### 1. Get the app

```bash
cd /path/to/frappe-bench
bench get-app https://github.com/your-org/hotel_pms
```

### 2. Install on a site

```bash
bench --site your.site.com install-app hotel_pms
```

### 3. Run migrations

```bash
bench --site your.site.com migrate
```

### 4. Restart bench

```bash
bench restart
```

---

## Post-Install: Seed Demo Data

1. Open your site in the browser.
2. Navigate to **Hotel PMS → Configuration → Seed Demo Data** (or go to `/app/seed_demo_data`).
3. Click **Seed All Demo Data**.

This creates:
- 7 room types (Standard, Deluxe, Superior, Junior Suite, Suite, Family, Accessible)
- 19 rooms across 5 floors
- 10 services (Breakfast, Lunch, Dinner, Laundry, Spa, …)
- 9 booking sources (Direct, Booking.com, Expedia, Airbnb, …)
- 5 sample customers
- 5 sample reservations (mix of Confirmed, Pending, Checked In)

The operation is idempotent — existing records are skipped.

---

## Module Overview

| Module | Key DocTypes |
|---|---|
| Front Desk | Hotel Reservation, Hotel Stay, Hotel Folio, Hotel Payment Allocation |
| Rooms | Hotel Room, Hotel Room Type, Hotel Room Movement |
| Housekeeping | Hotel Housekeeping |
| Configuration | Hotel Service, Hotel Season, Hotel Rate Plan, Hotel Booking Source |
| Reports | Room Occupancy Report, Arrival Departure Report, Revenue by Charge Type |

---

## DocType Reference

| DocType | Type | Description |
|---|---|---|
| Hotel Room Type | Master | Room categories with base rate and max occupancy |
| Hotel Room | Master | Individual rooms with floor, status, rate |
| Hotel Booking Source | Master | OTA / direct channels with commission % |
| Hotel Season | Master | Date ranges with rate multiplier |
| Hotel Rate Plan | Master | Room-type + season + meal-plan pricing |
| Hotel Service | Master | Billable services (F&B, Laundry, Spa, …) |
| Hotel Customer Category | Master | Guest segments |
| Hotel Family Type | Master | Family composition types |
| Hotel Reservation | Transactional | Booking with rooms, packages, family members |
| Hotel Reservation Room | Child | Rooms within a reservation |
| Hotel Reservation Package | Child | Services included in a reservation |
| Hotel Reservation Family | Child | Family members on a reservation |
| Hotel Stay | Transactional | Active in-house guest stay |
| Hotel Folio | Transactional | Guest bill (charges + payments) |
| Hotel Folio Item | Child | Single charge line on a folio |
| Hotel Payment Allocation | Submittable | Payment posted to a folio |
| Hotel Housekeeping | Transactional | Room cleaning / inspection task |
| Hotel Room Movement | Transactional | Room-change record |
| Hotel Package Item | Child | Generic package line item |

---

## API Reference

All methods are whitelisted (callable via `frappe.call`).

### Availability
- `hotel_pms.hotel_pms.api.availability.get_available_rooms(arrival_date, departure_date, room_type=None)`
- `hotel_pms.hotel_pms.api.availability.check_availability(arrival_date, departure_date, room_type=None)`

### Check-In
- `hotel_pms.hotel_pms.api.checkin.checkin_from_reservation(reservation_name, room=None)`
- `hotel_pms.hotel_pms.api.checkin.walkin_checkin(guest_name, room, nights=1, rate_per_night=None)`

### Check-Out
- `hotel_pms.hotel_pms.api.checkout.checkout_stay(stay_name, force=False)`
- `hotel_pms.hotel_pms.api.checkout.get_checkout_summary(stay_name)`

### Folio
- `hotel_pms.hotel_pms.api.folio.add_charge(folio_name, charge_type, description, amount, qty=1)`
- `hotel_pms.hotel_pms.api.folio.void_charge(folio_name, row_name)`
- `hotel_pms.hotel_pms.api.folio.get_folio_details(folio_name)`

### Payment
- `hotel_pms.hotel_pms.api.payment.post_payment(folio_name, payment_method, amount, reference=None)`
- `hotel_pms.hotel_pms.api.payment.get_payment_methods()`

### Reservation
- `hotel_pms.hotel_pms.api.reservation.confirm_reservation(reservation_name)`
- `hotel_pms.hotel_pms.api.reservation.cancel_reservation(reservation_name, reason=None)`
- `hotel_pms.hotel_pms.api.reservation.mark_no_show(reservation_name)`
- `hotel_pms.hotel_pms.api.reservation.get_arrivals(date=None)`
- `hotel_pms.hotel_pms.api.reservation.get_departures(date=None)`
- `hotel_pms.hotel_pms.api.reservation.get_in_house(date=None)`

### Room Board
- `hotel_pms.hotel_pms.api.room_board.get_room_board()`
- `hotel_pms.hotel_pms.api.room_board.get_room_stats()`

---

## Scheduler Events

| Frequency | Task |
|---|---|
| Daily | `tasks.auto_no_show` — marks overdue Confirmed reservations as No Show |
| Daily | `tasks.auto_post_room_charges` — posts room charge to all open folios |
| Hourly | `tasks.update_room_statuses` — marks Occupied rooms Available when stay is checked out |

---

## Roles

| Role | Description |
|---|---|
| Hotel Administrator | Full access to all doctypes |
| Hotel Manager | Read/write; cannot delete masters |
| Front Desk | Reservations, stays, folios |
| Housekeeping | Room status, housekeeping tasks |
| Cashier | Folio charges and payments |
| Night Audit | Audit access |
| Revenue Manager | Rate plans, seasons, reports |
| Food & Beverage | F&B services |
| Concierge | Read-only guest info |

---

## Development Notes

- App Python package: `hotel_pms/` (top level)
- Frappe module: `hotel_pms/hotel_pms/` (matches `modules.txt` entry `Hotel PMS`)
- Patches run automatically on `bench migrate`
- Frontend pages use plain Frappe JS (no build step required)
- `public/build.json` is intentionally empty (`{}`)

---

## License

MIT — see [LICENSE](LICENSE)

---

*Developed by [iTesLab](mailto:info@iteslab.com)*
