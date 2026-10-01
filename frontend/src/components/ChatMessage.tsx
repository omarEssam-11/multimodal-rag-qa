import { useState } from "react";
import { Bot, ChevronDown, User } from "lucide-react";
import type { ChatMessage as ChatMessageType } from "../types";
import Markdown from "./Markdown";
import EvidencePanel from "./EvidencePanel";

interface ChatMessageProps {
  message: ChatMessageType;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const [pipelineExpanded, setPipelineExpanded] = useState(false);
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="flex max-w-[80%] items-start gap-3">
          <div className="rounded-2xl rounded-tr-sm bg-brand-600 px-4 py-3 text-white shadow-sm">
            {message.image && (
              <img
                src={message.image}
                alt="Uploaded"
                className="mb-2 max-h-40 rounded-lg object-cover"
              />
            )}
            {message.text && (
              <p className="whitespace-pre-wrap text-sm">{message.text}</p>
            )}
          </div>
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-600 dark:bg-brand-900 dark:text-brand-400">
            <User className="h-4 w-4" />
          </div>
        </div>
      </div>
    );
  }

  // Assistant message
  return (
    <div className="flex justify-start">
      <div className="flex max-w-[85%] items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
          <Bot className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="rounded-2xl rounded-tl-sm border border-gray-200 bg-white px-4 py-3 shadow-sm dark:border-gray-700 dark:bg-gray-900">
            {message.loading ? (
              <div className="flex items-center gap-1.5 py-1">
                <span className="h-2 w-2 animate-bounce-dot rounded-full bg-gray-400" />
                <span
                  className="h-2 w-2 animate-bounce-dot rounded-full bg-gray-400"
                  style={{ animationDelay: "0.2s" }}
                />
                <span
                  className="h-2 w-2 animate-bounce-dot rounded-full bg-gray-400"
                  style={{ animationDelay: "0.4s" }}
                />
              </div>
            ) : message.error ? (
              <p className="text-sm text-red-600 dark:text-red-400">{message.error}</p>
            ) : (
              <>
                <Markdown text={message.text} />
                {message.response && (
                  <>
                    <EvidencePanel sources={message.response.sources} />

                    {/* Pipeline transparency strip */}
                    {message.response.pipeline.length > 0 && (
                      <div className="mt-3 border-t border-gray-100 pt-2 dark:border-gray-800">
                        <button
                          onClick={() => setPipelineExpanded(!pipelineExpanded)}
                          className="flex items-center gap-1.5 text-xs text-gray-500 transition-colors hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                        >
                          <ChevronDown
                            className={`h-3.5 w-3.5 transition-transform ${
                              pipelineExpanded ? "rotate-180" : ""
                            }`}
                          />
                          <span className="font-medium">Pipeline</span>
                          <span className="badge bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                            {message.response.query_type}
                          </span>
                        </button>
                        {pipelineExpanded && (
                          <div className="mt-2 space-y-1 rounded-md bg-gray-50 p-2 font-mono text-[11px] text-gray-600 dark:bg-gray-800/50 dark:text-gray-400">
                            {message.response.pipeline.map((step, i) => (
                              <div key={i} className="flex items-start gap-2">
                                <span className="text-gray-400 dark:text-gray-500">
                                  {String(i + 1).padStart(2, "0")}
                                </span>
                                <span>{step}</span>
                              </div>
                            ))}
                            <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1 border-t border-gray-200 pt-1.5 text-[10px] dark:border-gray-700">
                              <span>
                                Text hits: {message.response!.text_hits}
                              </span>
                              <span>
                                Image hits: {message.response!.image_hits}
                              </span>
                              <span>
                                Retrieval: {message.response!.retrieval_ms.toFixed(0)}ms
                              </span>
                              <span>
                                Generation: {message.response!.generation_ms.toFixed(0)}ms
                              </span>
                              <span>Model: {message.response!.model}</span>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
