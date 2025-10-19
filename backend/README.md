Backend (FastAPI)

A minimal FastAPI service managed with Poetry. Exposes a health endpoint and includes linting, formatting, and tests.

Requirements
- Python 3.10–3.12
- Poetry

Setup
- make install
  - Installs dependencies via Poetry

Run
- make dev – starts uvicorn at http://localhost:8000

Endpoints
- GET /health -> {"status":"ok"}

Environment
Copy .env.example to .env and adjust as needed.

Tooling
- Lint: ruff check app tests
- Format: black app tests; ruff --fix
- Test: pytest

Project layout
- app/main.py – FastAPI application
- tests/ – pytest tests
- pyproject.toml – Poetry + tool configs
