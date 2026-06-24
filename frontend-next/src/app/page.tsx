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

// NUEVAS TABS: El Viaje del Paciente
const TABS = ["Nutrición (M1)", "Riesgo (M2)", "Clínica (M3)", "Simulador ML"] as const;
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
  const [activeTab, setActiveTab] = useState<Tab>("Nutrición (M1)");
  const [page, setPage] = useState(0);

  // ML Simulator States
  const [simAge, setSimAge] = useState<number>(45);
  const [simGender, setSimGender] = useState<string>("Mujer");
  const [simNutrition, setSimNutrition] = useState<number>(80);
  const [simBmi, setSimBmi] = useState<number>(24);
  const [simGlucose, setSimGlucose] = useState<number>(90);
  const [simResult, setSimResult] = useState<any>(null);
  const [simLoading, setSimLoading] = useState<boolean>(false);

  const handleSimulate = async () => {
    setSimLoading(true);
    try {
      const res = await fetch("/api/proxy/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          ageYears: simAge, 
          gender: simGender, 
          nutritionalQualityScore: simNutrition,
          bmi: simBmi,
          glucose: simGlucose
        })
      });
      const data = await res.json();
      setSimResult(data);
    } catch (e) {
      console.error(e);
    } finally {
      setSimLoading(false);
    }
  };

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
        setMember3Data(Array.isArray(json) ? json : (json?.content ? json.content : []));
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

  // 2. Bar: avg scores by survey cycle
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
    <main className="min-h-screen bg-gray-900 text-white pb-12">
      {/* Top bar */}
      <div className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-end justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-blue-500">
              El Viaje del Paciente (NHANES)
            </h1>
            <p className="text-gray-400 text-sm mt-0.5">Arquitectura de Datos y Machine Learning — Claudio, Martín y Matías</p>
          </div>
          {!loading && (
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <span className="w-2 h-2 rounded-full bg-teal-400 inline-block"></span>
              {allData.length.toLocaleString()} registros poblacionales
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

          {/* Tabs Nav */}
          <div className="flex gap-1 border-b border-gray-700">
            {TABS.map((tab, idx) => {
              // Add a subtle gradient text color for the ML tab
              const isML = tab === "Simulador ML";
              return (
                <button key={tab} onClick={() => setActiveTab(tab)}
                  className={`px-6 py-3 text-sm font-semibold transition-all border-b-2 -mb-px flex items-center gap-2
                  ${activeTab === tab 
                    ? isML ? "border-purple-500 text-purple-400" : "border-teal-500 text-teal-400" 
                    : "border-transparent text-gray-400 hover:text-gray-200"
                  }`}>
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${activeTab === tab ? (isML ? 'bg-purple-900/50' : 'bg-teal-900/50') : 'bg-gray-800'}`}>
                    {idx + 1}
                  </span>
                  {tab}
                </button>
              )
            })}
          </div>

          {/* ── TAB 1: Nutrición (M1) ─────────────────────────────────────────── */}
          {activeTab === "Nutrición (M1)" && (
            <div className="space-y-6 animate-fade-in-up">
              
              <div className="mb-2 mt-4">
                <h2 className="text-xl font-bold text-teal-400">1. Evaluación Nutricional y Estilo de Vida</h2>
                <p className="text-sm text-gray-400">Responsable: Claudio. Fase inicial del viaje del paciente donde exploramos los hábitos dietarios y la calidad nutricional, la primera línea de defensa de la longevidad.</p>
              </div>

              {/* Stat cards Nutrición */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <StatCard label="Pacientes Registrados" value={filtered.length.toLocaleString()} sub={filterActive ? `Filtrados` : "Dataset completo"} accent="#2dd4bf" />
                <StatCard label="Calidad Nutricional Promedio" value={avg("nutritionalQualityScore")} sub="Escala 0–100 (HEI)" accent="#22c55e" />
                <StatCard label="Edad Promedio" value={avg("ageYears")} sub="Años de vida" accent="#60a5fa" />
              </div>

              {/* Row 1: Nutrición Graphs */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                  <h3 className="text-sm font-semibold mb-1">Distribución de Calidad Nutricional</h3>
                  <p className="text-xs text-gray-500 mb-3">Histograma poblacional</p>
                  <Plot
                    data={[{
                      x: filtered.map(r => r.nutritionalQualityScore).filter(v => v != null) as number[],
                      type: "histogram",
                      nbinsx: 25,
                      marker: { color: "#22c55e", opacity: 0.75 },
                      name: "Pacientes",
                    }]}
                    layout={{ ...PLOT_LAYOUT_BASE, height: 260, xaxis: { ...AXIS_STYLE, title: { text: "Nutritional Quality Score" } }, yaxis: { ...AXIS_STYLE, title: { text: "Pacientes" } } }}
                    config={{ displayModeBar: false, responsive: true }} style={{ width: "100%" }}
                  />
                </div>

                <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                  <h3 className="text-sm font-semibold mb-1">Distribución de Edades por Grupo de Longevidad</h3>
                  <p className="text-xs text-gray-500 mb-3">Superposición demográfica</p>
                  <Plot
                    data={ageHistTraces}
                    layout={{ ...PLOT_LAYOUT_BASE, height: 260, barmode: "overlay", xaxis: { ...AXIS_STYLE, title: { text: "Edad (años)" } }, yaxis: { ...AXIS_STYLE, title: { text: "Pacientes" } }, legend: { font: { color: "#9ca3af", size: 10 }, orientation: "h", y: -0.28 } }}
                    config={{ displayModeBar: false, responsive: true }} style={{ width: "100%" }}
                  />
                </div>
              </div>

              {/* Data Table Subset for Nutrition */}
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-5">
                  <h3 className="text-sm font-semibold">Muestra de Datos Poblacionales</h3>
                  <button onClick={() => exportCSV(filtered)} className="text-xs px-3 py-1.5 rounded-lg border border-teal-700 text-teal-300 hover:bg-teal-900/30">
                    Exportar CSV
                  </button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-gray-700 text-gray-400 uppercase text-xs">
                        <th className="p-3">SEQN</th>
                        <th className="p-3">Edad</th>
                        <th className="p-3">Género</th>
                        <th className="p-3">Grupo Longevidad</th>
                        <th className="p-3 text-right">Nutritional Quality</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pageRows.map(record => (
                        <tr key={record.seqn} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                          <td className="p-3 font-mono text-gray-300 text-sm">{record.seqn}</td>
                          <td className="p-3 text-gray-300">{record.ageYears}</td>
                          <td className="p-3 text-gray-300">{record.gender}</td>
                          <td className="p-3"><LongevityBadge group={record.longevityGroup} /></td>
                          <td className="p-3"><ScoreBar value={record.nutritionalQualityScore} type="nutrition" /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="flex items-center justify-between mt-5 pt-4 border-t border-gray-700">
                  <span className="text-sm text-gray-400">Página {page + 1} de {totalPages}</span>
                  <div className="flex gap-2">
                    <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} className="px-3 py-1 text-sm border border-gray-600 rounded-lg text-gray-300 hover:bg-gray-700 transition-colors">←</button>
                    <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1} className="px-3 py-1 text-sm border border-gray-600 rounded-lg text-gray-300 hover:bg-gray-700 transition-colors">→</button>
                  </div>
                </div>
              </div>

            </div>
          )}

          {/* ── TAB 2: Riesgo (M2) ─────────────────────────────────────────── */}
          {activeTab === "Riesgo (M2)" && (
            <div className="space-y-6 animate-fade-in-up">
              
              <div className="mb-2 mt-4">
                <h2 className="text-xl font-bold text-orange-400">2. Análisis de Riesgo Cardiovascular</h2>
                <p className="text-sm text-gray-400">Responsable: Martín. En esta etapa observamos las consecuencias epidemiológicas. ¿Cómo impactan los malos hábitos en el riesgo al corazón?</p>
              </div>

              {/* Stat cards Riesgo */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <StatCard label="Riesgo Cardio Promedio" value={avg("cardioRiskScore")} sub="Escala 0–100 (Calculadora)" accent="#f97316" />
                <StatCard label="Pacientes en Riesgo Crítico" value={filterActive ? filtered.filter(r => (r.cardioRiskScore ?? 0) > 80 && (r.nutritionalQualityScore ?? 100) < 40).length : criticalCount} sub="Cardio >80 y Nutrición <40" accent="#ef4444" />
              </div>

              {/* Critical banner */}
              {criticalCount > 0 && (
                <div className="bg-red-950/60 border border-red-700/50 rounded-xl p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-red-400 text-xl">⚠</span>
                    <div>
                      <p className="text-red-300 font-semibold text-sm">{criticalCount} pacientes críticos localizados en el análisis de riesgo.</p>
                      <p className="text-red-500 text-xs">Riesgo cardiovascular severo derivado de deficiencias nutricionales.</p>
                    </div>
                  </div>
                  <button onClick={() => { setShowCritical(v => !v); setFilterGroup("Todos"); setFilterCycle("Todos"); setFilterGender("Todos"); }}
                    className={`text-xs px-4 py-2 rounded-lg border transition-colors ${showCritical ? "bg-red-700 border-red-600 text-white" : "border-red-700 text-red-300 hover:bg-red-900/40"}`}>
                    {showCritical ? "Remover filtro" : "Aislar críticos"}
                  </button>
                </div>
              )}

              {/* Row 1: Cardio Graphs */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                  <h3 className="text-sm font-semibold mb-1">Impacto: Nutrición vs Riesgo Cardiovascular</h3>
                  <p className="text-xs text-gray-500 mb-3">Correlación directa ({scatterSample.length.toLocaleString()} muestras)</p>
                  <Plot
                    data={[{
                      x: scatterSample.map(r => r.nutritionalQualityScore),
                      y: scatterSample.map(r => r.cardioRiskScore),
                      mode: "markers", type: "scatter",
                      marker: {
                        color: scatterSample.map(r => (r.cardioRiskScore ?? 0) > 80 && (r.nutritionalQualityScore ?? 100) < 40 ? "#ef4444" : "#f97316"),
                        size: 5, opacity: 0.6,
                      },
                      text: scatterSample.map(r => `SEQN: ${r.seqn}<br>Edad: ${r.ageYears}`),
                      hovertemplate: "<b>%{text}</b><br>Nutrición: %{x}<br>Cardio: %{y}<extra></extra>",
                    }]}
                    layout={{ ...PLOT_LAYOUT_BASE, xaxis: { ...AXIS_STYLE, title: { text: "Nutritional Quality Score" } }, yaxis: { ...AXIS_STYLE, title: { text: "Cardio Risk Score" } } }}
                    config={{ displayModeBar: false, responsive: true }} style={{ width: "100%" }}
                  />
                </div>

                <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                  <h3 className="text-sm font-semibold mb-1">Severidad del Riesgo por Longevidad</h3>
                  <p className="text-xs text-gray-500 mb-3">Box plot de Riesgo Cardio</p>
                  <Plot
                    data={boxTraces}
                    layout={{ ...PLOT_LAYOUT_BASE, xaxis: { ...AXIS_STYLE }, yaxis: { ...AXIS_STYLE, title: { text: "Cardio Risk Score" }, range: [0, 105] }, showlegend: false }}
                    config={{ displayModeBar: false, responsive: true }} style={{ width: "100%" }}
                  />
                </div>
              </div>

            </div>
          )}

          {/* ── TAB 3: Clínica (M3) ─────────────────────────────────────────── */}
          {activeTab === "Clínica (M3)" && (
            <div className="space-y-6 animate-fade-in-up">
              
              <div className="mb-2 mt-4">
                <h2 className="text-xl font-bold text-purple-400">3. Biomarcadores y Laboratorio (Capa Gold)</h2>
                <p className="text-sm text-gray-400">Responsable: Matías. El interior del paciente. Resultados de exámenes de sangre (Glucosa, Colesterol) que conforman el Índice de Longevidad Clínica.</p>
              </div>

              {loadingM3 ? (
                <div className="flex justify-center items-center h-48">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
                </div>
              ) : member3Data.length === 0 ? (
                <div className="text-center p-6 text-gray-500 border border-gray-700 rounded-xl bg-gray-800">
                  No hay datos clínicos disponibles.
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-gray-800 p-5 rounded-xl border border-gray-700 shadow-lg">
                      <div className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Índice de Riesgo Clínico</div>
                      <div className="text-3xl font-bold text-purple-400 mt-2">
                        {(member3Data.reduce((acc, r) => acc + (r.longevity_risk_index ?? r.longevityRiskIndex ?? 0), 0) / member3Data.length).toFixed(2)}%
                      </div>
                      <div className="text-xs text-gray-500 mt-2">Medida compuesta de 8 biomarcadores NHANES</div>
                    </div>
                    <div className="bg-gray-800 p-5 rounded-xl border border-gray-700 shadow-lg">
                      <div className="text-xs text-gray-400 uppercase tracking-wider font-semibold">HbA1c Promedio</div>
                      <div className="text-3xl font-bold text-teal-400 mt-2">
                        {(member3Data.reduce((acc, r) => acc + (r.LBXGH ?? r.lbxgh ?? 0), 0) / member3Data.length).toFixed(2)}%
                      </div>
                      <div className="text-xs text-gray-500 mt-2">Hemoglobina glicosilada promedio en sangre</div>
                    </div>
                    <div className="bg-gray-800 p-5 rounded-xl border border-gray-700 shadow-lg">
                      <div className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Colesterol Total Promedio</div>
                      <div className="text-3xl font-bold text-blue-400 mt-2">
                        {(member3Data.reduce((acc, r) => acc + (r.LBXSCH ?? r.lbxsch ?? 0), 0) / member3Data.length).toFixed(2)} mg/dL
                      </div>
                      <div className="text-xs text-gray-500 mt-2">Nivel de lípidos global de la muestra</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-gray-800 p-5 rounded-xl border border-gray-700">
                      <h3 className="text-sm font-semibold mb-3 text-gray-300">Tiers de Riesgo Biológico</h3>
                      <Plot
                        data={[{
                            type: 'bar',
                            x: ['Bajo', 'Moderado', 'Alto', 'Crítico'],
                            y: [
                              member3Data.filter(r => (r.risk_tier ?? r.riskTier) === 'Low').length,
                              member3Data.filter(r => (r.risk_tier ?? r.riskTier) === 'Moderate').length,
                              member3Data.filter(r => (r.risk_tier ?? r.riskTier) === 'High').length,
                              member3Data.filter(r => (r.risk_tier ?? r.riskTier) === 'Critical').length
                            ],
                            marker: { color: ['#2dd4bf', '#3b82f6', '#a855f7', '#ef4444'] }
                        }]}
                        layout={{ ...PLOT_LAYOUT_BASE, xaxis: { ...AXIS_STYLE }, yaxis: { ...AXIS_STYLE, title: {text: "Pacientes"} } }}
                        config={{ displayModeBar: false }} style={{ width: "100%" }}
                      />
                    </div>

                    <div className="bg-gray-800 p-5 rounded-xl border border-gray-700">
                      <h3 className="text-sm font-semibold mb-3 text-gray-300">Glucosa vs. Índice de Riesgo Metabólico</h3>
                      <Plot
                        data={[{
                            x: member3Data.map(r => r.LBXGH ?? r.lbxgh),
                            y: member3Data.map(r => r.longevity_risk_index ?? r.longevityRiskIndex),
                            mode: 'markers', type: 'scatter',
                            marker: { color: '#a855f7', size: 6, opacity: 0.7 }
                        }]}
                        layout={{ ...PLOT_LAYOUT_BASE, xaxis: { ...AXIS_STYLE, title: { text: 'HbA1c (%)' } }, yaxis: { ...AXIS_STYLE, title: { text: 'Índice de Riesgo (%)' } } }}
                        config={{ displayModeBar: false }} style={{ width: "100%" }}
                      />
                    </div>
                  </div>
                </>
              )}

            </div>
          )}

          {/* ── TAB 4: Simulador ML ─────────────────────────────────────────── */}
          {activeTab === "Simulador ML" && (
            <div className="animate-fade-in-up mt-4">
              
              <div className="mb-6 max-w-4xl mx-auto">
                <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-teal-400">
                  4. Predicción Asistida por Inteligencia Artificial
                </h2>
                <p className="text-sm text-gray-400 mt-2">
                  La integración final. El modelo <strong>TPOT AutoML</strong> entrenado con Kedro cruza los hábitos alimenticios (M1), los riesgos demográficos (M2) y los biomarcadores clínicos (M3) para generar una inferencia en tiempo real.
                </p>
              </div>

              <div className="bg-gray-800 rounded-xl p-8 border border-gray-700 shadow-2xl max-w-4xl mx-auto">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                  
                  {/* Controles Clínicos Virtuales */}
                  <div className="space-y-6">
                    <h3 className="text-sm uppercase tracking-widest text-teal-500 font-bold mb-4">Inputs del Paciente</h3>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Edad Biológica: {simAge} años</label>
                      <input type="range" min="20" max="85" value={simAge} onChange={e => setSimAge(Number(e.target.value))} 
                             className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-teal-500" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Calidad de la Dieta (HEI): {simNutrition}/100</label>
                      <input type="range" min="0" max="100" value={simNutrition} onChange={e => setSimNutrition(Number(e.target.value))} 
                             className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-green-500" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">BMI (Índice de Masa Corporal): {simBmi}</label>
                      <input type="range" min="15" max="50" value={simBmi} onChange={e => setSimBmi(Number(e.target.value))} 
                             className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-orange-500" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Glucosa en Sangre: {simGlucose} mg/dL</label>
                      <input type="range" min="60" max="250" value={simGlucose} onChange={e => setSimGlucose(Number(e.target.value))} 
                             className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Género</label>
                      <div className="flex gap-4">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input type="radio" name="simGender" value="Hombre" checked={simGender === "Hombre"} onChange={e => setSimGender(e.target.value)} className="text-teal-500 focus:ring-teal-500" />
                          <span className="text-gray-300">Hombre</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input type="radio" name="simGender" value="Mujer" checked={simGender === "Mujer"} onChange={e => setSimGender(e.target.value)} className="text-teal-500 focus:ring-teal-500" />
                          <span className="text-gray-300">Mujer</span>
                        </label>
                      </div>
                    </div>
                    <button onClick={handleSimulate} disabled={simLoading}
                      className="w-full bg-gradient-to-r from-purple-600 to-teal-500 hover:from-purple-500 hover:to-teal-400 text-white font-bold py-4 px-4 rounded-xl shadow-[0_0_20px_rgba(45,212,191,0.2)] transform transition active:scale-95 disabled:opacity-50 mt-4">
                      {simLoading ? "Procesando predicción AutoML..." : "Ejecutar Inferencia Combinada"}
                    </button>
                  </div>

                  {/* Resultados AutoML */}
                  <div className="bg-gray-900 rounded-xl p-6 border border-gray-700 flex flex-col justify-center items-center text-center shadow-inner relative overflow-hidden">
                    {/* Background glow */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-teal-500/10 blur-[60px] rounded-full pointer-events-none"></div>

                    {simResult ? (
                      simResult.error ? (
                        <p className="text-red-400">Error en el modelo: {simResult.error}</p>
                      ) : (
                        <div className="w-full animate-fade-in-up relative z-10">
                          <p className="text-teal-400 text-sm uppercase tracking-widest mb-2 font-semibold">Puntaje de Longevidad Proyectado</p>
                          <div className="text-7xl font-black mb-4 drop-shadow-lg" style={{ color: `hsl(${simResult.healthyAgingScore * 1.2}, 70%, 50%)` }}>
                            {simResult.healthyAgingScore.toFixed(1)}
                          </div>
                          
                          <div className="w-full bg-gray-800 rounded-full h-3 mb-6 overflow-hidden">
                            <div className="h-3 transition-all duration-1000 ease-out rounded-full" 
                                 style={{ width: `${simResult.healthyAgingScore}%`, backgroundColor: `hsl(${simResult.healthyAgingScore * 1.2}, 70%, 50%)` }}></div>
                          </div>

                          <div className="grid grid-cols-2 gap-4 mt-8">
                            <div className="bg-gray-800/80 p-4 rounded-xl border border-gray-700/50">
                              <p className="text-xs text-gray-500 uppercase font-semibold">Riesgo Cardio Base</p>
                              <p className="text-2xl font-bold text-red-400 mt-1">{simResult.cardioRiskScore.toFixed(1)}%</p>
                            </div>
                            <div className="bg-gray-800/80 p-4 rounded-xl border border-gray-700/50">
                              <p className="text-xs text-gray-500 uppercase font-semibold">Motor ML</p>
                              <p className="text-xs font-mono text-purple-400 mt-2 bg-purple-900/30 py-1 px-2 rounded">{simResult.model_type}</p>
                            </div>
                          </div>
                        </div>
                      )
                    ) : (
                      <div className="text-gray-500 relative z-10">
                        <svg className="w-20 h-20 mx-auto mb-4 opacity-30 text-teal-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
                        <p className="text-sm">Ajusta los controles metabólicos a la izquierda para ejecutar una inferencia en vivo contra el modelo Kedro.</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

        </>)}
      </div>
    </main>
  );
}