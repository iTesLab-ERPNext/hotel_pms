# Hotel PMS — Frappe v15 App

A production-quality Hotel Property Management System built as a Frappe v15 application.

## Features

- **18 DocTypes** covering rooms, reservations, guests, folios, payments, housekeeping, and more
- **Dashboard** with live room status, today's arrivals/departures, financial summaries
- **Room Planning Board** — visual Gantt-style calendar showing room occupancy
- **Full API layer** — whitelisted server methods for check-in, check-out, room move, folio charges, payments
- **6 Script Reports** — Occupancy, Reservations, Arrivals, Departures, Revenue, Payments
- **Workspace** with quick-access shortcuts to all modules
- **Seed data system** — 20 rooms, 15 customers, 10 reservations, active stays with folios and payments
- **Test Data page** — UI to add/delete/reset test data with log output
- **Automated test suite** — 12 tests covering all core operations

---

## Installation

```bash
# From your bench directory
bench get-app hotel_pms /path/to/hotel_pms
bench --site yoursite install-app hotel_pms
```

Or install from a local directory:

```bash
bench pip install -e /path/to/hotel_pms
bench --site yoursite install-app hotel_pms
```

---

## Quick Start

1. Install the app (see above)
2. Navigate to the **Hotel PMS** workspace
3. Load test data via the **Test Data** page (or Dashboard → Test Data)
4. Explore the **Dashboard** and **Room Planning** pages

---

## DocTypes

| DocType | Description |
|---|---|
| Hotel Customer Category | Categories: Individual, Family, Corporate, VIP, Agency, Group |
| Hotel Family Type | Family types: Single, Couple, Family, Large Family, Group |
| Hotel Room Type | Room types with capacities and base prices |
| Hotel Customer | Guest profiles with categories, nationality, ID documents |
| Hotel Room | Physical rooms with status and housekeeping tracking |
| Hotel Reservation | Main reservation with rooms, families, packages |
| Hotel Reservation Room | Child: rooms per reservation |
| Hotel Reservation Family | Child: family groups per reservation |
| Hotel Reservation Guest | Child: individual guest details |
| Hotel Package | Packages combining services |
| Hotel Package Item | Child: package service items |
| Hotel Service | Individual services with rates |
| Hotel Stay | Active/completed stays per room per reservation |
| Hotel Room Movement | Room-to-room guest transfers |
| Hotel Folio | Bill for a stay, with itemised charges |
| Hotel Folio Item | Child: individual charge lines |
| Hotel Payment | Payments (cash, card, bank transfer) linked to folios |
| Hotel Housekeeping | Housekeeping status change log |

---

## API Methods

All methods are `@frappe.whitelist()` and available at `hotel_pms.api.hotel_api.*`:

| Method | Description |
|---|---|
| `get_dashboard_data()` | All stats for the dashboard |
| `get_room_availability(arrival, departure, room_type?)` | Available rooms for date range |
| `get_room_calendar(from_date, to_date, room?, room_type?)` | Calendar data |
| `get_planning_board(from_date, days)` | Room planning board data |
| `check_in(reservation)` | Creates stays, updates room status, creates folios |
| `check_out(stay_name)` | Closes stay, sets room to Cleaning, closes folio |
| `move_room(stay_name, new_room, reason?, new_rate?)` | Move guest to different room |
| `add_folio_charge(folio, charge_type, description, qty, rate, ...)` | Add charge to folio |
| `create_payment(customer, amount, method, ...)` | Record payment |
| `get_folio_details(reservation?, stay?)` | Folio with items and payments |
| `update_housekeeping_status(room, new_status, notes?)` | Update room HK status |

---

## Seed Data (bench command)

```bash
bench --site yoursite execute hotel_pms.setup.seed_demo_data.seed
bench --site yoursite execute hotel_pms.setup.seed_demo_data.delete_test_data
```

---

## Running Tests

```bash
bench run-tests --app hotel_pms --module hotel_pms.tests.test_hotel_pms
```

---

## Roles

| Role | Access |
|---|---|
| Hotel Manager | Full access to all DocTypes |
| Front Desk | Customers, Reservations, Rooms, Stays |
| Cashier | Folios, Payments |
| Housekeeping | Rooms, Housekeeping records |

---

## License

MIT
