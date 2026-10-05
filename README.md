# BAC Tracker

A web app that estimates and tracks your Blood Alcohol Concentration (BAC) in real time using the Widmark formula.

> **Disclaimer:** BAC values are estimates only. Never use this app to decide whether you are fit to drive.

Stack: React (Vite) · Python FastAPI · PostgreSQL · Docker. See [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md) for the architecture, database schema, API design and roadmap.

## Run with Docker (recommended)

Requires Docker with Docker Compose.

```sh
cp .env.example .env      # optional; compose has the same defaults built in
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000/api/v1/health |
| API docs (OpenAPI) | http://localhost:8000/docs |
| PostgreSQL | `localhost:5432` (user/password/db: `bac`) |

The `backend/` and `frontend/` directories are mounted into the containers, so code changes reload automatically. Stop with `docker compose down`; add `-v` to also delete the database volume.

## Run locally without Docker

Needs Python 3.12+, Node 20.19+ and a running PostgreSQL that matches `DATABASE_URL` in `.env`.

**Backend**

```sh
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload    # http://localhost:8000
```

**Frontend** (in another terminal)

```sh
cd frontend
npm install
npm run dev                      # http://localhost:5173, proxies /api to localhost:8000
```

## Project layout

```
backend/    FastAPI app (app/), Dockerfile, requirements.txt
frontend/   React + Vite app, Dockerfile
docs/       Project plan
docker-compose.yml
.env.example
```
