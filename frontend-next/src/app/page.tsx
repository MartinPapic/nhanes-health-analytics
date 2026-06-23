"use client";

import { useEffect, useState } from "react";

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

export default function Home() {
  const [data, setData] = useState<LongevityRecord[]>([]);
  const [loading, setLoading] = useState(true);

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
                    <th className="p-3 text-right">Cardio Risk Score</th>
                    <th className="p-3 text-right">Nutritional Quality</th>
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
                      <td className="p-3 text-right font-semibold text-rose-400">
                        {record.cardioRiskScore !== undefined && record.cardioRiskScore !== null ? record.cardioRiskScore : "-"}
                      </td>
                      <td className="p-3 text-right font-semibold text-green-400">
                        {record.nutritionalQualityScore !== undefined && record.nutritionalQualityScore !== null ? record.nutritionalQualityScore : "-"}
                      </td>
                    </tr>
                  ))}
                  {data.length === 0 && (
                    <tr>
                      <td colSpan={8} className="p-6 text-center text-gray-500">
                        No hay datos disponibles. Verifica que el backend esté conectado a PostgreSQL.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
