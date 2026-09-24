# MindLoop

An AI-powered study app: pick a topic, a difficulty, and how many questions you want, and an LLM generates a multiple-choice quiz on the spot. Answer questions one at a time with immediate feedback, get a final score, and track your performance across every quiz you've taken.

The long-term goal is an **adaptive study engine** — generate → answer → track performance → adapt what's shown next — rather than a static quiz generator. The current version covers the full generate → answer → score → history loop; adaptive question selection based on past performance is the next major piece (see [Roadmap](#roadmap)).

## Features

- Email/password auth (JWT-based)
- AI-generated multiple-choice quizzes — topic, difficulty (1-5), and question count (up to 20) are all user-chosen
- One-question-at-a-time quiz flow with instant correct/incorrect feedback and explanations
- Final score per quiz, with a full history and all-time stats (quizzes taken, overall accuracy, questions answered)

## Tech stack

**Backend** — FastAPI, SQLAlchemy + PostgreSQL, JWT auth (`pyjwt` + `passlib`/`bcrypt`), OpenAI API (Structured Outputs for reliable question generation)

**Frontend** — React + TypeScript, Vite, React Router

## Getting started

### Prerequisites

- Python 3.11+
- Node.js 18+
- A running PostgreSQL instance
- An [OpenAI API key](https://platform.openai.com/api-keys) with billing enabled

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL, OPENAI_API_KEY, JWT_SECRET_KEY
uvicorn app.main:app --reload
```

`JWT_SECRET_KEY` can be any random string — generate one with `openssl rand -hex 32`. Tables are created automatically on startup (no migration step needed); the database itself (`study_quiz` by default) must already exist.

The API is served at `http://localhost:8000` — interactive docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
cp .env.example .env   # defaults to http://localhost:8000, change if your API runs elsewhere
npm install
npm run dev
```

Runs at `http://localhost:5173`.

## API overview

| Method | Path | Description |
|---|---|---|
| POST | `/auth/signup` | Create an account, returns a token |
| POST | `/auth/login` | Log in, returns a token |
| POST | `/quiz/sessions` | Generate a new quiz (topic, difficulty, question count) |
| GET | `/quiz/sessions/{id}` | Re-fetch a quiz's questions (e.g. after a page refresh) |
| POST | `/quiz/sessions/{id}/answers` | Submit an answer to one question, get correctness + explanation |
| POST | `/quiz/sessions/{id}/finish` | Finalize a quiz and compute its score |
| GET | `/quiz/stats` | All-time stats and full quiz history for the current user |

All `/quiz/*` routes require `Authorization: Bearer <token>`.

## Roadmap

- Per-topic mastery tracking (the schema already has a `user_topic_mastery` table; nothing writes to it yet)
- Adaptive next-question selection based on that mastery data — the actual "adaptive" part of the adaptive study engine
- True/false and short-answer question types (schema supports them; generation and UI currently only handle multiple choice)
