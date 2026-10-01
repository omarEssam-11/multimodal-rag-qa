import { useState } from "react";
import { ChevronDown, FileText, Image as ImageIcon } from "lucide-react";
import type { Source } from "../types";
import { api } from "../services/api";
import ImageLightbox from "./ImageLightbox";

interface EvidencePanelProps {
  sources: Source[];
}

export default function EvidencePanel({ sources }: EvidencePanelProps) {
  const [expanded, setExpanded] = useState(true);
  const [lightboxSource, setLightboxSource] = useState<Source | null>(null);

  if (sources.length === 0) return null;

  const textSources = sources.filter((s) => s.type === "text");
  const imageSources = sources.filter((s) => s.type === "image");

  return (
    <>
      <div className="mt-3 rounded-lg border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/50">
        {/* Header */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex w-full items-center justify-between px-3 py-2 text-left"
          aria-expanded={expanded}
        >
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Retrieved Evidence
            </span>
            <span className="badge bg-brand-100 text-brand-700 dark:bg-brand-900 dark:text-brand-300">
              {sources.length}
            </span>
          </div>
          <ChevronDown
            className={`h-4 w-4 text-gray-400 transition-transform ${
              expanded ? "rotate-180" : ""
            }`}
          />
        </button>

        {expanded && (
          <div className="space-y-3 border-t border-gray-200 px-3 pb-3 pt-2 dark:border-gray-700">
            {/* Text sources */}
            {textSources.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-medium text-gray-500 dark:text-gray-400">
                  <FileText className="h-3.5 w-3.5" />
                  Text ({textSources.length})
                </div>
                {textSources.map((source, i) => (
                  <div
                    key={`text-${i}`}
                    className="rounded-md border border-gray-200 bg-white p-2.5 dark:border-gray-700 dark:bg-gray-900"
                  >
                    <div className="mb-1.5 flex flex-wrap items-center gap-1.5">
                      <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                        {source.document}
                      </span>
                      <span className="badge bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                        p.{source.page}
                      </span>
                      <span className="badge bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300">
                        {source.score.toFixed(3)}
                      </span>
                    </div>
                    <p className="line-clamp-3 text-xs leading-relaxed text-gray-600 dark:text-gray-400">
                      {source.content}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {/* Image sources */}
            {imageSources.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-medium text-gray-500 dark:text-gray-400">
                  <ImageIcon className="h-3.5 w-3.5" />
                  Images ({imageSources.length})
                </div>
                <div className="flex flex-wrap gap-2">
                  {imageSources.map((source, i) => (
                    <button
                      key={`img-${i}`}
                      onClick={() => setLightboxSource(source)}
                      className="group relative overflow-hidden rounded-md border border-gray-200 transition-all hover:border-brand-400 hover:shadow-md dark:border-gray-700"
                      aria-label={`View image from ${source.document} page ${source.page}`}
                    >
                      {source.image_url ? (
                        <img
                          src={api.imageUrl(source.image_url)}
                          alt={source.caption || "Retrieved image"}
                          className="h-20 w-20 object-cover"
                        />
                      ) : (
                        <div className="flex h-20 w-20 items-center justify-center bg-gray-100 dark:bg-gray-800">
                          <ImageIcon className="h-6 w-6 text-gray-400" />
                        </div>
                      )}
                      <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent px-1.5 pb-1 pt-4">
                        <p className="truncate text-[10px] font-medium text-white">
                          {source.document} · p.{source.page}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {lightboxSource && (
        <ImageLightbox
          source={lightboxSource}
          onClose={() => setLightboxSource(null)}
        />
      )}
    </>
  );
}
