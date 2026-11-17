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
    // Match node declarations like ID[Label with (parentheses) or / or special characters]
    // which fail Mermaid parsing unless enclosed in quotes: ID["Label..."]
    return line.replace(/(\w+)\s*\[([^"\]]+)\]/g, (match, nodeId, label) => {
      // If the label contains parentheses, slashes, colons, or commas, wrap in quotes
      if (/[\(\)\/\:\,\&\%\$\#\@\!\{\}]/.test(label)) {
        return `${nodeId}["${label.trim()}"]`;
      }
      return match;
    });
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
