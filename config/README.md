# Shared Configuration

Centralised configuration assets that apply to multiple parts of the stack live in this directory.

## Environment naming

Use the following naming convention for environment files:

- `backend/.env` – Runtime configuration for the FastAPI service.
- `frontend/.env.local` – Local development variables consumed by Vite.

## Secrets management

Never commit `.env` files or secrets to version control. Prefer using a secrets manager in deployed environments. For local development, copy the provided examples and override values per developer machine.

## Tooling

Linting and formatting rules are defined close to each service (see `backend/pyproject.toml` and `frontend/.eslintrc.cjs`). Shared CI workflows live under `.github/workflows`.
