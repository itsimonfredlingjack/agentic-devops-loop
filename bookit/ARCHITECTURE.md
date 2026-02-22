# BookIt — Architecture Overview

## What It Is

A multi-tenant booking system. Businesses create a tenant (e.g. "Klipp & Trim"), define services (Herrklippning, Damklippning, Färgning), generate time slots, and customers book via a public page. Supports Stripe payments, recurring bookings, email notifications, and a statistics dashboard.

```
┌──────────────────────────────────┐
│         ai-server2 (Ubuntu)      │
│                                  │
│  ┌────────────┐  ┌────────────┐  │
│  │  Frontend   │  │  Backend   │  │
│  │  React/Vite │  │  FastAPI   │  │
│  │  :5173      │──│  :8001     │  │
│  │             │  │            │  │
│  │  Zustand    │  │  SQLite    │  │
│  │  Router     │  │  Stripe    │  │
│  │  CSS Modules│  │  SMTP      │  │
│  └────────────┘  └────────────┘  │
│                       │          │
│                       ▼          │
│              ┌──────────────┐    │
│              │  bookit.db   │    │
│              │  (SQLite)    │    │
│              └──────────────┘    │
└──────────────────────────────────┘
         │                │
         ▼                ▼
   Stripe API       Jira Cloud
   (payments)    (future: via voice)
```

## Everything Runs on One Machine

Unlike the voice app (split Mac/server), BookIt runs entirely on **ai-server2**.

| | |
|---|---|
| **Machine** | ai-server2 — 6 cores, 15 GB RAM, Ubuntu 24.04 |
| **Backend** | FastAPI + aiosqlite on port `:8001` |
| **Frontend** | React + Vite on port `:5173` (proxies `/api` → `:8001`) |
| **Database** | SQLite file: `backend/bookit.db` |
| **Code path** | `/home/ai-server2/04-voice-mode-4-loop/bookit/` |

## Tech Stack

### Backend
| Tech | Purpose |
|------|---------|
| **FastAPI** | REST API framework (async) |
| **aiosqlite** | Async SQLite access |
| **Pydantic v2** | Request/response validation + settings |
| **Stripe** | Payment processing (checkout sessions, webhooks) |
| **aiosmtplib** | Email notifications (booking confirmation/cancellation) |
| **pytest + httpx** | Async test suite |
| **ruff** | Linting + formatting |

### Frontend
| Tech | Purpose |
|------|---------|
| **React 18** | UI framework |
| **TypeScript** | Type safety |
| **Vite** | Build tool + dev server |
| **Zustand** | State management |
| **react-router-dom** | Client-side routing |
| **CSS Modules** | Scoped component styles (glassmorphism design) |

## Database Schema

```
tenants
├── id (PK)
├── name            "Klipp & Trim"
├── slug            "klipp-trim"    ← used in URLs
└── created_at

services
├── id (PK)
├── tenant_id (FK → tenants)
├── name            "Herrklippning"
├── duration_min    30
├── capacity        1
├── price_cents     0 (or Stripe amount)
└── created_at

slots
├── id (PK)
├── service_id (FK → services)
├── start_time      "2026-02-20T09:00:00"
├── end_time        "2026-02-20T09:30:00"
├── capacity        1
├── booked_count    0
└── created_at

bookings
├── id (PK)
├── slot_id (FK → slots)
├── customer_name
├── customer_email
├── customer_phone
├── stripe_session_id
├── payment_status  "none" | "paid" | "refunded"
├── recurring_rule_id (FK → recurring_rules)
├── status          "confirmed" | "cancelled"
└── created_at

recurring_rules
├── id (PK)
├── frequency       "weekly" | "biweekly" | "monthly"
├── occurrences     4
└── created_at
```

## API Endpoints

### Tenants
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tenants/:slug` | Get tenant by slug |
| POST | `/api/tenants` | Create new tenant |

### Services
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tenants/:slug/services` | List services |
| POST | `/api/tenants/:slug/services` | Create service |

### Slots
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tenants/:slug/services/:id/slots?date=YYYY-MM-DD` | Get slots for date |
| POST | `/api/tenants/:slug/services/:id/slots/generate` | Bulk generate slots |

### Bookings
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/bookings` | Create booking |
| DELETE | `/api/bookings/:id` | Cancel booking (24h deadline) |
| GET | `/api/bookings?email=...` | Get bookings by email |

### Public
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/book/:slug` | Public tenant view (services + available slots) |

### Payments (Stripe)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/bookings/checkout` | Create Stripe checkout session |
| GET | `/api/bookings/checkout/:session_id/status` | Check payment status |
| POST | `/api/payments/webhook` | Stripe webhook handler |

### Recurring
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/bookings/recurring` | Create recurring booking series |
| GET | `/api/bookings/recurring/:rule_id` | Get recurring rule |
| DELETE | `/api/bookings/recurring/:rule_id` | Cancel entire series |

### Statistics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tenants/:slug/stats?period=week\|month\|year` | Booking + revenue stats |

## Frontend Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/book/:slug` | PublicBookingPage | Customer-facing booking form |
| `/book/:slug/success` | BookingSuccess | Post-booking confirmation |
| `/admin/:slug` | AdminLayout → Calendar | Admin calendar view (default) |
| `/admin/:slug/bookings` | AdminLayout → MyBookings | Manage existing bookings |
| `/admin/:slug/manage` | AdminLayout → AdminPanel | Create services + generate slots |
| `/admin/:slug/stats` | AdminLayout → StatsDashboard | Revenue & booking statistics |
| `/` | Redirect → `/admin/demo` | Default redirect |

## Key Files

### Backend (`bookit/backend/`)

| File | Purpose |
|------|---------|
| `src/bookit/main.py` | FastAPI app, CORS, router registration |
| `src/bookit/config.py` | Pydantic settings (DB, SMTP, Stripe, CORS) |
| `src/bookit/database.py` | SQLite schema, migrations, connection manager |
| `src/bookit/routers/bookings.py` | CRUD + cancellation (24h deadline) |
| `src/bookit/routers/public.py` | Public booking view (no auth) |
| `src/bookit/routers/payments.py` | Stripe checkout + webhook |
| `src/bookit/routers/recurring.py` | Recurring booking series |
| `src/bookit/routers/stats.py` | Revenue + booking statistics |
| `src/bookit/services/booking_service.py` | Business logic: capacity check, booking creation |
| `src/bookit/services/payment_service.py` | Stripe session creation |
| `src/bookit/services/recurring_service.py` | Slot duplication for recurring rules |
| `src/bookit/services/notification_service.py` | Email sending (confirmation/cancellation) |
| `src/bookit/services/stats_service.py` | Statistics aggregation queries |
| `scripts/seed.py` | Demo data: "Klipp & Trim" + "Demo Salong" with 7 days of slots |

### Frontend (`bookit/frontend/`)

| File | Purpose |
|------|---------|
| `src/App.tsx` | Router setup (public + admin routes) |
| `src/stores/bookingStore.ts` | Zustand store (services, slots, bookings, actions) |
| `src/lib/api.ts` | Typed API client (all endpoints) |
| `src/pages/PublicBookingPage.tsx` | Customer booking flow |
| `src/pages/BookingSuccess.tsx` | Post-booking confirmation |
| `src/pages/AdminLayout.tsx` | Admin shell with navigation |
| `src/pages/StatsDashboard.tsx` | Charts + revenue stats |
| `src/components/Calendar.tsx` | Day view with slot availability |
| `src/components/BookingForm.tsx` | Name/email/phone form |
| `src/components/AdminPanel.tsx` | Service creation + slot generation |
| `src/components/MyBookings.tsx` | Booking list with cancel/recurring |

### Tests (`bookit/backend/tests/`)

| File | Covers |
|------|--------|
| `test_api.py` | Health check, tenant CRUD |
| `test_booking.py` | Booking creation, cancellation, capacity |
| `test_slots.py` | Slot generation, availability |
| `test_payments.py` | Stripe checkout flow |
| `test_recurring.py` | Recurring series creation/cancellation |
| `test_notifications.py` | Email sending |
| `test_public.py` | Public tenant view |
| `test_stats.py` | Statistics aggregation |

## Running It

```bash
# Backend
cd /home/ai-server2/04-voice-mode-4-loop/bookit/backend
source venv/bin/activate
uvicorn src.bookit.main:app --host 0.0.0.0 --port 8001 --reload

# Seed demo data (first time)
python -m scripts.seed

# Frontend (separate terminal)
cd /home/ai-server2/04-voice-mode-4-loop/bookit/frontend
npm run dev    # → http://localhost:5173

# Tests
cd backend && source venv/bin/activate
pytest tests/ -xvs

# Lint
ruff check . && ruff format --check .

# Type check frontend
cd frontend && npx tsc --noEmit
```

## Configuration (Environment Variables)

All prefixed with `BOOKIT_`:

| Variable | Default | Description |
|----------|---------|-------------|
| `BOOKIT_DATABASE_URL` | `bookit.db` | SQLite file path |
| `BOOKIT_CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins |
| `BOOKIT_CANCELLATION_DEADLINE_HOURS` | `24` | Hours before slot when cancel is blocked |
| `BOOKIT_EMAIL_ENABLED` | `false` | Enable SMTP notifications |
| `BOOKIT_SMTP_HOST` | `localhost` | SMTP server |
| `BOOKIT_SMTP_PORT` | `587` | SMTP port |
| `BOOKIT_SMTP_USER` | `""` | SMTP username |
| `BOOKIT_SMTP_PASSWORD` | `""` | SMTP password |
| `BOOKIT_STRIPE_ENABLED` | `false` | Enable Stripe payments |
| `BOOKIT_STRIPE_SECRET_KEY` | `""` | Stripe secret key |
| `BOOKIT_STRIPE_WEBHOOK_SECRET` | `""` | Stripe webhook signing secret |
| `BOOKIT_FRONTEND_URL` | `http://localhost:5173` | Used for Stripe redirect URLs |

## Features

- **Multi-tenant**: Each business gets a slug (`/book/klipp-trim`)
- **Service management**: Create services with duration, capacity, pricing
- **Slot generation**: Bulk generate slots for date ranges
- **Public booking page**: Shareable URL, no login required
- **Capacity tracking**: Prevents overbooking (booked_count vs capacity)
- **Cancellation**: 24-hour deadline enforcement
- **Stripe payments**: Checkout sessions with webhook confirmation
- **Recurring bookings**: Weekly/biweekly/monthly series with batch cancel
- **Email notifications**: Confirmation + cancellation emails (optional)
- **Statistics dashboard**: Booking counts + revenue by service and period
- **Glassmorphism UI**: Shared design language with the voice app
