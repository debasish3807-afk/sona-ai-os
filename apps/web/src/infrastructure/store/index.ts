import { create } from "zustand";

interface AppState {
  sessionId: string | null;
  setSessionId: (id: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sessionId: null,
  setSessionId: (id) => set({ sessionId: id }),
}));
