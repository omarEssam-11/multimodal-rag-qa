"""RAG service: orchestrates retrieval + generation into a grounded answer."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Sequence

from app.config import settings
from app.services.conversation import conversation_manager
from app.services.llm_service import BaseLLMProvider, ChatMessage, get_llm_provider
from app.services.retriever import MultimodalRetriever, RetrievalResult, retriever as default_retriever
from app.utils.logger import get_logger, log_query_event

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a precise multimodal research assistant. You answer questions using ONLY the retrieved evidence provided below (text passages and images).

Rules:
1. Answer strictly from the retrieved evidence. Do not fabricate facts.
2. Clearly distinguish between what is directly stated in the evidence and what is your inference.
3. If the evidence is insufficient to answer, say so explicitly: "The retrieved documents do not contain sufficient evidence to answer this."
4. When images are provided as evidence, refer to them (e.g. "as shown in the figure from page 8").
5. Cite sources inline using the format [document_name — page N] or [document_name — Figure N].
6. Be concise but complete. Use markdown formatting when helpful.
"""


@dataclass
class RAGResponse:
    answer: str
    sources: list[dict]
    query_type: str
    retrieval_ms: float
    generation_ms: float
    model: str
    text_hits: int
    image_hits: int
    pipeline: list[str] = field(default_factory=list)


class RAGService:
    def __init__(
        self,
        retriever: MultimodalRetriever | None = None,
        llm: BaseLLMProvider | None = None,
    ) -> None:
        self.retriever = retriever or default_retriever
        self.llm = llm

    @property
    def provider(self) -> BaseLLMProvider:
        if self.llm is None:
            self.llm = get_llm_provider()
        return self.llm

    def answer(
        self,
        text: str | None = None,
        image: bytes | None = None,
        session_id: str | None = None,
        request_id: str | None = None,
    ) -> RAGResponse:
        from PIL import Image
        import io

        rid = request_id or "rag"
        conv = conversation_manager.get(session_id) if session_id else None

        # Decode image if provided
        pil_image = None
        if image:
            try:
                pil_image = Image.open(io.BytesIO(image))
                if pil_image.mode != "RGB":
                    pil_image = pil_image.convert("RGB")
            except Exception:
                pil_image = None

        # ---- Retrieval ----
        retrieval = self.retriever.retrieve(text=text, image=pil_image)

        # ---- Build context ----
        text_evidence = [r for r in retrieval.results if r.content_type == "text"]
        image_evidence = [r for r in retrieval.results if r.content_type == "image"]

        context_parts = []
        if text_evidence:
            context_parts.append("=== RETRIEVED TEXT EVIDENCE ===")
            for i, r in enumerate(text_evidence, 1):
                context_parts.append(
                    f"[Evidence {i}] Source: {r.document_name} — page {r.page_number} "
                    f"(score: {r.score:.2f})\n{r.content}"
                )
        if image_evidence:
            context_parts.append("\n=== RETRIEVED IMAGE EVIDENCE ===")
            for i, r in enumerate(image_evidence, 1):
                cap = f" — {r.caption}" if r.caption else ""
                context_parts.append(
                    f"[Image {i}] Source: {r.document_name} — page {r.page_number} "
                    f"(score: {r.score:.2f}){cap}"
                )

        context = "\n\n".join(context_parts) if context_parts else "No relevant evidence was retrieved."

        # ---- Build messages ----
        messages: list[ChatMessage] = [ChatMessage(role="system", content=SYSTEM_PROMPT)]

        # bounded history
        if conv:
            for m in conv.to_list()[-settings.max_history_messages * 2 :]:
                messages.append(ChatMessage(role=m["role"], content=m["content"]))

        user_content = text.strip() if text else ""
        if not user_content and pil_image is not None:
            user_content = "[The user uploaded an image. Analyze it in the context of the retrieved evidence.]"
        if not user_content:
            user_content = "No query provided."

        user_images: list[str] = []
        if pil_image is not None:
            user_images.append(self.provider._image_to_data_url(pil_image))
        # attach retrieved images as evidence (respect the provider's image cap)
        budget = max(settings.llm_max_images - len(user_images), 0)
        for r in image_evidence[:budget]:
            img_path = r.metadata.get("image_path")
            if img_path:
                user_images.append(self.provider._image_to_data_url(img_path))

        messages.append(ChatMessage(role="user", content=user_content, images=user_images))

        # ---- Generation ----
        gen_start = time.perf_counter()
        try:
            answer = self.provider.generate(messages)
        except Exception as e:
            logger.error("Generation failed: %s", e)
            answer = (
                "I retrieved relevant evidence but the language model failed to generate a response. "
                f"Error: {e}"
            )
        gen_ms = (time.perf_counter() - gen_start) * 1000.0

        # ---- Persist to conversation ----
        if conv:
            conv.add("user", user_content, has_image=pil_image is not None)
            conv.add("assistant", answer)

        # ---- Sources ----
        sources = []
        for r in retrieval.results:
            src = {
                "document": r.document_name,
                "page": r.page_number,
                "type": r.content_type,
                "score": round(r.score, 4),
                "content": r.content[:500] if r.content else "",
            }
            if r.image_url:
                src["image_url"] = r.image_url
            if r.caption:
                src["caption"] = r.caption
            sources.append(src)

        pipeline = [
            f"Query modality: {retrieval.query_type.upper()}",
            f"Text retrieval: {retrieval.text_hits} results",
            f"Image retrieval: {retrieval.image_hits} results",
            "Fusion / reranking",
            f"Top evidence: {len(text_evidence)} text + {len(image_evidence)} images",
            "Generation",
        ]

        log_query_event(
            logger,
            request_id=rid,
            query_type=retrieval.query_type,
            retrieval_ms=retrieval.retrieval_ms,
            n_text=retrieval.text_hits,
            n_images=retrieval.image_hits,
            generation_ms=gen_ms,
            model=self.provider.model,
        )

        return RAGResponse(
            answer=answer,
            sources=sources,
            query_type=retrieval.query_type,
            retrieval_ms=retrieval.retrieval_ms,
            generation_ms=gen_ms,
            model=self.provider.model,
            text_hits=retrieval.text_hits,
            image_hits=retrieval.image_hits,
            pipeline=pipeline,
        )


rag_service = RAGService()
