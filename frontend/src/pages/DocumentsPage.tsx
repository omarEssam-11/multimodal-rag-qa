import { useCallback, useEffect, useState } from "react";
import { FileText, RefreshCw } from "lucide-react";
import { api } from "../services/api";
import { useStore } from "../store/useStore";
import UploadZone from "../components/UploadZone";
import DocumentCard from "../components/DocumentCard";
import type { Document } from "../types";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [reindexingId, setReindexingId] = useState<string | null>(null);
  const addToast = useStore((s) => s.addToast);

  const fetchDocuments = useCallback(async () => {
    try {
      const data = await api.listDocuments();
      setDocuments(data);
    } catch (err) {
      addToast(
        "error",
        err instanceof Error ? err.message : "Failed to load documents"
      );
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setUploadProgress(0);
    try {
      await api.uploadDocument(file, (pct) => setUploadProgress(pct));
      addToast("success", `Uploaded "${file.name}"`);
      await fetchDocuments();
    } catch (err) {
      addToast(
        "error",
        err instanceof Error ? err.message : "Upload failed"
      );
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleReindex = async (id: string) => {
    setReindexingId(id);
    try {
      await api.reindexDocument(id);
      addToast("success", "Re-indexing started");
      await fetchDocuments();
    } catch (err) {
      addToast(
        "error",
        err instanceof Error ? err.message : "Re-index failed"
      );
    } finally {
      setReindexingId(null);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteDocument(id);
      addToast("success", "Document deleted");
      setDocuments((prev) => prev.filter((d) => d.document_id !== id));
    } catch (err) {
      addToast(
        "error",
        err instanceof Error ? err.message : "Delete failed"
      );
    }
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-5xl px-4 py-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              Documents
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Upload and manage your PDF documents
            </p>
          </div>
          <button
            onClick={fetchDocuments}
            disabled={loading}
            className="btn-secondary"
            aria-label="Refresh documents"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {/* Upload zone */}
        <div className="mb-6">
          <UploadZone
            onFileSelect={handleUpload}
            uploading={uploading}
            progress={uploadProgress}
          />
        </div>

        {/* Document list */}
        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="card animate-pulse p-4">
                <div className="mb-3 flex items-center gap-3">
                  <div className="h-9 w-9 rounded-lg bg-gray-200 dark:bg-gray-700" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3 w-3/4 rounded bg-gray-200 dark:bg-gray-700" />
                    <div className="h-2.5 w-1/2 rounded bg-gray-200 dark:bg-gray-700" />
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="h-2.5 w-16 rounded bg-gray-200 dark:bg-gray-700" />
                  <div className="h-2.5 w-16 rounded bg-gray-200 dark:bg-gray-700" />
                  <div className="h-2.5 w-16 rounded bg-gray-200 dark:bg-gray-700" />
                </div>
              </div>
            ))}
          </div>
        ) : documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 py-16 dark:border-gray-700">
            <div className="mb-3 rounded-full bg-gray-100 p-4 text-gray-400 dark:bg-gray-800">
              <FileText className="h-8 w-8" />
            </div>
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              No documents yet
            </p>
            <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">
              Upload a PDF to get started
            </p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {documents.map((doc) => (
              <DocumentCard
                key={doc.document_id}
                document={doc}
                onReindex={handleReindex}
                onDelete={handleDelete}
                reindexing={reindexingId === doc.document_id}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
