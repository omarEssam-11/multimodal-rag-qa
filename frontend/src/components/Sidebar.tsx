import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import {
  BrainCircuit,
  FileText,
  MessageSquare,
  Settings,
  X,
} from "lucide-react";
import { api } from "../services/api";
import type { HealthResponse } from "../types";
import { useStore } from "../store/useStore";
import StatusDot from "./StatusDot";
import ThemeToggle from "./ThemeToggle";

const navItems = [
  { to: "/", label: "Chat", icon: MessageSquare },
  { to: "/documents", label: "Documents", icon: FileText },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const sidebarOpen = useStore((s) => s.sidebarOpen);
  const setSidebarOpen = useStore((s) => s.setSidebarOpen);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await api.health();
        setHealth(data);
      } catch {
        // ignore
      }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 flex w-[260px] flex-col border-r border-gray-200 bg-white transition-transform duration-200 dark:border-gray-800 dark:bg-gray-900 lg:static lg:translate-x-0 ${
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      }`}
    >
      {/* Header */}
      <div className="flex h-14 items-center justify-between border-b border-gray-200 px-4 dark:border-gray-800">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
            <BrainCircuit className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-sm font-semibold leading-tight">Multimodal RAG</h1>
            <p className="text-[11px] leading-tight text-gray-500 dark:text-gray-400">
              Studio
            </p>
          </div>
        </div>
        <button
          className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-800 dark:hover:text-gray-300 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close sidebar"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={() => setSidebarOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100"
              }`
            }
          >
            <item.icon className="h-4.5 w-4.5 shrink-0" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Footer: system status + theme */}
      <div className="border-t border-gray-200 p-3 dark:border-gray-800">
        <div className="mb-2 rounded-lg bg-gray-50 p-3 dark:bg-gray-800/50">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
              System Status
            </span>
            <StatusDot online={health?.qdrant ?? false} />
          </div>
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500 dark:text-gray-400">Vector DB</span>
              <span
                className={`font-medium ${
                  health?.qdrant
                    ? "text-emerald-600 dark:text-emerald-400"
                    : "text-red-600 dark:text-red-400"
                }`}
              >
                {health?.qdrant ? "Connected" : "Disconnected"}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500 dark:text-gray-400">LLM</span>
              <span className="font-medium text-gray-700 dark:text-gray-300">
                {health?.llm_provider ?? "—"}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500 dark:text-gray-400">Model</span>
              <span className="max-w-[120px] truncate font-medium text-gray-700 dark:text-gray-300">
                {health?.llm_model ?? "—"}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center justify-between px-1">
          <span className="text-xs text-gray-500 dark:text-gray-400">Theme</span>
          <ThemeToggle />
        </div>
      </div>
    </aside>
  );
}
