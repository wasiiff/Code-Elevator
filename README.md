# Intelligent Code Evaluation Assistant

Paste in a snippet of source code and get back an AI code review: a list of security,
performance, and clean-code findings, a refactored version of the code, a 0–100 quality
score, and a short executive summary. Reviews are stored in MongoDB so past evaluations
can be listed and retrieved.

Powered by **Google Gemini** through LangChain LCEL, with a FastAPI backend and a
React + Vite + Tailwind frontend.

---

## Run it — 3 commands

Three terminals, one command each. (First time only, do [Setup](#setup) below first.)

```powershell
# Terminal 1 — MongoDB
.\backend\start_mongo.ps1
```

```powershell
# Terminal 2 — API on http://127.0.0.1:8000
cd backend; .\venv\Scripts\Activate.ps1; uvicorn main:app --reload --port 8000
```

```powershell
# Terminal 3 — UI on http://localhost:5173
cd frontend; npm run dev
```

Then open **<http://localhost:5173>**, paste code, and hit **Run Evaluation**.

> On macOS/Linux the only differences are `source venv/bin/activate` in terminal 2, and
> running your own `mongod` instead of `start_mongo.ps1`.

Leave all three running. Terminal 2 needs MongoDB up (terminal 1) or the API refuses to
start; terminal 3 proxies `/api` to terminal 2.

---

## How it works

A submitted snippet runs through two stages in `backend/agent.py`:

| Stage | Calls | Output |
|-------|-------|--------|
| 1. Analyse | 1 | Strategy plan (3–5 focus areas) **and** findings — category, severity, location, description, impact |
| 2. Refactor + score | 2, **run concurrently** | A full rewrite addressing the findings; plus executive summary and 0–100 quality score |

Planning and evaluation share one call, and the refactorer and scorer run in parallel
because scoring rates the code *as submitted* and so doesn't wait on the rewrite. That's
2 sequential model calls instead of 4 — a review takes roughly **25 seconds** instead of
45.

Both structured stages use `.with_structured_output()` against the Pydantic models in
`backend/schemas.py`, so findings and scores come back as validated objects rather than
text that needs parsing. Severity is constrained to `Critical | High | Medium | Low`.

Prompts for every stage live in `backend/prompts.py`.

**Live progress.** The UI calls `POST /api/v1/reviews/stream`, which emits one NDJSON
event per stage, so the frontend shows which step is running and how many issues were
found rather than an anonymous spinner.

> **Note on temperature:** the default model, `gemini-3.6-flash`, uses fixed sampling and
> ignores the per-stage temperatures in `agent.py`. They still apply if you switch
> `GEMINI_MODEL` to a model that honours them (for example `gemini-3.5-flash`).

## Project layout

```
backend/          FastAPI + LangChain + MongoDB
  main.py           API routes, CORS, key guard, NDJSON progress stream
  agent.py          2-stage LCEL evaluation pipeline
  prompts.py        System/human prompts per stage
  schemas.py        Pydantic request/response models
  database.py       Async MongoDB (Motor) connection + lifespan
  env_loader.py     Loads backend/.env by absolute path
  check_gemini_key.py   Reports key status without printing the secret
  check_mongo.py        Verifies the MongoDB connection
  start_mongo.ps1       Starts a portable local MongoDB
frontend/         React 18 + Vite 6 + Tailwind 3 (TypeScript)
  src/App.tsx           Language picker, code input, results
  src/components/       QualityScoreCard, FindingsList, CodeComparison,
                        EvaluationProgress (live stage indicator)
  src/services/api.ts   Axios client + NDJSON streaming client
```

## API

Base URL `http://127.0.0.1:8000`.

| Method | Endpoint | Description |
|--------|-------------------------|--------------------------------------|
| GET    | `/api/v1/health`          | Liveness check → `{"status":"ok"}` |
| POST   | `/api/v1/reviews`         | Run an evaluation and store it (blocks until done) |
| POST   | `/api/v1/reviews/stream`  | Same, streaming stage progress as NDJSON |
| GET    | `/api/v1/reviews`         | List recent reviews (`?limit=`, default 20) |
| GET    | `/api/v1/reviews/{id}`    | Fetch one review by id |

Both POST routes take `{"programming_language": "Python", "source_code": "..."}` and
produce the strategy plan, findings, refactored code, quality score, and summary.
Interactive docs are at `/docs`.

The stream emits one JSON object per line:

```
{"stage": "analyzing"}
{"stage": "refactoring", "findings_count": 4, "strategy_count": 3}
{"stage": "saving"}
{"stage": "done", "review": { ... }}
```

Failures inside the stream arrive as `{"stage": "error", "detail": "..."}`.

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

```powershell
cd backend
copy .env.example .env      # macOS/Linux: cp .env.example .env
```

Edit `backend/.env` and set a real `GEMINI_API_KEY`. The API returns `503` while the value
is still `your_gemini_api_key_here`.

| Variable | Default | Purpose |
|-----------------|-----------------------------|--------------------------------|
| `MONGODB_URL`   | `mongodb://localhost:27017` | MongoDB connection string |
| `DATABASE_NAME` | `code_reviewer_db`          | Database holding `reviews` |
| `GEMINI_API_KEY`| —                           | Google Gemini API key |
| `GEMINI_MODEL`  | `gemini-3.6-flash`          | Model used by both stages |

`.env` is gitignored — keep real keys out of the repo.

### 2. Install MongoDB (local option)

`start_mongo.ps1` expects a portable install — no admin rights, no Windows service:

1. Download `mongodb-windows-x86_64-7.0.16.zip` from
   [MongoDB's download centre](https://www.mongodb.com/try/download/community).
2. Extract it into `%USERPROFILE%\mongodb-local\` so that
   `%USERPROFILE%\mongodb-local\mongodb-win32-x86_64-windows-7.0.16\bin\mongod.exe` exists.

Data goes to `%USERPROFILE%\mongodb-data`. Using Atlas instead? Skip this and point
`MONGODB_URL` at your SRV string. Verify either way with `python backend/check_mongo.py`.

### 3. Install dependencies

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1     # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

```powershell
cd frontend
npm install
```

Now use the [3 commands](#run-it--3-commands) above.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `start_mongo.ps1 cannot be loaded ... is not digitally signed` | The file is marked as downloaded from the internet (common if you got the project as a `.zip`). Clear the mark: `Unblock-File .\backend\start_mongo.ps1`. One-off alternative: `pwsh -ExecutionPolicy Bypass -File .\backend\start_mongo.ps1`. |
| `[WinError 10013] ... socket ... forbidden` on startup | Port 8000 is already taken — usually an API instance you left running. Find it with `Get-NetTCPConnection -LocalPort 8000 -State Listen`, stop that PID, or run on another port with `--port 8001`. |
| `503 GEMINI_API_KEY is not configured` | Set a real key in `backend/.env`, restart the API. Check with `python backend/check_gemini_key.py`. |
| `404 ... no longer available to new users` | That `GEMINI_MODEL` is retired for new keys. Use `gemini-3.6-flash`. |
| `503 UNAVAILABLE ... high demand` | The model is temporarily overloaded — retry, or switch `GEMINI_MODEL`. |
| `MongoDB connection failed` | Start MongoDB (terminal 1) or fix `MONGODB_URL`. |
| Frontend shows "Is the API running?" | The backend isn't up on port 8000. |
| `venv` errors mentioning another user's path | The venv was built elsewhere. Delete `backend/venv` and redo step 3. |

## Scripts

| Command | Location | Purpose |
|---------|----------|---------|
| `uvicorn main:app --reload --port 8000` | `backend/` | Run the API |
| `python check_gemini_key.py` | `backend/` | Report key status (never prints the secret) |
| `python check_mongo.py` | `backend/` | Test the MongoDB connection |
| `npm run dev` | `frontend/` | Vite dev server on :5173 |
| `npm run build` | `frontend/` | Type-check and build to `dist/` |
| `npm run preview` | `frontend/` | Serve the production build |
