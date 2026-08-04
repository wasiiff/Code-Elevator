# Intelligent Code Evaluation Assistant

Paste in a snippet of source code and get back an AI code review: a list of security,
performance, and clean-code findings, a refactored version of the code, a 0–100 quality
score, and a short executive summary. Reviews are stored in MongoDB so past evaluations
can be listed and retrieved.

Powered by **Google Gemini** through LangChain LCEL, with a FastAPI backend and a
React + Vite + Tailwind frontend.

---

## How it works

A submitted snippet runs through a four-stage LCEL chain in `backend/agent.py`. Each
stage is a separate model call, and each feeds the next:

| # | Stage | Temp | Output |
|---|-------------|------|--------------------------------------------------------|
| 1 | Planner     | 0.3  | 3–5 review focus areas to steer the evaluation |
| 2 | Evaluator   | 0.1  | Structured findings — category, severity, location, description, impact |
| 3 | Refactorer  | 0.2  | A full rewrite of the code addressing the findings |
| 4 | Synthesizer | 0.2  | Executive summary + quality score (0–100) |

Stages 2 and 4 use `.with_structured_output()` against the Pydantic models in
`backend/schemas.py`, so findings and scores come back as validated objects rather than
text that needs parsing. Severity is constrained to `Critical | High | Medium | Low`.

The prompts for every stage live in `backend/prompts.py`.

> **Note on temperature:** the default model, `gemini-3.6-flash`, uses fixed sampling and
> ignores the per-stage temperatures above. They still apply if you switch `GEMINI_MODEL`
> to a model that honours them (for example `gemini-3.5-flash`).

## Project layout

```
backend/          FastAPI + LangChain + MongoDB
  main.py           API routes, CORS, key guard
  agent.py          4-stage LCEL evaluation chain
  prompts.py        System/human prompts per stage
  schemas.py        Pydantic request/response models
  database.py       Async MongoDB (Motor) connection + lifespan
  env_loader.py     Loads backend/.env by absolute path
  check_gemini_key.py   Reports key status without printing the secret
  check_mongo.py        Verifies the MongoDB connection
  start_mongo.ps1       Starts a portable local MongoDB
frontend/         React 18 + Vite 6 + Tailwind 3 (TypeScript)
  src/App.tsx           Language picker, code input, results
  src/components/       QualityScoreCard, FindingsList, CodeComparison
  src/services/api.ts   Axios client
```

## API

Base URL `http://127.0.0.1:8000`.

| Method | Endpoint | Description |
|--------|-------------------------|--------------------------------------|
| GET    | `/api/v1/health`        | Liveness check → `{"status":"ok"}` |
| POST   | `/api/v1/reviews`       | Run an evaluation and store it |
| GET    | `/api/v1/reviews`       | List recent reviews (`?limit=`, default 20) |
| GET    | `/api/v1/reviews/{id}`  | Fetch one review by id |

`POST /api/v1/reviews` takes `{"programming_language": "Python", "source_code": "..."}`
and returns the strategy plan, findings, refactored code, quality score, and summary.
Interactive docs are at `/docs`.

Error cases: `503` if `GEMINI_API_KEY` is missing or still the placeholder, `502` if the
model call fails, `400` on a malformed review id, `404` if a review isn't found.

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB — either a local instance or a MongoDB Atlas cluster
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 1. Configure the environment

```bash
cd backend
cp .env.example .env      # Windows: copy .env.example .env
```

Edit `backend/.env` and set a real `GEMINI_API_KEY`. The API returns `503` while the value
is still `your_gemini_api_key_here`.

| Variable | Default | Purpose |
|-----------------|-----------------------------|--------------------------------|
| `MONGODB_URL`   | `mongodb://localhost:27017` | MongoDB connection string |
| `DATABASE_NAME` | `code_reviewer_db`          | Database holding `reviews` |
| `GEMINI_API_KEY`| —                           | Google Gemini API key |
| `GEMINI_MODEL`  | `gemini-3.6-flash`          | Model used by all four stages |

`.env` is gitignored — keep real keys out of the repo.

### 2. Start MongoDB

For a local portable install on Windows:

```powershell
.\backend\start_mongo.ps1
```

The script expects `mongod.exe` under
`%USERPROFILE%\mongodb-local\mongodb-win32-x86_64-windows-7.0.16\bin\` and stores data in
`%USERPROFILE%\mongodb-data`. If you use MongoDB Atlas instead, skip this and point
`MONGODB_URL` at your SRV connection string.

Verify with `python backend/check_mongo.py`.

### 3. Run the backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate           # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API refuses to start if MongoDB is unreachable — the connection is opened in the
FastAPI lifespan handler. Confirm it's up:

```bash
curl http://127.0.0.1:8000/api/v1/health
```

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. Vite proxies `/api` to `127.0.0.1:8000`, so the backend must
be running.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `503 GEMINI_API_KEY is not configured` | Set a real key in `backend/.env`, restart the API. Check with `python backend/check_gemini_key.py`. |
| `404 ... no longer available to new users` | That `GEMINI_MODEL` is retired for new keys. Use `gemini-3.6-flash`. |
| `503 UNAVAILABLE ... high demand` | The model is temporarily overloaded — retry, or switch `GEMINI_MODEL`. |
| `MongoDB connection failed` | Start MongoDB (step 2) or fix `MONGODB_URL`. |
| Frontend shows "Is the API running?" | The backend isn't up on port 8000. |

## Scripts

| Command | Location | Purpose |
|---------|----------|---------|
| `uvicorn main:app --reload --port 8000` | `backend/` | Run the API |
| `python check_gemini_key.py` | `backend/` | Report key status (never prints the secret) |
| `python check_mongo.py` | `backend/` | Test the MongoDB connection |
| `npm run dev` | `frontend/` | Vite dev server on :5173 |
| `npm run build` | `frontend/` | Type-check and build to `dist/` |
| `npm run preview` | `frontend/` | Serve the production build |
