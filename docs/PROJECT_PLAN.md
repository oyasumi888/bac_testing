# BAC Tracker — Project Plan

## 1. Overview and scope

A full-stack web app that estimates and tracks a user's Blood Alcohol Concentration (BAC) in real time, using the Widmark formula.

**Core loop:** onboard (weight, biological sex) → tap "+1 Beer" / "+1 Shot" → see current BAC, colour-coded band and estimated sober time.

**Stack**

| Layer | Choice |
|---|---|
| Frontend | React (Vite), TanStack Query |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2 |
| Database | PostgreSQL 16 |
| Infrastructure | Docker / Docker Compose |

**Out of scope for the MVP:** email/password accounts, social features, food intake and absorption-rate modelling.

**Disclaimer requirement:** the UI must always state that the figure is an estimate and must not be used to decide whether it is safe to drive.

## 2. System architecture

```
┌──────────────┐   HTTP/JSON    ┌──────────────┐   SQLAlchemy   ┌──────────────┐
│  web (React) │ ─────────────▶ │ api (FastAPI)│ ─────────────▶ │ db (Postgres)│
│  :5173 (dev) │  /api/v1/*     │    :8000     │                │    :5432     │
└──────────────┘ ◀───────────── └──────────────┘ ◀───────────── └──────────────┘
```

- **Docker Compose services**
  - `db`: `postgres:16`, data in a named volume, credentials from `.env`.
  - `api`: FastAPI served by uvicorn. On startup it runs `alembic upgrade head`.
  - `web`: Vite dev server in development. In production the static build is served by nginx, which also reverse-proxies `/api` to `api`.
- **Request flow:** the browser only calls `/api/v1/*`. In dev, the Vite proxy forwards these calls to `api:8000`. In prod, nginx does the same. FastAPI is the only component that talks to Postgres.
- **Identity:** anonymous session. `POST /sessions` creates a user and returns an opaque token. The frontend stores it in `localStorage` and sends `Authorization: Bearer <token>` on every request.
- **Real-time:** BAC is **always computed on the backend**. The frontend re-fetches `GET /bac` right after every add or undo and polls it every 30 s, so the value decays visibly over time.

**Proposed repo layout**

```
backend/
  app/
    api/          # routers: sessions, me, drinks, consumptions, bac, health
    models/       # SQLAlchemy models
    schemas/      # Pydantic request/response models
    services/
      bac.py      # pure Widmark calculation
    config.py     # settings + Widmark constants
    db.py         # engine/session dependency
    main.py
  alembic/        # migrations (schema + catalog seed)
  tests/
  Dockerfile
frontend/
  src/
    api/          # fetch client
    components/
    pages/        # Onboarding, Tracker
    constants/    # BAC bands → colours
  Dockerfile
docker-compose.yml
.env.example
```

## 3. Widmark calculation (core logic)

**Alcohol per drink (grams)**

```
A_g = volume_ml × (abv_percent / 100) × 0.789      # 0.789 g/ml = ethanol density
```

**Widmark formula**

```
BAC% = A_g / (W_g × r) × 100 − β × t_hours
```

| Symbol | Meaning | Value |
|---|---|---|
| `W_g` | body weight in grams | `weight_kg × 1000` |
| `r` | Widmark distribution constant | 0.68 male, 0.55 female |
| `β` | elimination rate | 0.015 %/h |
| `t_hours` | time since drinking started | — |

**Multiple drinks, applied incrementally**

```
bac = 0
prev = first drink time
for drink in drinks sorted by consumed_at:
    bac = max(0, bac − β × hours(drink.consumed_at − prev))
    bac += drink.alcohol_g / (W_g × r) × 100
    prev = drink.consumed_at
bac = max(0, bac − β × hours(now − prev))
```

When drinks are close together, this gives the same result as plain Widmark. The `max(0, …)` stops elimination from going below zero during a sober gap between drinks. Without it, an afternoon beer would wrongly reduce the BAC of an evening drink.

**Outputs**
- `bac`: current BAC in %, rounded to 3 decimals.
- `band`: see the table below.
- `sober_at`: `now + bac / β` hours, or `null` when `bac == 0`.

**BAC bands** (contiguous ranges that close the gaps in the original thresholds)

| Band | Range | Colour |
|---|---|---|
| green | `< 0.03` | green |
| yellow | `0.03 – < 0.06` | yellow |
| orange | `0.06 – < 0.08` | orange |
| red | `≥ 0.08` | red |

**Worked example:** an 80 kg male drinks one 330 ml 5% beer.
`A_g = 330 × 0.05 × 0.789 = 13.02 g`, then `BAC = 13.02 / (80000 × 0.68) × 100 ≈ 0.024%` at t = 0. That is green, and it reaches 0 after about 1.6 h.

**Implementation notes**
- `services/bac.py` is a pure function, `calculate_bac(weight_kg, sex, drinks, now) -> BacResult`, with no DB or clock access. This makes it fully unit-testable.
- `r`, `β`, the ethanol density and the band boundaries live in `config.py` only. Both the frontend band colours and the backend use the band **name** returned by the API.

## 4. Database schema (PostgreSQL)

```
users 1 ──── N consumption_logs N ──── 1 drinks_catalog
```

### `users`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | `gen_random_uuid()` |
| `session_token` | TEXT UNIQUE NOT NULL | 32-byte urlsafe random; indexed |
| `weight_kg` | NUMERIC(5,1) NOT NULL | CHECK `weight_kg BETWEEN 20 AND 400` |
| `sex` | ENUM `biological_sex` ('male','female') NOT NULL | selects Widmark `r` |
| `created_at` | TIMESTAMPTZ NOT NULL | default `now()` |
| `updated_at` | TIMESTAMPTZ NOT NULL | default `now()`, updated on change |

### `drinks_catalog`
| Column | Type | Notes |
|---|---|---|
| `id` | SERIAL PK | |
| `name` | TEXT UNIQUE NOT NULL | e.g. "Beer" |
| `category` | ENUM `drink_category` ('beer','wine','spirit','cocktail','other') | |
| `volume_ml` | NUMERIC(6,1) NOT NULL | CHECK `> 0` |
| `abv_percent` | NUMERIC(4,1) NOT NULL | CHECK `BETWEEN 0 AND 100` |
| `icon` | TEXT NULL | emoji or asset key |
| `is_active` | BOOLEAN NOT NULL | default `true` |

### `consumption_logs`
| Column | Type | Notes |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `user_id` | UUID NOT NULL | FK → `users.id` ON DELETE CASCADE |
| `drink_id` | INT NOT NULL | FK → `drinks_catalog.id` |
| `consumed_at` | TIMESTAMPTZ NOT NULL | default `now()` |
| `volume_ml` | NUMERIC(6,1) NOT NULL | snapshot from catalog |
| `abv_percent` | NUMERIC(4,1) NOT NULL | snapshot from catalog |
| `alcohol_g` | NUMERIC(6,2) NOT NULL | computed at insert |

- Index: `(user_id, consumed_at)`, which supports "this user's drinks in the last N hours".
- The snapshot columns keep historical BAC values stable even if a catalog row is edited later.

### Catalog seed (Alembic data migration)

| Name | Category | Volume (ml) | ABV % |
|---|---|---|---|
| Beer | beer | 330 | 5.0 |
| Pint | beer | 568 | 5.0 |
| Light beer | beer | 355 | 4.2 |
| Cider | other | 330 | 4.5 |
| Hard seltzer | other | 355 | 5.0 |
| Wine (glass) | wine | 150 | 12.0 |
| Champagne | wine | 125 | 12.0 |
| Shot | spirit | 44 | 40.0 |
| Spirit + mixer | spirit | 250 | 7.0 |
| Margarita | cocktail | 200 | 13.0 |

## 5. REST API (`/api/v1`)

Every endpoint except `POST /sessions`, `GET /drinks` and `GET /health` requires `Authorization: Bearer <token>`.

| Method | Path | Request | Response |
|---|---|---|---|
| POST | `/sessions` | `{weight_kg, sex}` | `201 {token, user}` |
| GET | `/me` | — | `{id, weight_kg, sex}` |
| PATCH | `/me` | `{weight_kg?, sex?}` | updated user |
| GET | `/drinks` | — | `[{id, name, category, volume_ml, abv_percent, icon}]` (active only) |
| POST | `/consumptions` | `{drink_id, consumed_at?}` | `201 {id, drink_id, consumed_at, alcohol_g}` |
| GET | `/consumptions?since=` | `since` ISO timestamp, default now − 24 h | list, newest first |
| DELETE | `/consumptions/{id}` | — | `204` (undo a mistaken tap; own entries only) |
| GET | `/bac` | — | `{bac, band, sober_at, computed_at, drinks_counted}` |
| GET | `/health` | — | `{status: "ok"}` |

- `consumed_at` defaults to the server's `now()`. If a client sends it, it must not be in the future.
- `/bac` considers the user's drinks from the last 24 h. Older drinks are fully eliminated at any realistic intake, so they can be ignored.
- Errors: `401` for a missing or invalid token, `404` for an unknown drink or log entry, `422` for validation errors (FastAPI default).
- Interactive OpenAPI docs are served at `/docs`.

**Example `/bac` response**

```json
{
  "bac": 0.047,
  "band": "yellow",
  "sober_at": "2026-10-04T23:58:00Z",
  "computed_at": "2026-10-04T20:50:00Z",
  "drinks_counted": 3
}
```

## 6. Frontend (React)

- **Onboarding page:** weight (kg) and biological sex form → `POST /sessions` → store the token → go to the Tracker. Shown only when there is no valid token.
- **Tracker page**
  - Grid of drink buttons ("+1 Beer", "+1 Shot", …) built from `GET /drinks`.
  - BAC gauge / progress bar coloured by `band`, with the numeric BAC and "sober at HH:MM".
  - Recent drinks list with an undo action (`DELETE /consumptions/{id}`).
  - A persistent disclaimer.
  - An "Edit profile" control (`PATCH /me`).
- **Data layer:** a thin `fetch` wrapper that injects the token. TanStack Query handles caching, `refetchInterval: 30_000` on `/bac`, and invalidation of `/bac` and `/consumptions` after each mutation.
- **Band colours** are mapped in a single `constants/bands.js`.

## 7. Development roadmap

Work happens on the `dev` branch. Each bullet is one task and one commit (`feat: <brief explanation>`).

### Phase 0: Foundations
- Backend and frontend skeleton directories and Dockerfiles.
- `docker-compose.yml` (db, api, web), `.env.example`, `.gitignore`.
- README with setup and run instructions.

### Phase 1: Database and sessions
- SQLAlchemy models and the Alembic initial schema migration.
- Catalog seed data migration.
- `POST /sessions`, `GET/PATCH /me` and the token auth dependency.
- pytest setup with a Postgres test database.

### Phase 2: Core logic
- `services/bac.py` (Widmark, incremental elimination, bands, sober-at) with unit tests:
  - zero drinks
  - single-drink value matching the worked example
  - full elimination to 0
  - sober gap between drinks
  - male vs female `r`
  - band boundaries
- `GET /drinks`, plus `POST/GET/DELETE /consumptions`, with integration tests.
- `GET /bac` endpoint with integration tests.

### Phase 3: Frontend MVP
- Vite + React scaffold, API client, Vite proxy.
- Onboarding page.
- Tracker page: drink grid, BAC display with 4-band colours, polling.
- Recent drinks list with undo.

### Phase 4: Polish and hardening
- Disclaimer, form validation messages, and loading/empty/error states.
- Production build: nginx image serving the frontend and proxying `/api`.
- CI: pytest plus frontend lint and tests on push.

### Phase 5: Optional extensions
- Email/password accounts that claim the existing anonymous user.
- History of past sessions/nights.
- Custom user-defined drinks.

## 8. Testing strategy

- **Unit (pytest):** `services/bac.py` is the most critical code. Assertions use hand-calculated expected values, with a tolerance of ±0.001.
- **Integration (pytest + FastAPI TestClient):** run against a real Postgres test database, covering auth, ownership checks on undo, the `since` filter, and `/bac` end to end.
- **Frontend (Vitest + React Testing Library):** band-to-colour mapping, the onboarding form, and the add/undo flow with a mocked API.
