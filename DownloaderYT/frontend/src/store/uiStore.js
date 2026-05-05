import { create } from "zustand";
import { persist } from "zustand/middleware";

export const useUiStore = create(
  persist(
    (set) => ({
      sidebarOpen: false,
      theme: "light",
      language: "es-ES",
      sseStatus: "idle",
      setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setTheme: (theme) => set({ theme }),
      setLanguage: (language) => set({ language }),
      setSseStatus: (sseStatus) => set({ sseStatus }),
    }),
    {
      name: "downloaderyt-ui",
      partialize: (state) => ({ theme: state.theme, language: state.language }),
    },
  ),
);
