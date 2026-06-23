import { PlotlyWrapper } from "@/components/charts/PlotlyWrapper";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { Users, HeartPulse, ActivitySquare, AlertTriangle } from "lucide-react";

export default function DashboardPage() {
  // Mock data for the charts
  const ageDistributionData = [
    {
      x: ["18-30", "31-45", "46-60", "61-75", "76+"],
      y: [1200, 2300, 2800, 1900, 800],
      type: "bar",
      marker: {
        color: ["#0ea5e9", "#0284c7", "#0d9488", "#10b981", "#34d399"],
        opacity: 0.8
      }
    }
  ];

  const metabolicCorrelationData = [
    {
      x: [120, 135, 140, 110, 150, 130, 145, 125, 160, 115], // Presión sistólica
      y: [90, 105, 110, 85, 120, 100, 115, 95, 130, 88], // Glucosa
      mode: "markers",
      type: "scatter",
      marker: {
        size: 12,
        color: "#14b8a6",
        line: {
          color: "#ffffff",
          width: 1
        }
      }
    }
  ];

  const layoutBar = {
    title: { text: "Distribución de Edades en la Muestra", font: { color: "#f8fafc" } },
    xaxis: { tickfont: { color: "#94a3b8" }, gridcolor: "#334155" },
    yaxis: { tickfont: { color: "#94a3b8" }, gridcolor: "#334155" },
  };

  const layoutScatter = {
    title: { text: "Presión Sistólica vs. Glucosa", font: { color: "#f8fafc" } },
    xaxis: { title: "Presión Sistólica (mmHg)", tickfont: { color: "#94a3b8" }, gridcolor: "#334155" },
    yaxis: { title: "Glucosa en ayuno (mg/dL)", tickfont: { color: "#94a3b8" }, gridcolor: "#334155" },
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Resumen Ejecutivo</h1>
          <p className="text-foreground/60 mt-1">
            Indicadores principales de longevidad del ciclo 2017-2018.
          </p>
        </div>
        <div className="flex gap-2">
          <select className="bg-card text-sm border border-border rounded-lg px-4 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary">
            <option>Ciclo: 2017-2018</option>
            <option>Ciclo: 2015-2016</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KpiCard
          title="Tamaño de Muestra"
          value="9,254"
          subtitle="Pacientes procesados"
          icon={Users}
          trend="up"
          trendValue="+12%"
        />
        <KpiCard
          title="Salud Metabólica"
          value="68%"
          subtitle="Dentro del rango óptimo"
          icon={HeartPulse}
          trend="neutral"
          trendValue="0%"
        />
        <KpiCard
          title="Score de Envejecimiento"
          value="7.2/10"
          subtitle="Promedio global"
          icon={ActivitySquare}
          trend="up"
          trendValue="+0.4"
        />
        <KpiCard
          title="Riesgo Cardiovascular"
          value="14%"
          subtitle="Población en riesgo alto"
          icon={AlertTriangle}
          trend="down"
          trendValue="-2%"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass p-6 rounded-2xl h-[400px]">
          <PlotlyWrapper data={ageDistributionData} layout={layoutBar} />
        </div>
        <div className="glass p-6 rounded-2xl h-[400px]">
          <PlotlyWrapper data={metabolicCorrelationData} layout={layoutScatter} />
        </div>
      </div>
    </div>
  );
}
