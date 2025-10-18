# Backend Service

A FastAPI application that powers the API layer for the full-stack starter project.

## Getting started

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

## Environment variables

Configuration is managed with [`pydantic-settings`](https://docs.pydantic.dev/latest/concepts/pydantic_settings/). Copy `.env.example` to `.env` and adjust the values as needed:

- `PROJECT_NAME` – Service display name.
- `API_PREFIX` – Root path for versioned API routes.
- `MONGODB_URI` – Connection string for MongoDB (used by data services).
- `SECRET_KEY` – Secret used for signing JWTs.
- `ALGORITHM` – JWT algorithm (defaults to `HS256`).
- `ACCESS_TOKEN_EXPIRE_MINUTES` – Expiration window for access tokens.

## Tooling

- **Poetry** manages runtime and development dependencies.
- **Ruff** enforces lint rules (`poetry run ruff check app`).
- **Black** ensures consistent formatting (`poetry run black app`).
- **Pytest** runs automated tests (`poetry run pytest`).
