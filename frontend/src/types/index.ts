export interface Source {
  document: string;
  page: number;
  type: "text" | "image";
  score: number;
  content: string;
  image_url: string | null;
  caption: string | null;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  query_type: "text" | "image" | "text+image";
  retrieval_ms: number;
  generation_ms: number;
  model: string;
  text_hits: number;
  image_hits: number;
  pipeline: string[];
  session_id: string;
}

export interface RetrieveResponse {
  query_type: "text" | "image" | "text+image";
  results: Source[];
  text_hits: number;
  image_hits: number;
  retrieval_ms: number;
}

export interface Document {
  document_id: string;
  document_name: string;
  status: "pending" | "processing" | "indexed" | "failed";
  num_pages: number;
  num_images: number;
  num_chunks: number;
  file_size: number;
  created_at: string;
  updated_at: string;
  error: string | null;
}

export interface DocumentStatus {
  document_id: string;
  status: "pending" | "processing" | "indexed" | "failed";
  num_pages: number;
  num_images: number;
  num_chunks: number;
  error: string | null;
}

export interface HealthResponse {
  status: string;
  qdrant: boolean;
  embedding_models: string[];
  llm_provider: string;
  llm_model: string;
}

export interface ConfigResponse {
  llm_provider: string;
  llm_model: string;
  temperature: number;
  top_k_text: number;
  top_k_images: number;
  text_weight: number;
  image_weight: number;
  chunk_size: number;
  chunk_overlap: number;
  clip_model: string;
  text_embedding_model: string;
  max_history_messages: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  image?: string | null;
  imageName?: string;
  response?: ChatResponse;
  loading?: boolean;
  error?: string;
}

export interface ToastItem {
  id: string;
  type: "success" | "error" | "info";
  message: string;
}

export interface UISettings {
  llm_provider: string;
  llm_model: string;
  temperature: number;
  top_k_text: number;
  top_k_images: number;
  text_weight: number;
  image_weight: number;
  chunk_size: number;
  chunk_overlap: number;
}
