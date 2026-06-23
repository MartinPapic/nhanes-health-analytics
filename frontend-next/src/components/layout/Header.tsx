import { Bell, Search, UserCircle } from "lucide-react";

export function Header() {
  return (
    <header className="h-16 border-b border-border bg-card/50 backdrop-blur-md flex items-center justify-between px-6 z-10">
      <div className="flex-1 max-w-xl relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-foreground/40">
          <Search size={18} />
        </div>
        <input
          type="text"
          placeholder="Buscar variables, pacientes o secciones..."
          className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
        />
      </div>

      <div className="flex items-center gap-4">
        <button className="p-2 text-foreground/60 hover:text-foreground hover:bg-foreground/5 rounded-full transition-all relative">
          <Bell size={20} />
          <span className="absolute top-2 right-2 w-2 h-2 bg-accent rounded-full"></span>
        </button>
        <div className="h-8 w-px bg-border mx-2"></div>
        <div className="flex items-center gap-3 cursor-pointer group">
          <div className="text-right hidden md:block">
            <p className="text-sm font-medium text-foreground group-hover:text-primary transition-colors">Dr. Analista</p>
            <p className="text-xs text-foreground/60">Investigador Jefe</p>
          </div>
          <UserCircle size={32} className="text-foreground/80 group-hover:text-primary transition-colors" />
        </div>
      </div>
    </header>
  );
}
