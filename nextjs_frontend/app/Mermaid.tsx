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

export default function Mermaid({ chart }: MermaidProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>('');
  const [hasError, setHasError] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    const renderChart = async () => {
      if (!chart || !containerRef.current) return;
      try {
        const id = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
        const { svg } = await mermaid.render(id, chart);
        if (isMounted) {
          setSvgContent(svg);
          setHasError(false);
        }
      } catch (err) {
        console.warn("Mermaid parsing fallback:", err);
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
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-xs font-mono text-slate-400 overflow-x-auto">
        <div className="text-amber-400 font-semibold mb-1">Diagram (Raw Code):</div>
        <pre>{chart}</pre>
      </div>
    );
  }

  return (
    <div className="my-4 p-4 bg-[#111827] border border-gray-700/80 rounded-xl overflow-x-auto flex justify-center shadow-lg">
      <div ref={containerRef} dangerouslySetInnerHTML={{ __html: svgContent }} />
    </div>
  );
}
