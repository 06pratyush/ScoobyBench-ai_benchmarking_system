# Contributing to ScoobyBench

Thanks for helping make hardware benchmarks honest. This guide covers the
development workflow; see [README.md](../README.md) for the architecture
overview and [API.md](API.md) for endpoint documentation.

## Development Setup

```powershell
git clone https://github.com/06pratyush/ScoobyBench-ai_benchmarking_system
cd ScoobyBench-ai_benchmarking_system

# Backend
cd backend
python -m venv venv311
venv311\Scripts\activate
pip install -r requirements-dev.txt

# Frontend
cd ..\frontend
npm install
```

Open `ScoobyBench.code-workspace` in VS Code to get tasks, launch configs,
and recommended extensions.

## Running Locally

```powershell
# Terminal 1 — backend on http://127.0.0.1:8472
cd backend && python run.py

# Terminal 2 — Electron window
cd frontend && npm run electron:dev
```

## Quality Gates

Every PR must pass CI (`.github/workflows/ci.yml`):

| Check | Command |
|-------|---------|
| Lint | `ruff check app tests ../scripts` (from `backend/`) |
| Backend tests | `pytest tests -v` (from `backend/`) |
| Frontend build | `npm run build` (from `frontend/`) |

Tests run against a throwaway `SCOOBYBENCH_HOME`, so they never touch your
real benchmark database.

## Pull Request Workflow

1. Fork and create a feature branch: `git checkout -b feature/your-feature`
2. Make your change, with tests for new backend behavior
3. Run the quality gates above locally
4. Commit using [Conventional Commits](https://www.conventionalcommits.org/)
   (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`)
5. Open a PR against `main`

## Project Conventions

- **Backend**: FastAPI + Pydantic v2. Blocking endpoints (benchmarks, model
  pulls) are sync `def` routes so they run in the threadpool. Timestamps are
  timezone-aware UTC (`datetime.now(timezone.utc)`).
- **Validation**: anything derived from user input that reaches a file path
  or SQL goes through `app/utils/validators.py`.
- **Frontend**: renderer components call the backend through
  `src/renderer/utils/api.js` and `src/renderer/utils/websocket.js` — no
  hardcoded URLs in components.
- **Baselines**: community baseline submissions (JSON reports) are welcome —
  open a Discussion under **Community Baselines**.
