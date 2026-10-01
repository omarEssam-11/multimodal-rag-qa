import type {
  ChatResponse,
  ConfigResponse,
  Document,
  DocumentStatus,
  HealthResponse,
  RetrieveResponse,
} from "../types";

const BASE_URL = "/api";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      if (data && typeof data === "object" && "detail" in data) {
        const d = (data as { detail: unknown }).detail;
        detail = typeof d === "string" ? d : JSON.stringify(d);
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(detail || `Request failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // Health & config
  async health(): Promise<HealthResponse> {
    const res = await fetch(`${BASE_URL}/health`);
    return handleResponse<HealthResponse>(res);
  },

  async config(): Promise<ConfigResponse> {
    const res = await fetch(`${BASE_URL}/config`);
    return handleResponse<ConfigResponse>(res);
  },

  // Documents
  async listDocuments(): Promise<Document[]> {
    const res = await fetch(`${BASE_URL}/documents`);
    return handleResponse<Document[]>(res);
  },

  async getDocument(documentId: string): Promise<Document> {
    const res = await fetch(`${BASE_URL}/documents/${documentId}`);
    return handleResponse<Document>(res);
  },

  async getDocumentStatus(documentId: string): Promise<DocumentStatus> {
    const res = await fetch(`${BASE_URL}/documents/${documentId}/status`);
    return handleResponse<DocumentStatus>(res);
  },

  async uploadDocument(
    file: File,
    onProgress?: (pct: number) => void
  ): Promise<Document> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const form = new FormData();
      form.append("file", file);

      xhr.open("POST", `${BASE_URL}/documents/upload`);
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch (err) {
            reject(new Error("Invalid JSON response from server"));
          }
        } else {
          let detail = xhr.statusText;
          try {
            const data = JSON.parse(xhr.responseText);
            if (data && typeof data === "object" && "detail" in data) {
              const d = (data as { detail: unknown }).detail;
              detail = typeof d === "string" ? d : JSON.stringify(d);
            }
          } catch {
            // ignore
          }
          reject(new Error(detail || `Upload failed with status ${xhr.status}`));
        }
      };
      xhr.onerror = () => reject(new Error("Network error during upload"));
      xhr.send(form);
    });
  },

  async reindexDocument(documentId: string): Promise<Document> {
    const res = await fetch(`${BASE_URL}/documents/${documentId}/index`, {
      method: "POST",
    });
    return handleResponse<Document>(res);
  },

  async deleteDocument(documentId: string): Promise<{ message: string; document_id: string }> {
    const res = await fetch(`${BASE_URL}/documents/${documentId}`, {
      method: "DELETE",
    });
    return handleResponse(res);
  },

  // Chat
  async chat(params: {
    message?: string;
    sessionId?: string;
    image?: File | null;
  }): Promise<ChatResponse> {
    const form = new FormData();
    if (params.message) form.append("message", params.message);
    if (params.sessionId) form.append("session_id", params.sessionId);
    if (params.image) form.append("image", params.image);

    const res = await fetch(`${BASE_URL}/chat`, {
      method: "POST",
      body: form,
    });
    return handleResponse<ChatResponse>(res);
  },

  // Retrieve
  async retrieve(params: {
    text?: string;
    image?: File | null;
  }): Promise<RetrieveResponse> {
    const form = new FormData();
    if (params.text) form.append("text", params.text);
    if (params.image) form.append("image", params.image);

    const res = await fetch(`${BASE_URL}/retrieve`, {
      method: "POST",
      body: form,
    });
    return handleResponse<RetrieveResponse>(res);
  },

  // Images — accepts a bare image id or a full /api/images/... path
  imageUrl(imageId: string): string {
    if (imageId.startsWith("/") || imageId.startsWith("http")) {
      return imageId;
    }
    return `${BASE_URL}/images/${imageId}`;
  },
};
