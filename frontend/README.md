Frontend (Vite + React + TypeScript)

A Vite-based React application with React Router, Zustand, Tailwind CSS, ESLint, Prettier, and Vitest.

Requirements
- Node.js 20
- npm

Setup
- npm ci

Run
- npm run dev – starts the Vite dev server at http://localhost:5173

Lint/Format/Test
- npm run lint – ESLint
- npm run format – Prettier (write)
- npm run format:check – Prettier (check)
- npm test – Vitest

Environment
Copy .env.example to .env and set VITE_API_BASE_URL to your backend URL (e.g. http://localhost:8000).

Build
- npm run build – type-check and build production assets
- npm run preview – preview the production build locally
