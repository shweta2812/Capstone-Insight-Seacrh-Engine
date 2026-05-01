"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  LayoutDashboard,
  Building2,
  Lightbulb,
  TrendingUp,
  FileText,
  Globe,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/",          label: "Overview",     icon: LayoutDashboard },
  { href: "/companies", label: "Companies",    icon: Building2 },
  { href: "/insights",  label: "Insights",     icon: Lightbulb },
  { href: "/trends",    label: "Trends",       icon: TrendingUp },
  { href: "/documents", label: "Documents",    icon: FileText },
  { href: "/sources",   label: "Data Sources", icon: Globe },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "flex flex-col h-screen bg-sidebar border-r border-sidebar-border transition-all duration-200 shrink-0",
        collapsed ? "w-[60px]" : "w-[220px]"
      )}
    >
      <div className={cn(
        "flex items-center h-14 px-4 border-b border-sidebar-border shrink-0",
        collapsed && "justify-center px-0"
      )}>
        {!collapsed && (
          <div>
            <span className="text-sm font-semibold text-white tracking-tight">
              <span className="text-blue-200">CI</span> Insights Engine
            </span>
            <p className="text-[10px] text-white/50 mt-0.5">Blue Shield of California</p>
          </div>
        )}
        {collapsed && <span className="text-blue-200 font-bold text-base">CI</span>}
      </div>

      <nav className="flex-1 py-3 overflow-y-auto">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 mx-2 px-3 py-2 rounded-md text-sm transition-colors mb-0.5",
                active
                  ? "bg-white/20 text-white font-medium"
                  : "text-white/70 hover:bg-white/10 hover:text-white",
                collapsed && "justify-center px-0 mx-2"
              )}
              title={collapsed ? label : undefined}
            >
              <Icon size={16} className={cn("shrink-0", active && "text-white")} />
              {!collapsed && <span>{label}</span>}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-sidebar-border p-2">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center w-full h-8 rounded-md text-white/40 hover:text-white hover:bg-white/10 transition-colors"
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>
    </aside>
  );
}
