import { LucideIcon } from "lucide-react";

interface KpiCardProps {
  title: string;
  value: string;
  subtitle: string;
  icon: LucideIcon;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
}

export function KpiCard({ title, value, subtitle, icon: Icon, trend, trendValue }: KpiCardProps) {
  return (
    <div className="glass p-6 rounded-2xl flex flex-col hover:border-primary/30 transition-colors group relative overflow-hidden">
      {/* Decorative gradient */}
      <div className="absolute -right-10 -top-10 w-32 h-32 bg-primary/5 rounded-full blur-2xl group-hover:bg-primary/10 transition-colors pointer-events-none" />
      
      <div className="flex justify-between items-start mb-4 relative z-10">
        <div>
          <p className="text-sm font-medium text-foreground/70 mb-1">{title}</p>
          <h3 className="text-3xl font-bold text-foreground tracking-tight">{value}</h3>
        </div>
        <div className="p-3 bg-primary/10 text-primary rounded-xl ring-1 ring-primary/20 group-hover:ring-primary/40 transition-all">
          <Icon size={24} />
        </div>
      </div>
      
      <div className="flex items-center gap-2 mt-auto relative z-10">
        {trend && (
          <span
            className={`text-xs font-semibold px-2 py-1 rounded-full ${
              trend === "up"
                ? "bg-emerald-500/10 text-emerald-500"
                : trend === "down"
                ? "bg-rose-500/10 text-rose-500"
                : "bg-foreground/10 text-foreground/70"
            }`}
          >
            {trend === "up" ? "↑" : trend === "down" ? "↓" : "−"} {trendValue}
          </span>
        )}
        <span className="text-xs text-foreground/50">{subtitle}</span>
      </div>
    </div>
  );
}
