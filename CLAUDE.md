# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Greenfield: there is no application code, build tooling, or tests yet (the git repo has no commits). The only spec is `Plan.md`. Update this file with real build/test/run commands once the stack is scaffolded.

## What is being built

A full-stack web app that calculates and tracks a user's Blood Alcohol Concentration (BAC) in real time, per `Plan.md`.

Planned stack:
- Frontend: React.js
- Backend: Python **or** Node.js (not yet decided, so confirm with the user before scaffolding)
- Database: PostgreSQL
- Infrastructure: Docker

## Domain requirements (from Plan.md)

- **BAC math must strictly use the Widmark formula.** It needs the user's body weight (kg), biological sex (which sets the Widmark distribution constant r), grams of alcohol consumed, and time elapsed (elimination over time).
- **User onboarding** collects weight in kg and biological sex. These are stored per session or per user profile.
- **Drink catalog** is a pre-populated DB table of common drinks with standard volume (ml) and ABV %, so users don't type these in. Alcohol grams are derived from volume × ABV × ethanol density.
- **Consumption log**: one-tap "+1 Beer" / "+1 Shot" entries, each with an automatic timestamp.
- **BAC calculation happens in a backend controller** over the accumulated drinks and elapsed time. It is not done on the frontend.
- **Frontend display** is a dynamic progress bar or color-coded thresholds: Green < 0.03, Yellow 0.04–0.06, Red > 0.08. Plan.md leaves the ranges between those bands undefined, so ask before choosing boundaries.

Core data entities: Users, Drinks Catalog, Consumption Logs (users ↔ logs ↔ catalog drinks).

The full project plan, covering architecture, Widmark algorithm, PostgreSQL schema, REST API and phased roadmap, is in `docs/PROJECT_PLAN.md`. Decisions recorded there: backend is Python + FastAPI (SQLAlchemy 2 + Alembic); identity is an anonymous session token first; BAC bands are contiguous: green < 0.03, yellow 0.03–<0.06, orange 0.06–<0.08, red ≥ 0.08.

## Rules

We will only work on a branch named dev. Every task you made is separated and commited independently, each commit must be normalized in this way (feat:brief explain of what you did)
