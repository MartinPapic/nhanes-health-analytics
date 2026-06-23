"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

// Plotly must be loaded dynamically with SSR disabled
const Plot = dynamic(() => import("react-plotly.js"), { 
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-card/50 rounded-xl animate-pulse">
      <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
    </div>
  )
});

interface PlotlyWrapperProps {
  data: any[];
  layout?: any;
  config?: any;
  className?: string;
}

export function PlotlyWrapper({ data, layout, config, className }: PlotlyWrapperProps) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) return null;

  const defaultLayout = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: {
      family: 'var(--font-inter), Arial, sans-serif',
      color: 'var(--foreground)'
    },
    margin: { t: 40, r: 20, l: 40, b: 40 },
    ...layout
  };

  const defaultConfig = {
    displayModeBar: false,
    responsive: true,
    ...config
  };

  return (
    <div className={`w-full h-full ${className || ''}`}>
      <Plot
        data={data}
        layout={defaultLayout}
        config={defaultConfig}
        useResizeHandler={true}
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
}
