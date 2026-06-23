"use client";

import { useEffect, useState, useMemo } from "react";
import dynamic from "next/dynamic";

// Load react-plotly.js dynamically to avoid SSR "window/document is not defined" error
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface LongevityRecord {
  seqn: number;
  surveyCycle: string;
  ageYears: number;
  gender: string;
  longevityGroup: string;
  healthyAgingScore: number;
  cardioRiskScore?: number | null;
  nutritionalQualityScore?: number | null;
}

const FETCH_SIZE = 2000;
const PAGE_SIZE = 20;

function round1(v: number) { return Math.round(v * 10) / 10; }

async function fetchAll(): Promise<LongevityRecord[]> {
  const first = await fetch(`/api/proxy/member1-2?page=0&size=${FETCH_SIZE}&sort=surveyCycle,desc`).then(r => r.json());
  const all: LongevityRecord[] = [...(first.content || [])];
  const totalPages: number = first.totalPages || 1;
  if (totalPages > 1) {
    const rest = await Promise.all(
      Array.from({ length: totalPages - 1 }, (_, i) =>
        fetch(`/api/proxy/member1-2?page=${i + 1}&size=${FETCH_SIZE}&sort=surveyCycle,desc`).then(r => r.json())
      )
    );
    rest.forEach(json => all.push(...(json.content || [])));
  }
  return all;
}

function exportCSV(rows: LongevityRecord[]) {
  const headers = ["SEQN", "Ciclo", "Edad", "Género", "Grupo Longevidad", "Healthy Aging Score", "Cardio Risk Score", "Nutritional Quality Score"];
  const lines = rows.map(r =>
    [r.seqn, r.surveyCycle, r.ageYears, r.gender, r.longevityGroup,
    round1(r.healthyAgingScore), r.cardioRiskScore ?? "", r.nutritionalQualityScore ?? ""].join(",")
  );
  const blob = new Blob([headers.join(",") + "\n" + lines.join("\n")], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a"); a.href = url; a.download = "nhanes_export.csv"; a.click();
  URL.revokeObjectURL(url);
}

// ── UI primitives ──────────────────────────────────────────────────────────
function ScoreBar({ value, type }: { value: number | null | undefined; type: "cardio" | "nutrition" | "aging" }) {
  if (value === null || value === undefined) return <span className="text-gray-600 text-sm">—</span>;
  const display = round1(value);
  const pct = Math.min(Math.max(value, 0), 100);
  const color = type === "cardio"
    ? pct > 80 ? "#ef4444" : pct > 50 ? "#f97316" : "#22c55e"
    : type === "nutrition"
      ? pct > 70 ? "#22c55e" : pct > 40 ? "#f97316" : "#ef4444"
      : pct > 70 ? "#2dd4bf" : pct > 40 ? "#60a5fa" : "#a78bfa";
  return (
    <div className="flex items-center gap-2 justify-end">
      <span className="text-xs font-mono w-10 text-right" style={{ color }}>{display}</span>
      <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      {type === "cardio" && pct > 80 && <span className="text-red-400 text-xs">⚠</span>}
    </div>
  );
}

function LongevityBadge({ group }: { group: string }) {
  const style = group.includes("Extrema") ? "bg-purple-900/50 text-purple-300 border-purple-700/50"
    : group.includes("Alta") ? "bg-teal-900/50 text-teal-300 border-teal-700/50"
      : "bg-blue-900/50 text-blue-300 border-blue-700/50";
  return <span className={`px-2 py-1 rounded-full text-xs font-medium border ${style}`}>{group}</span>;
}

function StatCard({ label, value, sub, accent }: { label: string; value: string | number; sub?: string; accent: string }) {
  return (
    <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
      <p className="text-xs text-gray-400 uppercase tracking-widest mb-1">{label}</p>
      <p className="text-2xl font-bold" style={{ color: accent }}>{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}

const TABS = ["Resumen", "Análisis", "Tabla"] as const;
type Tab = typeof TABS[number];

const PLOT_LAYOUT_BASE = {
  paper_bgcolor: "transparent", plot_bgcolor: "rgba(255,255,255,0.03)",
  font: { color: "#9ca3af", size: 11 },
  margin: { t: 20, r: 16, b: 50, l: 60 },
  height: 300,
  legend: { font: { color: "#9ca3af", size: 11 } },
};

const AXIS_STYLE = { gridcolor: "rgba(255,255,255,0.06)", color: "#6b7280", linecolor: "rgba(255,255,255,0.1)" };

// ── Main ───────────────────────────────────────────────────────────────────
export default function Home() {
  const [allData, setAllData] = useState<LongevityRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMsg, setLoadingMsg] = useState("Conectando al backend...");
  const [activeTab, setActiveTab] = useState<Tab>("Resumen");
  const [page, setPage] = useState(0);

  // Filters
  const [filterGroup, setFilterGroup] = useState("Todos");
  const [filterCycle, setFilterCycle] = useState("Todos");
  const [filterGender, setFilterGender] = useState("Todos");
  const [ageRange, setAgeRange] = useState<[number, number]>([0, 120]);
  const [showCritical, setShowCritical] = useState(false);

  // Member 3 states
  const [member3Data, setMember3Data] = useState<any[]>([]);
  const [loadingM3, setLoadingM3] = useState(true);

  useEffect(() => {
    setLoadingMsg("Cargando dataset completo...");
    fetchAll().then(all => { setAllData(all); setLoading(false); }).catch(() => { setLoadingMsg("Error conectando al backend."); setLoading(false); });

    // Fetch Member 3 laboratory gold data
    fetch(`/api/proxy/member3`)
      .then((res) => res.json())
      .then((json) => {
        setMember3Data(json || []);
        setLoadingM3(false);
      })
      .catch((err) => {
        console.error("Error fetching member 3 data", err);
        setLoadingM3(false);
      });
  }, []);

  const ageMin = useMemo(() => allData.length ? Math.min(...allData.map(r => r.ageYears)) : 0, [allData]);
  const ageMax = useMemo(() => allData.length ? Math.max(...allData.map(r => r.ageYears)) : 120, [allData]);

  // Set age range once data loads
  useEffect(() => { if (allData.length) setAgeRange([ageMin, ageMax]); }, [ageMin, ageMax]);

  const longevityGroups = useMemo(() => ["Todos", ...Array.from(new Set(allData.map(r => r.longevityGroup))).sort()], [allData]);
  const surveyCycles = useMemo(() => ["Todos", ...Array.from(new Set(allData.map(r => r.surveyCycle))).sort().reverse()], [allData]);

  // Filtered dataset (used everywhere — stats, charts, table)
  const filtered = useMemo(() => {
    let rows = allData;
    if (showCritical) rows = rows.filter(r => (r.cardioRiskScore ?? 0) > 80 && (r.nutritionalQualityScore ?? 100) < 40);
    if (filterGroup !== "Todos") rows = rows.filter(r => r.longevityGroup === filterGroup);
    if (filterCycle !== "Todos") rows = rows.filter(r => r.surveyCycle === filterCycle);
    if (filterGender !== "Todos") rows = rows.filter(r => r.gender === filterGender);
    rows = rows.filter(r => r.ageYears >= ageRange[0] && r.ageYears <= ageRange[1]);
    return rows;
  }, [allData, showCritical, filterGroup, filterCycle, filterGender, ageRange]);

  useEffect(() => { setPage(0); }, [filterGroup, filterCycle, filterGender, ageRange, showCritical]);

  const criticalCount = useMemo(() =>
    allData.filter(r => (r.cardioRiskScore ?? 0) > 80 && (r.nutritionalQualityScore ?? 100) < 40).length,
    [allData]
  );

  // Stats from filtered
  const avg = (key: keyof LongevityRecord) => {
    const vals = filtered.map(r => r[key] as number).filter(v => v != null && !isNaN(v));
    return vals.length ? round1(vals.reduce((a, b) => a + b, 0) / vals.length) : "—";
  };

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageRows = useMemo(() => filtered.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE), [filtered, page]);

  // ── Chart data ─────────────────────────────────────────────────────────
  // 1. Scatter: nutrition vs cardio
  const scatterSample = useMemo(() => {
    const valid = filtered.filter(r => r.nutritionalQualityScore != null && r.cardioRiskScore != null);
    return valid.length > 3000 ? valid.filter((_, i) => i % Math.ceil(valid.length / 3000) === 0) : valid;
  }, [filtered]);

  // 2. Bar: avg scores by survey cycle (from allData, not filtered, to always show full timeline)
  const cycleStats = useMemo(() => {
    const cycles = Array.from(new Set(allData.map(r => r.surveyCycle))).sort();
    return cycles.map(cycle => {
      const rows = allData.filter(r => r.surveyCycle === cycle);
      const avgScore = (key: keyof LongevityRecord) => {
        const vals = rows.map(r => r[key] as number).filter(v => v != null);
        return vals.length ? round1(vals.reduce((a, b) => a + b, 0) / vals.length) : 0;
      };
      return { cycle, cardio: avgScore("cardioRiskScore"), nutrition: avgScore("nutritionalQualityScore"), aging: avgScore("healthyAgingScore") };
    });
  }, [allData]);

  // 3. Histogram: age distribution by longevity group (filtered)
  const longevityColors: Record<string, string> = {
    "Longevidad Base (<65)": "#60a5fa",
    "Longevidad Alta (65-79)": "#2dd4bf",
    "Longevidad Extrema (80+)": "#a78bfa",
  };

  const ageHistTraces = useMemo(() => {
    const groups = Array.from(new Set(filtered.map(r => r.longevityGroup)));
    return groups.map(g => ({
      x: filtered.filter(r => r.longevityGroup === g).map(r => r.ageYears),
      type: "histogram" as const,
      name: g.replace("Longevidad ", ""),
      opacity: 0.75,
      marker: { color: longevityColors[g] || "#9ca3af" },
      nbinsx: 20,
    }));
  }, [filtered]);

  // 4. Box plot: cardio risk by longevity group
  const boxTraces = useMemo(() => {
    const groups = Array.from(new Set(filtered.map(r => r.longevityGroup)));
    return groups.map(g => ({
      y: filtered.filter(r => r.longevityGroup === g && r.cardioRiskScore != null).map(r => r.cardioRiskScore as number),
      type: "box" as const,
      name: g.replace("Longevidad ", ""),
      marker: { color: longevityColors[g] || "#9ca3af" },
      boxpoints: false as const,
    }));
  }, [filtered]);

  // 5. Donut: gender distribution
  const genderCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    filtered.forEach(r => { counts[r.gender] = (counts[r.gender] || 0) + 1; });
    return counts;
  }, [filtered]);

  // 6. Donut: longevity group distribution
  const groupCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    filtered.forEach(r => { counts[r.longevityGroup] = (counts[r.longevityGroup] || 0) + 1; });
    return counts;
  }, [filtered]);

  const filterActive = filterGroup !== "Todos" || filterCycle !== "Todos" || filterGender !== "Todos" || ageRange[0] !== ageMin || ageRange[1] !== ageMax || showCritical;

  // ── Render ─────────────────────────────────────────────────────────────
  return (
    <main className="min-h-screen bg-gray-900 text-white">
      {/* Top bar */}
      <div className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-end justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-blue-500">
              NHANES Longevity Dashboard
            </h1>
            <p className="text-gray-400 text-sm mt-0.5">Análisis de Nutrición y Riesgo Cardiovascular — Miembros 1 y 2 (Claudio y Martín)</p>
          </div>
          {!loading && (
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <span className="w-2 h-2 rounded-full bg-teal-400 inline-block"></span>
              {allData.length.toLocaleString()} registros cargados
              {filterActive && (
                <span className="ml-2 px-2 py-0.5 bg-teal-900/50 text-teal-300 border border-teal-700/50 rounded-full">
                  {filtered.length.toLocaleString()} filtrados
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">

        {/* Loading */}
        {loading && (
          <div className="flex flex-col items-center justify-center h-64 gap-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500" />
            <p className="text-gray-400 text-sm">{loadingMsg}</p>
          </div>
        )}

        {!loading && (<>

          {/* Stat cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Pacientes" value={filtered.length.toLocaleString()} sub={filterActive ? `de ${allData.length.toLocaleString()} totales` : "Dataset completo"} accent="#2dd4bf" />
            <StatCard label="Riesgo cardio prom." value={avg("cardioRiskScore")} sub="Escala 0–100" accent="#f97316" />
            <StatCard label="Calidad nutricional prom." value={avg("nutritionalQualityScore")} sub="Escala 0–100" accent="#22c55e" />
            <StatCard label="Pacientes críticos" value={filterActive ? filtered.filter(r => (r.cardioRiskScore ?? 0) > 80 && (r.nutritionalQualityScore ?? 100) < 40).length : criticalCount} sub="Cardio >80 y Nutrición <40" accent="#ef4444" />
          </div>

          {/* Critical banner */}
          {criticalCount > 0 && (
            <div className="bg-red-950/60 border border-red-700/50 rounded-xl p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-red-400 text-xl">⚠</span>
                <div>
                  <p className="text-red-300 font-semibold text-sm">{criticalCount} pacientes en riesgo crítico en el dataset completo</p>
                  <p className="text-red-500 text-xs">Riesgo cardiovascular alto combinado con dieta deficiente</p>
                </div>
              </div>
              <button
                onClick={() => { setShowCritical(v => !v); setFilterGroup("Todos"); setFilterCycle("Todos"); setFilterGender("Todos"); }}
                className={`text-xs px-4 py-2 rounded-lg border transition-colors ${showCritical ? "bg-red-700 border-red-600 text-white" : "border-red-700 text-red-300 hover:bg-red-900/40"}`}
              >
                {showCritical ? "Ver todos" : "Filtrar críticos"}
              </button>
            </div>
          )}

          {/* Global filters bar */}
          <div className="bg-gray-800 rounded-xl px-5 py-4 border border-gray-700">
            <div className="flex flex-wrap gap-4 items-end">
              <div>
                <p className="text-xs text-gray-400 mb-1 uppercase tracking-wider">Ciclo</p>
                <select value={filterCycle} onChange={e => { setFilterCycle(e.target.value); setShowCritical(false); }}
                  className="bg-gray-700 border border-gray-600 text-sm rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:border-teal-500">
                  {surveyCycles.map(c => <option key={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <p className="text-xs text-gray-400 mb-1 uppercase tracking-wider">Grupo longevidad</p>
                <select value={filterGroup} onChange={e => { setFilterGroup(e.target.value); setShowCritical(false); }}
                  className="bg-gray-700 border border-gray-600 text-sm rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:border-teal-500">
                  {longevityGroups.map(g => <option key={g}>{g}</option>)}
                </select>
              </div>
              <div>
                <p className="text-xs text-gray-400 mb-1 uppercase tracking-wider">Género</p>
                <select value={filterGender} onChange={e => { setFilterGender(e.target.value); setShowCritical(false); }}
                  className="bg-gray-700 border border-gray-600 text-sm rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:border-teal-500">
                  {["Todos", "Hombre", "Mujer"].map(g => <option key={g}>{g}</option>)}
                </select>
              </div>
              <div className="flex-1 min-w-48">
                <p className="text-xs text-gray-400 mb-1 uppercase tracking-wider">
                  Rango de edad: {ageRange[0]}–{ageRange[1]} años
                </p>
                <div className="flex gap-2 items-center">
                  <input type="range" min={ageMin} max={ageMax} value={ageRange[0]}
                    onChange={e => setAgeRange([Math.min(Number(e.target.value), ageRange[1] - 1), ageRange[1]])}
                    className="flex-1 accent-teal-500" />
                  <input type="range" min={ageMin} max={ageMax} value={ageRange[1]}
                    onChange={e => setAgeRange([ageRange[0], Math.max(Number(e.target.value), ageRange[0] + 1)])}
                    className="flex-1 accent-teal-500" />
                </div>
              </div>
              {filterActive && (
                <button onClick={() => { setFilterGroup("Todos"); setFilterCycle("Todos"); setFilterGender("Todos"); setAgeRange([ageMin, ageMax]); setShowCritical(false); }}
                  className="text-xs px-3 py-1.5 rounded-lg border border-gray-600 text-gray-400 hover:text-white hover:border-gray-400 transition-colors">
                  ✕ Limpiar filtros
                </button>
              )}
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 border-b border-gray-700">
            {TABS.map(tab => (
              <button key={tab} onClick={() => setActiveTab(tab)}
                className={`px-5 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${activeTab === tab ? "border-teal-500 text-teal-400" : "border-transparent text-gray-400 hover:text-gray-200"
                  }`}>
                {tab}
              </button>
            ))}
          </div>

          {/* ── TAB: Resumen ─────────────────────────────────────────── */}
          {activeTab === "Resumen" && (
            <div className="space-y-6">

              {/* Row 1: Scatter + Bar scores por ciclo */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                  <h3 className="text-sm font-semibold mb-1">Nutrición vs Riesgo cardiovascular</h3>
                  <p className="text-xs text-gray-500 mb-3">{scatterSample.length.toLocaleString()} pacientes — rojo: críticos</p>
                  <Plot
                    data={[{
                      x: scatterSample.map(r => r.nutritionalQualityScore),
                      y: scatterSample.map(r => r.cardioRiskScore),
                      mode: "markers", type: "scatter",
                      marker: {
                        color: scatterSample.map(r => (r.cardioRiskScore ?? 0) > 80 && (r.nutritionalQualityScore ?? 100) < 40 ? "#ef4444" : "#2dd4bf"),
                        size: 5, opacity: 0.6,
                      },
                      text: scatterSample.map(r => `SEQN: ${r.seqn}<br>Edad: ${r.ageYears}<br>${r.longevityGroup}`),
                      hovertemplate: "<b>%{text}</b><br>Nutrición: %{x}<br>Cardio: %{y}<extra></extra>",
                    }]}
                    layout={{ ...PLOT_LAYOUT_BASE, xaxis: { ...AXIS_STYLE, title: { text: "Nutritional Quality Score" } }, yaxis: { ...AXIS_STYLE, title: { text: "Cardio Risk Score" } } }}
                    config={{ displayModeBar: false, responsive: true }} style={{ width: "100%" }}
                  />
                </div>

                <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                  <h3 className="text-sm font-semibold mb-1">Scores promedio por ciclo</h3>
                  <p className="text-xs text-gray-500 mb-3">Evolución de la salud poblacional entre encuestas</p>
                  <Plot
                    data={[
                      { x: cycleStats.map(c => c.cycle), y: cycleStats.map(c => c.cardio), type: "bar", name: "Cardio Risk", marker: { color: "#f97316" } },
                      { x: cycleStats.map(c => c.cycle), y: cycleStats.map(c => c.nutrition), type: "bar", name: "Nutritional Quality", marker: { color: "#22c55e" } },
                      { x: cycleStats.map(c => c.cycle), y: cycleStats.map(c => c.aging), type: "bar", name: "Healthy Aging", marker: { color: "#2dd4bf" } },
                    ]}
                    layout={{ ...PLOT_LAYOUT_BASE, barmode: "group", xaxis: { ...AXIS_STYLE }, yaxis: { ...AXIS_STYLE, range: [0, 100] }, legend: { orientation: "h", y: -0.25, font: { color: "#9ca3af", size: 10 } } }}
                    config={{ displayModeBar: false, responsive: true }} style={{ width: "100%" }}
                  />
                </div>
              </div>

              {/* Row 2: Donuts */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                  <h3 className="text-sm font-semibold mb-1">Distribución por género</h3>
                  <p className="text-xs text-gray-500 mb-3">Selección actual</p>
                  <Plot
                    data={[{
                      values: Object.values(genderCounts),
                      labels: Object.keys(genderCounts),
                      type: "pie", hole: 0.55,
                      marker: { colors: ["#60a5fa", "#f472b6"] },
                      textinfo: "label+percent",
                      textfont: { color: "#d1d5db", size: 11 },
                      hovertemplate: "%{label}: %{value} pacientes<extra></extra>",
                    }]}
                    layout={{ ...PLOT_LAYOUT_BASE, height: 260, showlegend: false, margin: { t: 10, r: 10, b: 10, l: 10 } }}
                    config={{ displayModeBar: false, responsive: true }} style={{ width: "100%" }}
                  />
                </div>

                <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                  <h3 className="text-sm font-semibold mb-1">Distribución por grupo de longevidad</h3>
                  <p className="text-xs text-gray-500 mb-3">Selección actual</p>
                  <Plot
                    data={[{
                      values: Object.values(groupCounts),
                      labels: Object.keys(groupCounts).map(k => k.replace("Longevidad ", "")),
                      type: "pie", hole: 0.55,
                      marker: { colors: ["#60a5fa", "#2dd4bf", "#a78bfa"] },
                      textinfo: "label+percent",
                      textfont: { color: "#d1d5db", size: 11 },
                      hovertemplate: "%{label}: %{value} pacientes<extra></extra>",
                    }]}
                    layout={{ ...PLOT_LAYOUT_BASE, height: 260, showlegend: false, margin: { t: 10, r: 10, b: 10, l: 10 } }}
                    config={{ displayModeBar: false, responsive: true }} style={{ width: "100%" }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* ── TAB: Análisis ────────────────────────────────────────── */}
          {activeTab === "Análisis" && (
            <div className="space-y-6">

              {/* Row 1: Histogram + Box plot */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                  <h3 className="text-sm font-semibold mb-1">Distribución de edades por grupo</h3>
                  <p className="text-xs text-gray-500 mb-3">Histograma — selección actual</p>
                  <Plot
                    data={ageHistTraces}
                    layout={{ ...PLOT_LAYOUT_BASE, barmode: "overlay", xaxis: { ...AXIS_STYLE, title: { text: "Edad (años)" } }, yaxis: { ...AXIS_STYLE, title: { text: "Pacientes" } }, legend: { font: { color: "#9ca3af", size: 10 }, orientation: "h", y: -0.28 } }}
                    config={{ displayModeBar: false, responsive: true }} style={{ width: "100%" }}
                  />
                </div>

                <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                  <h3 className="text-sm font-semibold mb-1">Riesgo cardiovascular por grupo</h3>
                  <p className="text-xs text-gray-500 mb-3">Box plot — mediana, IQR y outliers</p>
                  <Plot
                    data={boxTraces}
                    layout={{ ...PLOT_LAYOUT_BASE, xaxis: { ...AXIS_STYLE }, yaxis: { ...AXIS_STYLE, title: { text: "Cardio Risk Score" }, range: [0, 105] }, showlegend: false }}
                    config={{ displayModeBar: false, responsive: true }} style={{ width: "100%" }}
                  />
                </div>
              </div>

              {/* Row 2: Nutritional quality histogram */}
              <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <h3 className="text-sm font-semibold mb-1">Distribución de calidad nutricional</h3>
                <p className="text-xs text-gray-500 mb-3">Todos los pacientes de la selección actual</p>
                <Plot
                  data={[{
                    x: filtered.map(r => r.nutritionalQualityScore).filter(v => v != null) as number[],
                    type: "histogram",
                    nbinsx: 25,
                    marker: { color: "#22c55e", opacity: 0.75 },
                    name: "Pacientes",
                  }]}
                  layout={{ ...PLOT_LAYOUT_BASE, height: 220, xaxis: { ...AXIS_STYLE, title: { text: "Nutritional Quality Score" } }, yaxis: { ...AXIS_STYLE, title: { text: "Pacientes" } } }}
                  config={{ displayModeBar: false, responsive: true }} style={{ width: "100%" }}
                />
              </div>
            </div>
          )}

          {/* ── TAB: Tabla ───────────────────────────────────────────── */}
          {activeTab === "Tabla" && (
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-lg font-semibold">
                  {showCritical ? "Pacientes en riesgo crítico" : "Registros procesados"}
                  <span className="ml-2 text-sm text-gray-400 font-normal">
                    ({filtered.length.toLocaleString()} total)
                  </span>
                </h2>
                <button
                  onClick={() => exportCSV(filtered)}
                  className="flex items-center gap-2 text-xs px-4 py-2 rounded-lg border border-teal-700 text-teal-300 hover:bg-teal-900/30 transition-colors"
                >
                  ↓ Exportar CSV ({filtered.length.toLocaleString()})
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-gray-700 text-gray-400 uppercase text-xs">
                      <th className="p-3">SEQN</th>
                      <th className="p-3">Ciclo</th>
                      <th className="p-3">Edad</th>
                      <th className="p-3">Género</th>
                      <th className="p-3">Grupo Longevidad</th>
                      <th className="p-3 text-right">Healthy Aging</th>
                      <th className="p-3 text-right">Cardio Risk</th>
                      <th className="p-3 text-right">Nutritional Quality</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pageRows.map(record => (
                      <tr key={record.seqn}
                        className={`border-b border-gray-700/50 transition-colors ${(record.cardioRiskScore ?? 0) > 80 && (record.nutritionalQualityScore ?? 100) < 40
                            ? "bg-red-950/20 hover:bg-red-950/30"
                            : "hover:bg-gray-700/30"
                          }`}>
                        <td className="p-3 font-mono text-gray-300 text-sm">{record.seqn}</td>
                        <td className="p-3 text-sm text-gray-300">{record.surveyCycle}</td>
                        <td className="p-3 text-gray-300">{record.ageYears}</td>
                        <td className="p-3 text-gray-300">{record.gender}</td>
                        <td className="p-3"><LongevityBadge group={record.longevityGroup} /></td>
                        <td className="p-3"><ScoreBar value={record.healthyAgingScore} type="aging" /></td>
                        <td className="p-3"><ScoreBar value={record.cardioRiskScore} type="cardio" /></td>
                        <td className="p-3"><ScoreBar value={record.nutritionalQualityScore} type="nutrition" /></td>
                      </tr>
                    ))}
                    {pageRows.length === 0 && (
                      <tr><td colSpan={8} className="p-6 text-center text-gray-500">Sin resultados para los filtros seleccionados.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-between mt-5 pt-4 border-t border-gray-700">
                <span className="text-sm text-gray-400">Página {page + 1} de {totalPages}</span>
                <div className="flex gap-2">
                  <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
                    className="px-4 py-1.5 text-sm rounded-lg border border-gray-600 text-gray-300 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
                    ← Anterior
                  </button>
                  <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}
                    className="px-4 py-1.5 text-sm rounded-lg border border-gray-600 text-gray-300 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
                    Siguiente →
                  </button>
                </div>
              </div>
            </div>
          )}

        </>)}
        
        {/* Sección Miembro 3 - Matías Retamal (Clínicos y Longevidad) */}
        {!loading && (
        <div className="bg-gray-800 rounded-xl p-6 shadow-2xl border border-gray-700 mt-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-teal-400">
              Análisis Clínico y de Longevidad — Miembro 3 (Matías Retamal)
            </h2>
            <div className="text-sm text-gray-400">
              {loadingM3 ? "Cargando datos clínicos..." : `${member3Data.length} registros cargados`}
            </div>
          </div>

          {loadingM3 ? (
            <div className="flex justify-center items-center h-48">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
            </div>
          ) : member3Data.length === 0 ? (
            <div className="text-center p-6 text-gray-500">
              No hay datos clínicos de la capa Gold disponibles. Asegúrate de correr la pipeline de Kedro y exportar a PostgreSQL.
            </div>
          ) : (
            <div>
              {/* KPIs de laboratorio */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700/50">
                  <div className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Índice de Riesgo Promedio</div>
                  <div className="text-2xl font-bold text-purple-400 mt-1">
                    {(member3Data.reduce((acc, r) => acc + (r.longevity_risk_index ?? r.longevityRiskIndex ?? 0), 0) / member3Data.length).toFixed(2)}%
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Medida compuesta de 8 biomarcadores</div>
                </div>
                <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700/50">
                  <div className="text-xs text-gray-400 uppercase tracking-wider font-semibold">HbA1c Promedio</div>
                  <div className="text-2xl font-bold text-teal-400 mt-1">
                    {(member3Data.reduce((acc, r) => acc + (r.LBXGH ?? r.lbxgh ?? 0), 0) / member3Data.length).toFixed(2)}%
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Nivel promedio de glicosilada</div>
                </div>
                <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700/50">
                  <div className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Colesterol Total Promedio</div>
                  <div className="text-2xl font-bold text-blue-400 mt-1">
                    {(member3Data.reduce((acc, r) => acc + (r.LBXSCH ?? r.lbxsch ?? 0), 0) / member3Data.length).toFixed(2)} mg/dL
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Nivel promedio de colesterol en sangre</div>
                </div>
              </div>

              {/* Gráficos de Plotly */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Gráfico 1: Tiers de Riesgo */}
                <div className="bg-gray-950 p-4 rounded-lg border border-gray-700/50 flex flex-col items-center">
                  <h3 className="text-sm font-semibold mb-3 text-gray-300">Distribución de Categorías de Riesgo de Longevidad</h3>
                  <Plot
                    data={[
                      {
                        type: 'bar',
                        x: ['Low', 'Moderate', 'High', 'Critical'],
                        y: [
                          member3Data.filter(r => (r.risk_tier ?? r.riskTier) === 'Low').length,
                          member3Data.filter(r => (r.risk_tier ?? r.riskTier) === 'Moderate').length,
                          member3Data.filter(r => (r.risk_tier ?? r.riskTier) === 'High').length,
                          member3Data.filter(r => (r.risk_tier ?? r.riskTier) === 'Critical').length
                        ],
                        marker: {
                          color: ['#2dd4bf', '#3b82f6', '#a855f7', '#ef4444'],
                        }
                      }
                    ]}
                    layout={{
                      width: 450,
                      height: 320,
                      paper_bgcolor: 'rgba(0,0,0,0)',
                      plot_bgcolor: 'rgba(0,0,0,0)',
                      font: { color: '#9ca3af' },
                      margin: { t: 20, b: 40, l: 40, r: 20 },
                      xaxis: { gridcolor: '#374151' },
                      yaxis: { gridcolor: '#374151' }
                    }}
                    config={{ displayModeBar: false }}
                  />
                </div>

                {/* Gráfico 2: HbA1c vs Riesgo */}
                <div className="bg-gray-950 p-4 rounded-lg border border-gray-700/50 flex flex-col items-center">
                  <h3 className="text-sm font-semibold mb-3 text-gray-300">Relación: HbA1c vs. Índice de Riesgo de Longevidad</h3>
                  <Plot
                    data={[
                      {
                        x: member3Data.map(r => r.LBXGH ?? r.lbxgh),
                        y: member3Data.map(r => r.longevity_risk_index ?? r.longevityRiskIndex),
                        mode: 'markers',
                        type: 'scatter',
                        marker: {
                          color: '#a855f7',
                          size: 6,
                          opacity: 0.7
                        }
                      }
                    ]}
                    layout={{
                      width: 450,
                      height: 320,
                      paper_bgcolor: 'rgba(0,0,0,0)',
                      plot_bgcolor: 'rgba(0,0,0,0)',
                      font: { color: '#9ca3af' },
                      margin: { t: 20, b: 40, l: 40, r: 20 },
                      xaxis: { title: 'HbA1c (%)', gridcolor: '#374151', titlefont: { size: 12 } },
                      yaxis: { title: 'Índice de Riesgo (%)', gridcolor: '#374151', titlefont: { size: 12 } }
                    }}
                    config={{ displayModeBar: false }}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
        )}

      </div>
    </main>
  );
}