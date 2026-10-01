import { useRef, useState } from "react";
import { FileUp, Upload } from "lucide-react";

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  uploading: boolean;
  progress: number;
}

export default function UploadZone({
  onFileSelect,
  uploading,
  progress,
}: UploadZoneProps) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type === "application/pdf") {
      onFileSelect(file);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onFileSelect(file);
    e.target.value = "";
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      onClick={() => !uploading && inputRef.current?.click()}
      className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-colors ${
        dragOver
          ? "border-brand-500 bg-brand-50 dark:bg-brand-900/20"
          : "border-gray-300 hover:border-brand-400 hover:bg-gray-50 dark:border-gray-700 dark:hover:border-brand-500 dark:hover:bg-gray-800/50"
      } ${uploading ? "pointer-events-none opacity-60" : ""}`}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          if (!uploading) inputRef.current?.click();
        }
      }}
      aria-label="Upload PDF document"
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        onChange={handleChange}
        className="hidden"
        aria-hidden="true"
      />
      {uploading ? (
        <>
          <div className="mb-3 h-10 w-10 overflow-hidden rounded-full border-4 border-brand-200 border-t-brand-600 animate-spin dark:border-brand-800 dark:border-t-brand-400" />
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Uploading... {progress}%
          </p>
          <div className="mt-2 h-1.5 w-48 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
            <div
              className="h-full rounded-full bg-brand-600 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </>
      ) : (
        <>
          <div className="mb-3 rounded-full bg-brand-100 p-3 text-brand-600 dark:bg-brand-900 dark:text-brand-400">
            {dragOver ? (
              <FileUp className="h-6 w-6" />
            ) : (
              <Upload className="h-6 w-6" />
            )}
          </div>
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {dragOver ? "Drop your PDF here" : "Drag & drop a PDF here"}
          </p>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            or click to browse
          </p>
        </>
      )}
    </div>
  );
}
