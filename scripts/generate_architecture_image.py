"""Generate the architecture diagram for the README.

Creates docs/architecture.png showing the full multimodal RAG pipeline.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


def draw_box(ax, x, y, w, h, text, color, fontsize=9, text_color="white"):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        facecolor=color, edgecolor="#333333", linewidth=1.2,
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, color=text_color, fontweight="bold", wrap=True)


def draw_arrow(ax, x1, y1, x2, y2, color="#555555", style="-|>"):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle=style, mutation_scale=14, color=color, linewidth=1.4,
    ))


def main():
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis("off")
    fig.patch.set_facecolor("#0f172a")

    # Title
    ax.text(8, 9.6, "Multimodal RAG Studio — Architecture", ha="center", va="center",
            fontsize=16, color="white", fontweight="bold")

    # ---- Ingestion pipeline (left side) ----
    draw_box(ax, 0.3, 8.0, 2.2, 0.7, "PDF /\nDocument", "#1e40af")
    draw_box(ax, 0.3, 6.8, 2.2, 0.7, "Document\nProcessing", "#1e40af")
    draw_box(ax, 0.3, 5.6, 2.2, 0.7, "Extract Text\n+ Images", "#1e40af")

    draw_arrow(ax, 1.4, 8.0, 1.4, 7.5)
    draw_arrow(ax, 1.4, 6.8, 1.4, 6.3)

    # Text branch
    draw_box(ax, 3.2, 6.0, 2.0, 0.7, "Text\nChunking", "#0e7490")
    draw_box(ax, 3.2, 4.8, 2.0, 0.7, "Text Embedding\n(all-MiniLM)", "#0e7490")
    draw_arrow(ax, 2.5, 5.95, 3.2, 6.35)
    draw_arrow(ax, 4.2, 6.0, 4.2, 5.5)

    # Image branch
    draw_box(ax, 3.2, 3.6, 2.0, 0.7, "CLIP Image\nEmbedding", "#7c3aed")
    draw_arrow(ax, 2.5, 5.6, 3.2, 3.95)

    # Qdrant
    draw_box(ax, 6.0, 4.8, 2.4, 1.0, "Qdrant\nVector DB", "#b45309", fontsize=10)
    draw_arrow(ax, 5.2, 5.15, 6.0, 5.3)
    draw_arrow(ax, 5.2, 3.95, 6.0, 4.9)

    # ---- Query pipeline (right side) ----
    draw_box(ax, 9.2, 8.0, 2.2, 0.7, "User Query", "#15803d")
    draw_box(ax, 9.2, 6.8, 2.2, 0.7, "Query\nEmbedding", "#15803d")
    draw_arrow(ax, 10.3, 8.0, 10.3, 7.5)

    # Query type branches
    draw_box(ax, 12.2, 7.2, 1.6, 0.6, "Text\nEmbedding", "#0e7490", fontsize=8)
    draw_box(ax, 12.2, 6.2, 1.6, 0.6, "CLIP\nEmbedding", "#7c3aed", fontsize=8)
    draw_arrow(ax, 11.4, 7.15, 12.2, 7.5)
    draw_arrow(ax, 11.4, 6.8, 12.2, 6.5)

    # Retrieval
    draw_box(ax, 9.2, 5.4, 2.2, 0.7, "Multimodal\nRetrieval", "#b45309")
    draw_arrow(ax, 10.3, 6.8, 10.3, 6.1)
    draw_arrow(ax, 8.4, 5.3, 9.2, 5.75)

    # Fusion
    draw_box(ax, 9.2, 4.2, 2.2, 0.7, "Result Fusion\n/ Reranking", "#b45309")
    draw_arrow(ax, 10.3, 5.4, 10.3, 4.9)

    # Evidence
    draw_box(ax, 6.0, 3.0, 2.4, 0.7, "Relevant Text", "#0e7490")
    draw_box(ax, 6.0, 2.0, 2.4, 0.7, "Relevant Images", "#7c3aed")
    draw_arrow(ax, 9.2, 4.55, 8.4, 3.35)
    draw_arrow(ax, 9.2, 4.2, 8.4, 2.35)

    # VLM
    draw_box(ax, 9.2, 1.0, 2.2, 0.7, "Multimodal\nLLM / VLM", "#be123c", fontsize=10)
    draw_arrow(ax, 7.2, 3.0, 9.2, 1.5)
    draw_arrow(ax, 7.2, 2.0, 9.2, 1.3)

    # Answer
    draw_box(ax, 12.2, 1.0, 2.0, 0.7, "Grounded Answer\n+ Citations", "#15803d", fontsize=9)
    draw_arrow(ax, 11.4, 1.35, 12.2, 1.35)

    # CLIP cross-modal annotation
    ax.annotate("", xy=(12.2, 6.5), xytext=(8.4, 4.9),
                arrowprops=dict(arrowstyle="<->", color="#a78bfa", lw=1.2, linestyle="--"))
    ax.text(10.3, 5.8, "CLIP cross-modal", fontsize=7, color="#a78bfa", ha="center")

    # Legend
    legend_items = [
        mpatches.Patch(color="#1e40af", label="Ingestion"),
        mpatches.Patch(color="#0e7490", label="Text Pipeline"),
        mpatches.Patch(color="#7c3aed", label="CLIP / Image Pipeline"),
        mpatches.Patch(color="#b45309", label="Vector DB / Retrieval"),
        mpatches.Patch(color="#15803d", label="Query / Output"),
        mpatches.Patch(color="#be123c", label="Generation"),
    ]
    ax.legend(handles=legend_items, loc="lower left", fontsize=8,
              facecolor="#1e293b", edgecolor="#475569", labelcolor="white",
              ncol=3, framealpha=0.9)

    out = Path("docs/architecture.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Architecture image saved: {out}")


if __name__ == "__main__":
    main()
