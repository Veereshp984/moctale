import { useEffect, useState } from "react";

import axios from "axios";

import { useAppStore } from "@/store/useAppStore";

type HealthStatus = "idle" | "loading" | "online" | "offline";

type HealthResponse = {
  status: string;
};

function Home(): JSX.Element {
  const { apiBaseUrl, theme, toggleTheme } = useAppStore();
  const [health, setHealth] = useState<HealthStatus>("idle");

  useEffect(() => {
    let cancelled = false;

    async function fetchHealth() {
      setHealth("loading");
      try {
        const { data } = await axios.get<HealthResponse>(`${apiBaseUrl}/health`, {
          timeout: 2000,
        });
        if (!cancelled) {
          setHealth(data.status === "ok" ? "online" : "offline");
        }
      } catch (error) {
        if (!cancelled) {
          setHealth("offline");
        }
      }
    }

    fetchHealth();

    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl]);

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Environment</p>
        <h2 className="mt-2 text-3xl font-semibold">
          Frontend theme: <span className="text-indigo-300">{theme}</span>
        </h2>
        <button
          type="button"
          onClick={toggleTheme}
          className="mt-4 inline-flex items-center gap-2 rounded-full bg-indigo-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-400"
        >
          Toggle theme
        </button>
      </div>

      <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-6">
        <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Backend health</p>
        <div className="mt-3 flex items-baseline gap-3">
          <span className="text-4xl font-bold text-white">
            {health === "online" && "Online"}
            {health === "offline" && "Offline"}
            {health === "loading" && "Checking"}
            {health === "idle" && "Pending"}
          </span>
          <span className="text-sm text-slate-400">{apiBaseUrl}/health</span>
        </div>
        {health === "offline" && (
          <p className="mt-2 text-sm text-amber-300">
            Unable to reach the backend. Start the FastAPI server to see it go online.
          </p>
        )}
      </div>
    </section>
  );
}

export default Home;
