# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

This is an early-stage scaffold for a study-quiz app: FastAPI backend + PostgreSQL, with a frontend directory that has no source files or framework chosen yet (`frontend/package.json` is a bare stub). `backend/app/routes` and `backend/app/services` exist but are currently empty — routes are not yet wired into `main.py`. There is no test suite, no linter config, and no migration tooling (Alembic) anywhere in the repo.

## Commands

Backend setup and run (from `backend/`):
```
pip install -r requirements.txt
uvicorn app.main:app --reload
```
This requires a running Postgres instance reachable via `DATABASE_URL` (defaults to `postgresql+psycopg://postgres:postgres@localhost:5432/study_quiz`, set in `backend/app/db/database.py`). On startup, `main.py` calls `create_db_and_tables()`, which creates tables from the SQLAlchemy models via `Base.metadata.create_all` — there is no migration system, so schema changes are applied by editing the models directly (see Architecture below for how this relates to `schema.sql`).

`docker-compose.yml` exists but is currently empty — there is no containerized dev setup yet.

There are no automated tests configured. `backend/app/test_openai.py` is not a pytest test despite the name — it's a standalone script that calls the OpenAI API to generate quiz questions and requires `OPENAI_API_KEY` in a `.env` file (loaded via `python-dotenv`). It also depends on the `openai` package, which is **not** listed in `requirements.txt`.

## Architecture

- **`app/db/base.py`** — declares the shared SQLAlchemy `DeclarativeBase` (`Base`) that all models inherit from.
- **`app/db/database.py`** — engine/session setup, reads `DATABASE_URL` from the environment.
- **`app/models/study_models.py`** — all SQLAlchemy ORM models in one file: `User`, `Topic` (self-referential via `parent_topic_id` for topic hierarchies), `Question`, `QuestionTopic` (many-to-many join table between questions and topics), `Session` (a quiz-taking session with a `mode` of `adaptive`/`review`/`practice`), `Attempt` (a single answer given during a session), and `UserTopicMastery` (per-user, per-topic mastery score derived from attempt history).
- **`app/db/schema.sql`** — a raw SQL definition of the same schema. This is a parallel reference/documentation artifact, not something that gets executed automatically — the app provisions tables from the SQLAlchemy models, not this file. **When changing the data model, update both `study_models.py` and `schema.sql` to keep them in sync**, since nothing enforces that automatically.
- **`app/main.py`** — FastAPI app entrypoint. Currently only exposes `/health`; new endpoints should live in `app/routes` (empty so far) and be included via routers, with business logic in `app/services` (also empty so far) rather than inline in route handlers.

### Data model relationships

Quiz questions belong to one or more topics (via `QuestionTopic`). A user starts a `Session` (scoped to a mode and optionally a set of topic IDs), and each answer they give during that session is recorded as an `Attempt` linked to both the session and the question. `UserTopicMastery` rows are the aggregate/derived state per user-topic pair (mastery score, counts seen/correct) — expected to be updated based on `Attempt` history, though the update logic doesn't exist yet (no services are implemented).
