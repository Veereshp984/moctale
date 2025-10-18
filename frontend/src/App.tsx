import { Suspense } from "react";

import { AppRoutes } from "./routes";

function App(): JSX.Element {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/80">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
          <h1 className="text-lg font-semibold tracking-tight">Full-Stack Starter</h1>
          <nav className="flex items-center gap-6 text-sm text-slate-300">
            <a className="hover:text-white" href="https://fastapi.tiangolo.com/" target="_blank" rel="noreferrer">
              FastAPI Docs
            </a>
            <a className="hover:text-white" href="https://vitejs.dev/" target="_blank" rel="noreferrer">
              Vite Docs
            </a>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-12">
        <Suspense fallback={<p className="text-slate-400">Loading…</p>}>
          <AppRoutes />
        </Suspense>
      </main>
    </div>
  );
}

export default App;
