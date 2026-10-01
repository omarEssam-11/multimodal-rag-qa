import { useEffect, useState } from "react";
import { Save } from "lucide-react";
import { api } from "../services/api";
import { useStore } from "../store/useStore";
import type { ConfigResponse, UISettings } from "../types";

export default function SettingsPage() {
  const { settings, saveSettings, addToast } = useStore();
  const [form, setForm] = useState<UISettings>(settings);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const config: ConfigResponse = await api.config();
        const newForm: UISettings = {
          llm_provider: config.llm_provider,
          llm_model: config.llm_model,
          temperature: config.temperature,
          top_k_text: config.top_k_text,
          top_k_images: config.top_k_images,
          text_weight: config.text_weight,
          image_weight: config.image_weight,
          chunk_size: config.chunk_size,
          chunk_overlap: config.chunk_overlap,
        };
        setForm(newForm);
        saveSettings(newForm);
      } catch (err) {
        addToast(
          "error",
          err instanceof Error ? err.message : "Failed to load config"
        );
      } finally {
        setLoading(false);
      }
    };
    loadConfig();
  }, [addToast, saveSettings]);

  const update = <K extends keyof UISettings>(key: K, value: UISettings[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    saveSettings(form);
    addToast("success", "Settings saved");
  };

  if (loading) {
    return (
      <div className="h-full overflow-y-auto">
        <div className="mx-auto max-w-2xl px-4 py-6">
          <div className="mb-6 h-8 w-48 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
          <div className="space-y-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="card animate-pulse p-4">
                <div className="mb-2 h-3 w-32 rounded bg-gray-200 dark:bg-gray-700" />
                <div className="h-9 w-full rounded bg-gray-200 dark:bg-gray-700" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-2xl px-4 py-6">
        <div className="mb-6">
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
            Settings
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            UI preferences for the studio interface
          </p>
        </div>

        <div className="space-y-4">
          {/* LLM Provider */}
          <div className="card p-4">
            <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
              LLM Provider
            </label>
            <select
              value={form.llm_provider}
              onChange={(e) => update("llm_provider", e.target.value)}
              className="input-field"
              aria-label="LLM provider"
            >
              <option value="ollama">Ollama</option>
              <option value="openai_compatible">OpenAI Compatible</option>
            </select>
          </div>

          {/* Model */}
          <div className="card p-4">
            <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Model
            </label>
            <input
              type="text"
              value={form.llm_model}
              onChange={(e) => update("llm_model", e.target.value)}
              placeholder={
                form.llm_provider === "ollama"
                  ? "e.g., llava:7b"
                  : "e.g., gpt-4-vision-preview"
              }
              className="input-field"
              aria-label="Model name"
            />
          </div>

          {/* Temperature */}
          <div className="card p-4">
            <div className="mb-1.5 flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Temperature
              </label>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {form.temperature.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={form.temperature}
              onChange={(e) => update("temperature", parseFloat(e.target.value))}
              className="w-full accent-brand-600"
              aria-label="Temperature"
            />
          </div>

          {/* Top-K row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="card p-4">
              <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Top-K Text
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={form.top_k_text}
                onChange={(e) =>
                  update("top_k_text", parseInt(e.target.value) || 1)
                }
                className="input-field"
                aria-label="Top-K text results"
              />
            </div>
            <div className="card p-4">
              <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Top-K Images
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={form.top_k_images}
                onChange={(e) =>
                  update("top_k_images", parseInt(e.target.value) || 1)
                }
                className="input-field"
                aria-label="Top-K image results"
              />
            </div>
          </div>

          {/* Retrieval weights */}
          <div className="card p-4">
            <div className="mb-1.5 flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Text Retrieval Weight
              </label>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {form.text_weight.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={form.text_weight}
              onChange={(e) => update("text_weight", parseFloat(e.target.value))}
              className="w-full accent-brand-600"
              aria-label="Text retrieval weight"
            />
          </div>

          <div className="card p-4">
            <div className="mb-1.5 flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Image Retrieval Weight
              </label>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {form.image_weight.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={form.image_weight}
              onChange={(e) => update("image_weight", parseFloat(e.target.value))}
              className="w-full accent-brand-600"
              aria-label="Image retrieval weight"
            />
          </div>

          {/* Chunking */}
          <div className="grid grid-cols-2 gap-4">
            <div className="card p-4">
              <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Chunk Size
              </label>
              <input
                type="number"
                min="64"
                max="4096"
                value={form.chunk_size}
                onChange={(e) =>
                  update("chunk_size", parseInt(e.target.value) || 64)
                }
                className="input-field"
                aria-label="Chunk size"
              />
            </div>
            <div className="card p-4">
              <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Chunk Overlap
              </label>
              <input
                type="number"
                min="0"
                max="1024"
                value={form.chunk_overlap}
                onChange={(e) =>
                  update("chunk_overlap", parseInt(e.target.value) || 0)
                }
                className="input-field"
                aria-label="Chunk overlap"
              />
            </div>
          </div>

          {/* Save button */}
          <div className="flex justify-end pt-2">
            <button onClick={handleSave} className="btn-primary">
              <Save className="h-4 w-4" />
              Save Settings
            </button>
          </div>

          <p className="text-center text-xs text-gray-400 dark:text-gray-500">
            Note: These are client-side UI preferences. Actual retrieval
            parameters are configured server-side.
          </p>
        </div>
      </div>
    </div>
  );
}
