Full-stack starter monorepo

This repository contains a clean baseline for a full‑stack application with a FastAPI backend and a Vite + React + TypeScript frontend. It includes shared tooling and a simple CI workflow to lint and test both apps.

Structure
- backend/ – FastAPI service with a health endpoint and Poetry-managed dependencies
- frontend/ – Vite + React + TypeScript app with routing, Zustand state, Tailwind CSS, ESLint + Prettier
- .github/workflows/ci.yml – CI to lint, test, and build

Quick start
1) Install prerequisites
- Python 3.10–3.12
- Poetry
- Node.js 20 and npm

2) Install dependencies
- make setup
  - Installs backend poetry deps and frontend npm packages

3) Run locally
- make backend-dev – starts FastAPI at http://localhost:8000
- make frontend-dev – starts Vite dev server at http://localhost:5173

The backend exposes GET /health returning {"status":"ok"}. The frontend renders a basic React app.

Tooling
Backend
- Formatter: black
- Linter: ruff
- Tests: pytest

Frontend
- Linter: ESLint (flat config)
- Formatter: Prettier
- Unit tests: Vitest (+ Testing Library)

CI
- Triggers on pull requests
- Jobs:
  - Backend: poetry install, ruff + black checks, pytest
  - Frontend: npm ci, eslint, prettier check, vitest, build

Environment variables
- backend/.env.example – app settings (Mongo URI, JWT keys, etc.)
- frontend/.env.example – VITE_API_BASE_URL for API calls

Common commands
- make lint – run linters in both apps
- make format – format code in both apps
- make test – run unit tests for both apps

Notes
- This is a fresh scaffold; previous conflicting files were removed or relocated into the appropriate app directories.
- If you previously installed dependencies at the repository root, delete any leftover node_modules or virtualenvs and use the app-specific directories instead.
