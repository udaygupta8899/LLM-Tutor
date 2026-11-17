"use client";
import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  suppressErrorRendering: true,
  theme: 'dark',
  securityLevel: 'loose',
  themeVariables: {
    darkMode: true,
    background: '#111827',
    primaryColor: '#4f46e5',
    primaryTextColor: '#f3f4f6',
    primaryBorderColor: '#6366f1',
    lineColor: '#93c5fd',
    secondaryColor: '#1f2937',
    tertiaryColor: '#374151'
  }
});

interface MermaidProps {
  chart: string;
}

/**
 * Robust sanitizer for common LLM Mermaid syntax quirks:
 * 1. Merges illegal hybrid arrows like `L1 -- "text1" -->|text2| R` into `L1 -->|"text1 (text2)"| R`.
 * 2. Cleans angle brackets `<...>` from edge labels to prevent Mermaid's HTML tag lexer from breaking.
 * 3. Encloses edge labels inside double quotes `|"...""|`.
 * 4. Quotes node labels containing special characters like parentheses, slashes, or brackets.
 */
function sanitizeMermaidCode(code: string): string {
  if (!code) return "";
  let lines = code.trim().split("\n");
  
  let cleanedLines = lines.map(line => {
    // 1. Fix illegal hybrid arrows: NodeA -- "Label1" -->|Label2| NodeB
    line = line.replace(/(\w+)\s*--\s*(?:"([^"]+)"|'([^']+)'|([^\->]+))\s*-->\s*\|([^|]+)\|\s*(\w+)/g, 
      (match, n1, q1, q2, q3, label2, n2) => {
        const text1 = (q1 || q2 || q3 || "").trim().replace(/[<>]/g, "");
        const text2 = label2.trim().replace(/[<>"]/g, "");
        return `${n1} -->|"${text1} (${text2})"| ${n2}`;
      }
    );

    // 2. Sanitize standalone edge labels |...|:
    // Strip angle brackets like `<RET>` that Mermaid treats as invalid HTML tags
    line = line.replace(/\|([^|]+)\|/g, (match, edgeLabel) => {
      let cleanedLabel = edgeLabel
        .replace(/</g, '')
        .replace(/>/g, '')
        .replace(/"/g, "'")
        .trim();
      return `|"${cleanedLabel}"|`;
    });

    // 3. Sanitize node definitions: ID[Label (with special characters)] -> ID["Label..."]
    line = line.replace(/(\w+)\s*\[([^"\]]+)\]/g, (match, nodeId, label) => {
      if (/[\(\)\/\:\,\&\%\$\#\@\!\{\}\<\>]/.test(label)) {
        return `${nodeId}["${label.trim()}"]`;
      }
      return match;
    });

    return line;
  });

  return cleanedLines.join("\n");
}

export default function Mermaid({ chart }: MermaidProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>('');
  const [hasError, setHasError] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    const renderChart = async () => {
      if (!chart || !containerRef.current) return;
      try {
        const sanitized = sanitizeMermaidCode(chart);
        const id = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
        const { svg } = await mermaid.render(id, sanitized);
        if (isMounted) {
          setSvgContent(svg);
          setHasError(false);
        }
      } catch (err) {
        console.warn("Mermaid render error:", err);
        // Suppress and remove any global error popups/DOM nodes injected by mermaid
        if (typeof document !== 'undefined') {
          const errorDoms = document.querySelectorAll('[id^="dmermaid-"], .mermaid-error, [data-mermaid-error]');
          errorDoms.forEach(el => el.remove());
        }
        if (isMounted) {
          setHasError(true);
        }
      }
    };

    renderChart();
    return () => {
      isMounted = false;
    };
  }, [chart]);

  if (hasError) {
    return (
      <div className="my-3 bg-slate-900 border border-slate-800 rounded-lg p-3 text-xs font-mono text-slate-300 overflow-x-auto">
        <div className="text-indigo-400 font-semibold mb-1 flex items-center gap-1.5">
          <span>📊 Architectural Diagram</span>
        </div>
        <pre className="text-slate-400 text-[11px] leading-relaxed">{chart}</pre>
      </div>
    );
  }

  return (
    <div className="my-4 p-4 bg-[#111827] border border-gray-700/80 rounded-xl overflow-x-auto flex justify-center shadow-lg">
      <div ref={containerRef} dangerouslySetInnerHTML={{ __html: svgContent }} />
    </div>
  );
}
