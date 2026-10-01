import { useState } from "react";
import {
  AlertCircle,
  ChevronDown,
  FileText,
  Image as ImageIcon,
  Layers,
  RefreshCw,
  Trash2,
} from "lucide-react";
import type { Document } from "../types";

interface DocumentCardProps {
  document: Document;
  onReindex: (id: string) => void;
  onDelete: (id: string) => void;
  reindexing: boolean;
}

const statusConfig: Record<
  Document["status"],
  { label: string; className: string }
> = {
  pending: {
    label: "Pending",
    className: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-400",
  },
  processing: {
    label: "Processing",
    className: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400",
  },
  indexed: {
    label: "Indexed",
    className: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400",
  },
  failed: {
    label: "Failed",
    className: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400",
  },
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export default function DocumentCard({
  document,
  onReindex,
  onDelete,
  reindexing,
}: DocumentCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const status = statusConfig[document.status];

  return (
    <div className="card overflow-hidden transition-shadow hover:shadow-md">
      <div className="p-4">
        <div className="mb-2 flex items-start justify-between gap-2">
          <div className="flex min-w-0 items-center gap-2.5">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400">
              <FileText className="h-4.5 w-4.5" />
            </div>
            <div className="min-w-0">
              <h3 className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
                {document.document_name}
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {formatDate(document.created_at)}
              </p>
            </div>
          </div>
          <span className={`badge shrink-0 ${status.className}`}>
            {document.status === "processing" && (
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-blue-500" />
            )}
            {status.label}
          </span>
        </div>

        {/* Stats row */}
        <div className="mb-3 flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
          <span className="flex items-center gap-1">
            <FileText className="h-3.5 w-3.5" />
            {document.num_pages} pages
          </span>
          <span className="flex items-center gap-1">
            <ImageIcon className="h-3.5 w-3.5" />
            {document.num_images} images
          </span>
          <span className="flex items-center gap-1">
            <Layers className="h-3.5 w-3.5" />
            {document.num_chunks} chunks
          </span>
          <span>{formatBytes(document.file_size)}</span>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => onReindex(document.document_id)}
            disabled={reindexing || document.status === "processing"}
            className="btn-ghost !px-2 !py-1.5 text-xs"
            aria-label={`Re-index ${document.document_name}`}
            title="Re-index"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${reindexing ? "animate-spin" : ""}`}
            />
            Re-index
          </button>
          <button
            onClick={() => setConfirmDelete(true)}
            className="btn-ghost !px-2 !py-1.5 text-xs text-red-600 hover:bg-red-50 hover:text-red-700 dark:text-red-400 dark:hover:bg-red-900/20 dark:hover:text-red-300"
            aria-label={`Delete ${document.document_name}`}
            title="Delete"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Delete
          </button>
          <button
            onClick={() => setExpanded(!expanded)}
            className="btn-ghost !px-2 !py-1.5 text-xs ml-auto"
            aria-label={expanded ? "Collapse details" : "Expand details"}
          >
            <ChevronDown
              className={`h-3.5 w-3.5 transition-transform ${
                expanded ? "rotate-180" : ""
              }`}
            />
          </button>
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="border-t border-gray-100 bg-gray-50 px-4 py-3 dark:border-gray-800 dark:bg-gray-800/50">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
            <div>
              <dt className="text-gray-500 dark:text-gray-400">Document ID</dt>
              <dd className="font-mono text-gray-700 dark:text-gray-300">
                {document.document_id}
              </dd>
            </div>
            <div>
              <dt className="text-gray-500 dark:text-gray-400">Updated</dt>
              <dd className="text-gray-700 dark:text-gray-300">
                {formatDate(document.updated_at)}
              </dd>
            </div>
            {document.error && (
              <div className="col-span-2">
                <dt className="mb-1 flex items-center gap-1 text-red-600 dark:text-red-400">
                  <AlertCircle className="h-3.5 w-3.5" />
                  Error
                </dt>
                <dd className="rounded-md bg-red-50 p-2 text-red-700 dark:bg-red-900/20 dark:text-red-300">
                  {document.error}
                </dd>
              </div>
            )}
          </dl>
        </div>
      )}

      {/* Delete confirmation */}
      {confirmDelete && (
        <div className="border-t border-red-100 bg-red-50 px-4 py-3 dark:border-red-900/30 dark:bg-red-900/10">
          <p className="mb-2 text-xs text-red-700 dark:text-red-300">
            Delete "{document.document_name}"? This cannot be undone.
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => {
                onDelete(document.document_id);
                setConfirmDelete(false);
              }}
              className="rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-red-700"
            >
              Delete
            </button>
            <button
              onClick={() => setConfirmDelete(false)}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
