# Soundwave Studio — frontend scaffold

This repository contains a Vite + React + TypeScript starter that establishes a core UI foundation for the Soundwave Studio experience. It ships with routing, state management, mocked data fetching, and a responsive navigation shell covering the key surface areas (auth, discovery, playlists, profile).

Key ingredients:

- **Vite + React + TypeScript** for a fast development workflow.
- **React Router** with a shell layout and placeholder screens for each primary route.
- **Zustand** state store to coordinate global UI state (theme, navigation, mocked catalogue data).
- **Axios** HTTP utilities with an opinionated wrapper and graceful error handling.
- **Tailwind CSS** for themeable design tokens, responsive layout primitives, and shared UI components (buttons, cards, modal, loader, etc.).
- **ESLint + Prettier** for consistent formatting and linting.
- **Vitest + Testing Library** for unit tests, including an example around shared UI primitives.

## Getting started

```bash
npm install
npm run dev
```

Open <http://localhost:5173> to explore the scaffolded interface.

## Available scripts

- `npm run dev` – start the Vite dev server.
- `npm run build` – type-check and build the production bundle.
- `npm run preview` – preview the production build locally.
- `npm run lint` – run ESLint across the codebase.
- `npm run lint:fix` – run ESLint with automatic fixes.
- `npm run format` – format the repository with Prettier.
- `npm run test` – execute the Vitest unit tests.
- `npm run cy:open` – open the Cypress test runner.
- `npm run cy:run` / `npm run test:e2e` – run the Cypress smoke tests headlessly.

## Project structure

```
src/
  components/
    ui/           # Core UI primitives (buttons, cards, loaders, modal)
  hooks/          # Custom hooks for mocked data fetching
  layouts/        # Shared navigation shell + chrome
  lib/            # HTTP client utilities and mocked API facades
  pages/          # Routed pages for auth, discovery, playlists, profile, 404
  store/          # Global Zustand store for UI + catalogue state
  index.css       # Tailwind layers and theme tokens
  main.tsx        # Application entry point
```

Tailwind is configured through design tokens exposed as CSS variables, making it easy to adjust themes or expand the design system.

## Testing

Unit tests are powered by Vitest and Testing Library. Run them with:

```bash
npm run test
```

The shared Testing Library setup (`src/setupTests.ts`) activates jest-dom matchers and polyfills browser APIs used by the theme resolver. A sample test for the button primitive demonstrates typical usage.
