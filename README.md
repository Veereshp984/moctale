# Full-Stack Starter Kit

This repository provides a batteries-included baseline for building a modern full-stack application with a FastAPI backend and a Vite + React + TypeScript frontend. Shared tooling for linting, formatting, and CI is configured out of the box so you can focus on product development.

## Project structure

```
├── backend/        # FastAPI application + Poetry dependencies
├── frontend/       # Vite + React + TypeScript single-page app
├── config/         # Shared configuration documentation
└── .github/        # Continuous integration workflows
```

## Prerequisites

- **Python** 3.11+
- **Poetry** for Python dependency management ([installation guide](https://python-poetry.org/docs/#installation))
- **Node.js** 18.17+ and **npm** 9+

## Backend setup

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

The FastAPI server will be available on <http://localhost:8000>. API routes are mounted under `/api` (see `app/api/routes.py`).

### Backend tooling

- `poetry run ruff check app` – lint with Ruff
- `poetry run black app` – format with Black
- `poetry run pytest` – run backend tests (tests folder ready for expansion)

### Backend environment variables

Copy the example file and adjust values as needed:

```bash
cp backend/.env.example backend/.env
```

Key variables:

- `MONGODB_URI` – connection string for MongoDB (Motor client)
- `SECRET_KEY` / `ALGORITHM` / `ACCESS_TOKEN_EXPIRE_MINUTES` – authentication settings
- `PROJECT_NAME` / `API_PREFIX` – service metadata

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server runs on <http://localhost:5173>. The frontend ships with routing, Zustand state management, Tailwind CSS styling, and Axios utilities ready to connect to the API (`/src/pages/Home.tsx` targets the backend health endpoint).

### Frontend tooling

- `npm run lint` – ESLint with TypeScript + React plugins
- `npm run lint:fix` – ESLint with auto-fix
- `npm run format` – Prettier formatting
- `npm run build` – Type-check and bundle the application

### Frontend environment variables

Copy the example file to configure the API base URL:

```bash
cp frontend/.env.example frontend/.env.local
```

## Continuous integration

A GitHub Actions workflow (`.github/workflows/ci.yml`) runs linting and build checks for both services on every push and pull request. Expand it with tests and deployment steps as the project grows.

## Next steps

- Add domain-specific API routes and services under `backend/app/`
- Introduce feature modules and UI components within `frontend/src/`
- Wire up a real database and authentication provider

Happy shipping! 🚀
