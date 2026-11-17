"use client";
import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
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
 * Sanitizes common LLM Mermaid syntax mistakes before rendering:
 * 1. Wraps unquoted node labels with special characters (parentheses, slashes, brackets) in double quotes.
 *    e.g. `SR2[Retriever (vector DB / API)]` -> `SR2["Retriever (vector DB / API)"]`
 * 2. Cleans unbalanced quotes or invalid trailing characters.
 */
function sanitizeMermaidCode(code: string): string {
  if (!code) return "";
  let lines = code.trim().split("\n");
  
  let cleanedLines = lines.map(line => {
    // 1. Sanitize edge labels |...|:
    // Angle brackets like `<RET>` or `<CRIT>` get treated as unclosed HTML tags by Mermaid's lexer.
    // Parentheses or quotes inside |...| can also break parsing.
    line = line.replace(/\|([^|]+)\|/g, (match, edgeLabel) => {
      let cleanedLabel = edgeLabel
        .replace(/</g, '')
        .replace(/>/g, '')
        .replace(/"/g, "'")
        .trim();
      return `|"${cleanedLabel}"|`;
    });

    // 2. Sanitize node definitions:
    // Any node bracket declaration containing parentheses, colons, slashes, or special symbols
    // e.g. ID[Label (extra info)] -> ID["Label (extra info)"]
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
        // Clean out any fallback error elements injected by mermaid into the DOM
        const errorElement = document.getElementById(`d${chart}`);
        if (errorElement) errorElement.remove();
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
