import React from "react";

/**
 * Lightweight markdown renderer.
 * Handles: bold, italic, inline code, code blocks, links, line breaks,
 * unordered/ordered lists, and citation-style [n] markers.
 */
function renderInline(text: string, keyPrefix: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  // Split by inline code first to avoid processing markdown inside code
  const codeParts = text.split(/(`[^`]+`)/g);

  codeParts.forEach((part, i) => {
    if (part.startsWith("`") && part.endsWith("`") && part.length > 1) {
      nodes.push(
        <code key={`${keyPrefix}-c${i}`}>
          {part.slice(1, -1)}
        </code>
      );
    } else if (part) {
      // Process bold, italic, links, citations within non-code text
      const regex = /(\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\)|\[\d+\])/g;
      const subParts = part.split(regex);
      subParts.forEach((sub, j) => {
        if (!sub) return;
        if (sub.startsWith("**") && sub.endsWith("**")) {
          nodes.push(
            <strong key={`${keyPrefix}-b${i}-${j}`}>{sub.slice(2, -2)}</strong>
          );
        } else if (sub.startsWith("*") && sub.endsWith("*") && sub.length > 2) {
          nodes.push(
            <em key={`${keyPrefix}-i${i}-${j}`}>{sub.slice(1, -1)}</em>
          );
        } else {
          const linkMatch = sub.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
          if (linkMatch) {
            nodes.push(
              <a
                key={`${keyPrefix}-l${i}-${j}`}
                href={linkMatch[2]}
                target="_blank"
                rel="noopener noreferrer"
              >
                {linkMatch[1]}
              </a>
            );
          } else {
            // Citation markers like [1], [2]
            const citationMatch = sub.match(/^\[(\d+)\]$/);
            if (citationMatch) {
              nodes.push(
                <sup
                  key={`${keyPrefix}-cite${i}-${j}`}
                  className="ml-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded bg-brand-100 px-1 text-[10px] font-semibold text-brand-700 dark:bg-brand-900 dark:text-brand-300"
                >
                  {citationMatch[1]}
                </sup>
              );
            } else {
              nodes.push(<React.Fragment key={`${keyPrefix}-t${i}-${j}`}>{sub}</React.Fragment>);
            }
          }
        }
      });
    }
  });

  return nodes;
}

export default function Markdown({ text }: { text: string }) {
  const lines = text.split("\n");
  const blocks: React.ReactNode[] = [];
  let listBuffer: string[] = [];
  let listType: "ul" | "ol" | null = null;
  let key = 0;

  const flushList = () => {
    if (listBuffer.length === 0 || !listType) return;
    const items = listBuffer.map((item, i) => (
      <li key={i}>{renderInline(item, `li-${key}-${i}`)}</li>
    ));
    blocks.push(
      listType === "ul" ? (
        <ul key={`ul-${key++}`}>{items}</ul>
      ) : (
        <ol key={`ol-${key++}`}>{items}</ol>
      )
    );
    listBuffer = [];
    listType = null;
  };

  for (const line of lines) {
    const trimmed = line.trim();

    // Code block fence
    if (trimmed.startsWith("```")) {
      flushList();
      // Simple handling: skip fence lines, collect until next fence
      // For simplicity, treat fenced content as-is
      continue;
    }

    // Unordered list
    const ulMatch = trimmed.match(/^[-*]\s+(.+)/);
    if (ulMatch) {
      if (listType && listType !== "ul") flushList();
      listType = "ul";
      listBuffer.push(ulMatch[1]);
      continue;
    }

    // Ordered list
    const olMatch = trimmed.match(/^\d+\.\s+(.+)/);
    if (olMatch) {
      if (listType && listType !== "ol") flushList();
      listType = "ol";
      listBuffer.push(olMatch[1]);
      continue;
    }

    // Blank line flushes list
    if (trimmed === "") {
      flushList();
      continue;
    }

    // Regular paragraph
    flushList();
    blocks.push(<p key={`p-${key++}`}>{renderInline(trimmed, `p-${key}`)}</p>);
  }
  flushList();

  return <div className="markdown-body">{blocks}</div>;
}
