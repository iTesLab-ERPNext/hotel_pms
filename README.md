# Hotel PMS — Frappe v15

A complete Hotel Property Management System built for **Frappe Framework v15**.

> Does **NOT** require ERPNext.

## Features

- Hotel Reservations with double-booking prevention
- Customer management with categories and family types
- Room Types and Rooms with status tracking
- Reservation Packages (Room Only, BB, HB, FB, Family Weekend, Adventure)
- Check-in to Stay to Folio to Checkout workflow
- Room Movement during active stays
- Guest Folio with service charges
- Payment management (Cash, Card, Bank Transfer, Cheque)
- Housekeeping workflow (Dirty to Cleaning to Clean to Available)
- Room Calendar / Availability API
- Dashboard KPIs
- Role-based permissions (Hotel Manager, Front Desk, Housekeeping Staff, Hotel Cashier)
- Complete demo seed data

## Installation

```bash
# 1. Get app
bench get-app https://github.com/your-org/hotel_pms

# 2. Install on site
bench --site your-site.localhost install-app hotel_pms

# 3. Migrate
bench --site your-site.localhost migrate

# 4. Load demo data (optional)
bench --site your-site.localhost execute hotel_pms.fixtures.seed_data.create_demo_data
```

## DocTypes

| DocType | Description |
|---|---|
| Hotel Customer | Guest profile |
| Hotel Customer Category | Customer categories |
| Hotel Family Type | Family type lookup |
| Hotel Room Type | Room type definitions |
| Hotel Room | Individual rooms |
| Hotel Package | Reservation packages |
| Hotel Package Item | Package service items |
| Hotel Reservation | Main reservation |
| Hotel Reservation Room | Rooms in reservation |
| Hotel Reservation Guest | Guest families |
| Hotel Stay | Active stay record |
| Hotel Room Movement | Room change history |
| Hotel Service | Available services |
| Hotel Folio | Guest billing folio |
| Hotel Folio Item | Folio charge lines |
| Hotel Payment | Payments |
| Hotel Housekeeping | Housekeeping tasks |

## Roles

| Role | Permissions |
|---|---|
| Hotel Manager | Full access |
| Front Desk | Reservations, Check-in, Folio |
| Housekeeping Staff | Rooms, Housekeeping |
| Hotel Cashier | Folio, Payments |

## Workflow

```
Customer -> Reservation -> Confirm
         -> Check-in -> Stay + Folio
         -> Add Charges -> Payment
         -> Checkout -> Housekeeping -> Room Available
```

## API

```python
# Check availability
frappe.call('hotel_pms.api.availability.get_available_rooms',
    args={arrival_date, departure_date, room_type})

# Room calendar
frappe.call('hotel_pms.api.availability.get_room_calendar',
    args={from_date, to_date})

# Check-in
frappe.call('hotel_pms.api.checkin.checkin',
    args={reservation})

# Checkout
frappe.call('hotel_pms.api.checkout.checkout',
    args={stay})

# Room movement
frappe.call('hotel_pms.api.movement.move_room',
    args={stay, new_room, reason, new_rate})

# Add folio charge
frappe.call('hotel_pms.api.folio.add_charge',
    args={folio, service, quantity, rate})

# Add payment
frappe.call('hotel_pms.api.payment.add_payment',
    args={folio, customer, amount, payment_method})
```

## Tests

```bash
bench run-tests --app hotel_pms
```
