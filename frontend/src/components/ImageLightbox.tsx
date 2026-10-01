import { useEffect } from "react";
import { X } from "lucide-react";
import type { Source } from "../types";
import { api } from "../services/api";

interface ImageLightboxProps {
  source: Source;
  onClose: () => void;
}

export default function ImageLightbox({ source, onClose }: ImageLightboxProps) {
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Image preview"
    >
      <div
        className="relative max-h-[90vh] w-full max-w-3xl overflow-hidden rounded-xl bg-white shadow-2xl dark:bg-gray-900"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute right-3 top-3 z-10 rounded-full bg-black/50 p-1.5 text-white transition-colors hover:bg-black/70"
          aria-label="Close preview"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Image */}
        <div className="flex max-h-[70vh] items-center justify-center overflow-hidden bg-gray-100 dark:bg-gray-800">
          {source.image_url ? (
            <img
              src={api.imageUrl(source.image_url)}
              alt={source.caption || "Retrieved image"}
              className="max-h-[70vh] w-auto max-w-full object-contain"
            />
          ) : (
            <div className="flex h-48 items-center justify-center text-gray-400">
              No image available
            </div>
          )}
        </div>

        {/* Metadata */}
        <div className="space-y-2 p-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="badge bg-brand-100 text-brand-700 dark:bg-brand-900 dark:text-brand-300">
              {source.document}
            </span>
            <span className="badge bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
              Page {source.page}
            </span>
            <span className="badge bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300">
              Score: {source.score.toFixed(3)}
            </span>
          </div>
          {source.caption && (
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {source.caption}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
