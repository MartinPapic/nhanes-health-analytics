"use client";

import { Activity, LayoutDashboard, Database, ActivitySquare, Settings, LogOut } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  { name: "Resumen Ejecutivo", href: "/dashboard", icon: LayoutDashboard },
  { name: "Análisis Clínico", href: "/dashboard/clinical", icon: ActivitySquare },
  { name: "Explorador de Datos", href: "/dashboard/explorer", icon: Database },
  { name: "Configuración", href: "/dashboard/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex flex-col w-64 bg-card border-r border-border h-full">
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 bg-primary/10 text-primary rounded-lg flex items-center justify-center ring-1 ring-primary/30">
          <Activity size={20} />
        </div>
        <span className="font-bold text-foreground tracking-tight">NHANES Analytics</span>
      </div>

      <nav className="flex-1 px-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
                  : "text-foreground/70 hover:bg-foreground/5 hover:text-foreground"
              }`}
            >
              <Icon size={18} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-border">
        <Link
          href="/login"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-foreground/70 hover:bg-destructive/10 hover:text-destructive transition-all"
        >
          <LogOut size={18} />
          Cerrar Sesión
        </Link>
      </div>
    </div>
  );
}
