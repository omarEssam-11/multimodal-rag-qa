import { create } from "zustand";
import type { ChatMessage, ToastItem, UISettings } from "../types";

const SETTINGS_KEY = "mrs-settings";
const THEME_KEY = "mrs-theme";

function loadSettings(): UISettings {
  const defaults: UISettings = {
    llm_provider: "ollama",
    llm_model: "llava:7b",
    temperature: 0.7,
    top_k_text: 5,
    top_k_images: 3,
    text_weight: 0.7,
    image_weight: 0.3,
    chunk_size: 512,
    chunk_overlap: 50,
  };
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) return { ...defaults, ...JSON.parse(raw) };
  } catch {
    // ignore
  }
  return defaults;
}

function loadTheme(): "dark" | "light" {
  try {
    const t = localStorage.getItem(THEME_KEY);
    if (t === "light") return "light";
  } catch {
    // ignore
  }
  return "dark";
}

interface AppState {
  // Theme
  theme: "dark" | "light";
  toggleTheme: () => void;

  // Settings
  settings: UISettings;
  saveSettings: (s: UISettings) => void;

  // Chat
  messages: ChatMessage[];
  sessionId: string | null;
  isSending: boolean;
  addMessage: (msg: ChatMessage) => void;
  updateMessage: (id: string, patch: Partial<ChatMessage>) => void;
  setSessionId: (id: string) => void;
  setSending: (v: boolean) => void;
  clearMessages: () => void;

  // Toasts
  toasts: ToastItem[];
  addToast: (type: ToastItem["type"], message: string) => void;
  removeToast: (id: string) => void;

  // Sidebar
  sidebarOpen: boolean;
  setSidebarOpen: (v: boolean) => void;
}

export const useStore = create<AppState>((set, get) => ({
  theme: loadTheme(),
  toggleTheme: () => {
    const next = get().theme === "dark" ? "light" : "dark";
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {
      // ignore
    }
    document.documentElement.classList.toggle("dark", next === "dark");
    set({ theme: next });
  },

  settings: loadSettings(),
  saveSettings: (s) => {
    try {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(s));
    } catch {
      // ignore
    }
    set({ settings: s });
  },

  messages: [],
  sessionId: null,
  isSending: false,
  addMessage: (msg) => set({ messages: [...get().messages, msg] }),
  updateMessage: (id, patch) =>
    set({
      messages: get().messages.map((m) => (m.id === id ? { ...m, ...patch } : m)),
    }),
  setSessionId: (id) => set({ sessionId: id }),
  setSending: (v) => set({ isSending: v }),
  clearMessages: () => set({ messages: [], sessionId: null }),

  toasts: [],
  addToast: (type, message) => {
    const id = Math.random().toString(36).slice(2);
    set({ toasts: [...get().toasts, { id, type, message }] });
    setTimeout(() => get().removeToast(id), 4500);
  },
  removeToast: (id) => set({ toasts: get().toasts.filter((t) => t.id !== id) }),

  sidebarOpen: false,
  setSidebarOpen: (v) => set({ sidebarOpen: v }),
}));
