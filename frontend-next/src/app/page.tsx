"use client";

import { useEffect, useState } from "react";
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
}

export default function Home() {
  const [data, setData] = useState<LongevityRecord[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Member 3 states
  const [member3Data, setMember3Data] = useState<any[]>([]);
  const [loadingM3, setLoadingM3] = useState(true);

  useEffect(() => {
    fetch('/api/v1/analytics')
      .then((res) => res.json())
      .then((json) => {
        // Spring Data JPA Paging returns { content: [...] }
        setData(json.content || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching data", err);
        setLoading(false);
      });

    // Fetch Member 3 laboratory gold data
    fetch('/api/v1/analytics/member3')
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

  return (
    <main className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-blue-500">
          NHANES Longevity Dashboard
        </h1>

        <div className="bg-gray-800 rounded-xl p-6 shadow-2xl border border-gray-700">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">Capa Gold - Datos Procesados</h2>
            <div className="text-sm text-gray-400">
              {loading ? "Conectando al Backend..." : `${data.length} registros (Página 1)`}
            </div>
          </div>

          {loading ? (
            <div className="flex justify-center items-center h-48">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500"></div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-gray-700 text-gray-400 uppercase text-xs">
                    <th className="p-3">SEQN</th>
                    <th className="p-3">Ciclo</th>
                    <th className="p-3">Edad</th>
                    <th className="p-3">Género</th>
                    <th className="p-3">Grupo Longevidad</th>
                    <th className="p-3 text-right">Healthy Aging Score</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((record) => (
                    <tr key={record.seqn} className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors">
                      <td className="p-3 font-mono text-gray-300">{record.seqn}</td>
                      <td className="p-3 text-sm">{record.surveyCycle}</td>
                      <td className="p-3">{record.ageYears}</td>
                      <td className="p-3">{record.gender}</td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          record.longevityGroup.includes('Extrema') ? 'bg-purple-900/50 text-purple-300 border border-purple-700/50' :
                          record.longevityGroup.includes('Alta') ? 'bg-teal-900/50 text-teal-300 border border-teal-700/50' :
                          'bg-blue-900/50 text-blue-300 border border-blue-700/50'
                        }`}>
                          {record.longevityGroup}
                        </span>
                      </td>
                      <td className="p-3 text-right font-semibold text-teal-400">
                        {record.healthyAgingScore}
                      </td>
                    </tr>
                  ))}
                  {data.length === 0 && (
                    <tr>
                      <td colSpan={6} className="p-6 text-center text-gray-500">
                        No hay datos disponibles. Verifica que el backend esté conectado a PostgreSQL.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Sección Miembro 3 - Matías Retamal (Clínicos y Longevidad) */}
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
                    {(member3Data.reduce((acc, r) => acc + (r.LBXTC ?? r.lbxtc ?? 0), 0) / member3Data.length).toFixed(2)} mg/dL
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
      </div>
    </main>
  );
}
