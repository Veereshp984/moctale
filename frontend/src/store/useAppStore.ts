import { create } from "zustand";

export type Theme = "light" | "dark";

interface AppState {
  theme: Theme;
  apiBaseUrl: string;
  toggleTheme: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  theme: "dark",
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api",
  toggleTheme: () => {
    const nextTheme = get().theme === "dark" ? "light" : "dark";
    set({ theme: nextTheme });
  },
}));
