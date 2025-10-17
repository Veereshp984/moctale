# Auragraph — discovery, playlists & sharing UI

This project implements the discovery dashboard for films and music described in the ticket. It is a Vite + React + TypeScript single-page application that lets people:

- Browse combined discovery surfaces for curated films and music with filtering and search.
- Build and manage a hybrid playlist with ordering controls and metadata editing.
- Toggle public access, copy/share links, and expose a public read-only playlist page.
- View personalised recommendations driven by the tones present in the playlist.
- Exercise an end-to-end happy path through Cypress smoke tests.

The experience is backed by a lightweight mock catalogue and simulated network calls so it behaves like an integrated frontend while remaining self-contained inside this repository.

## Getting started

```bash
npm install
npm run dev
```

Open <http://localhost:5173> to explore the experience.

## Available scripts

- `npm run dev` – start the Vite dev server.
- `npm run build` – type-check and build the production bundle.
- `npm run preview` – preview the production build.
- `npm run lint` – run ESLint across the project.
- `npm run cy:open` – open the Cypress runner for interactive testing.
- `npm run cy:run` / `npm run test:e2e` – execute Cypress smoke tests in headless mode.

## Project structure

```
src/
  components/      // UI building blocks (layout, discovery, playlist, sharing, recommendations)
  context/         // Playlist state management and persistence helpers
  data/            // Mock catalogue used by the API service
  pages/           // Top-level routed views (dashboard + public playlist)
  services/        // API facade with simulated latency and recommendation logic
  utils/           // Formatting helpers
  types.ts         // Shared TypeScript types
cypress/           // Cypress configuration and happy path test suite
```

## Testing

The repository includes a Cypress happy-path e2e spec that covers discovery, playlist management, saving, sharing, and public playlist visibility.

```bash
npm run cy:run
# or interactively
npm run cy:open
```

The tests assume the dev server is available at `http://localhost:5173` (the default Vite port).
