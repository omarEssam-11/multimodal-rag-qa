import { useEffect, useRef, useState } from "react";
import {
  ImagePlus,
  Menu,
  Send,
  Sparkles,
  X,
} from "lucide-react";
import { api } from "../services/api";
import { useStore } from "../store/useStore";
import ChatMessage from "../components/ChatMessage";
import type { ChatMessage as ChatMessageType } from "../types";

const exampleQueries = [
  {
    label: "Text query",
    text: "What is the main contribution of this paper?",
    type: "text" as const,
  },
  {
    label: "Image query",
    text: "Find diagrams or figures related to the architecture",
    type: "image" as const,
  },
  {
    label: "Text + Image",
    text: "Explain the methodology shown in this figure",
    type: "text+image" as const,
  },
];

export default function ChatPage() {
  const {
    messages,
    sessionId,
    isSending,
    addMessage,
    updateMessage,
    setSessionId,
    setSending,
    addToast,
    setSidebarOpen,
  } = useStore();

  const [input, setInput] = useState("");
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [input]);

  const handleImageSelect = (file: File) => {
    if (!file.type.startsWith("image/")) {
      addToast("error", "Please select an image file");
      return;
    }
    setSelectedImage(file);
    const reader = new FileReader();
    reader.onload = (e) => setImagePreview(e.target?.result as string);
    reader.readAsDataURL(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleImageSelect(file);
  };

  const clearImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSend = async () => {
    const trimmed = input.trim();
    if ((!trimmed && !selectedImage) || isSending) return;

    const userMsg: ChatMessageType = {
      id: `user-${Date.now()}`,
      role: "user",
      text: trimmed,
      image: imagePreview,
      imageName: selectedImage?.name,
    };
    addMessage(userMsg);

    const assistantMsg: ChatMessageType = {
      id: `assistant-${Date.now()}`,
      role: "assistant",
      text: "",
      loading: true,
    };
    addMessage(assistantMsg);

    setInput("");
    clearImage();
    setSending(true);

    try {
      const response = await api.chat({
        message: trimmed || undefined,
        sessionId: sessionId || undefined,
        image: selectedImage,
      });

      if (!sessionId) setSessionId(response.session_id);

      updateMessage(assistantMsg.id, {
        text: response.answer,
        response,
        loading: false,
      });
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "An error occurred";
      updateMessage(assistantMsg.id, {
        text: "",
        loading: false,
        error: errorMsg,
      });
      addToast("error", errorMsg);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleExampleClick = (text: string) => {
    setInput(text);
    textareaRef.current?.focus();
  };

  return (
    <div className="flex h-full flex-col">
      {/* Mobile header */}
      <div className="flex h-14 items-center gap-3 border-b border-gray-200 px-4 dark:border-gray-800 lg:hidden">
        <button
          onClick={() => setSidebarOpen(true)}
          className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
          aria-label="Open sidebar"
        >
          <Menu className="h-5 w-5" />
        </button>
        <h2 className="text-sm font-semibold">Chat</h2>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          /* Empty state */
          <div className="flex h-full flex-col items-center justify-center px-4 py-12">
            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-100 text-brand-600 dark:bg-brand-900 dark:text-brand-400">
              <Sparkles className="h-8 w-8" />
            </div>
            <h2 className="mb-2 text-2xl font-bold text-gray-900 dark:text-gray-100">
              Multimodal RAG QA
            </h2>
            <p className="mb-8 max-w-md text-center text-sm text-gray-500 dark:text-gray-400">
              Ask questions about your documents using text, images, or both.
              The system retrieves relevant evidence and generates answers using
              CLIP-powered multimodal search.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {exampleQueries.map((q) => (
                <button
                  key={q.label}
                  onClick={() => handleExampleClick(q.text)}
                  className="rounded-full border border-gray-200 bg-white px-4 py-2 text-sm text-gray-600 transition-all hover:border-brand-300 hover:bg-brand-50 hover:text-brand-700 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-400 dark:hover:border-brand-500 dark:hover:bg-brand-900/20 dark:hover:text-brand-300"
                >
                  {q.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-6 px-4 py-6">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900">
        <div className="mx-auto max-w-3xl">
          {/* Image preview */}
          {imagePreview && (
            <div className="mb-2 inline-block">
              <div className="relative">
                <img
                  src={imagePreview}
                  alt="Selected"
                  className="h-16 w-16 rounded-lg border border-gray-200 object-cover dark:border-gray-700"
                />
                <button
                  onClick={clearImage}
                  className="absolute -right-1.5 -top-1.5 rounded-full bg-gray-800 p-0.5 text-white shadow-sm transition-colors hover:bg-gray-700 dark:bg-gray-600"
                  aria-label="Remove image"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            </div>
          )}

          {/* Input row */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`flex items-end gap-2 rounded-xl border bg-gray-50 p-2 transition-colors dark:bg-gray-800 ${
              dragOver
                ? "border-brand-500 ring-2 ring-brand-500/20"
                : "border-gray-200 dark:border-gray-700"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleImageSelect(file);
              }}
              className="hidden"
              aria-hidden="true"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="shrink-0 rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-200 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-300"
              aria-label="Add image"
              title="Add image"
            >
              <ImagePlus className="h-5 w-5" />
            </button>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question... (Enter to send, Shift+Enter for newline)"
              rows={1}
              className="max-h-[200px] flex-1 resize-none bg-transparent px-1 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none dark:text-gray-100 dark:placeholder-gray-500"
              aria-label="Message input"
            />
            <button
              onClick={handleSend}
              disabled={(!input.trim() && !selectedImage) || isSending}
              className="shrink-0 rounded-lg bg-brand-600 p-2 text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-40"
              aria-label="Send message"
            >
              <Send className="h-5 w-5" />
            </button>
          </div>
          <p className="mt-1.5 text-center text-[11px] text-gray-400 dark:text-gray-500">
            Supports text, image, and combined queries
          </p>
        </div>
      </div>
    </div>
  );
}
