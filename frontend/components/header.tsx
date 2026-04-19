"use client";

import { Bell, RefreshCw } from "lucide-react";

interface HeaderProps {
  title: string;
  subtitle?: string;
  onRefresh?: () => void;
}

export function Header({ title, subtitle, onRefresh }: HeaderProps) {
  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-border bg-white shrink-0 shadow-sm">
      <div>
        <h1 className="text-sm font-semibold text-foreground">{title}</h1>
        {subtitle && <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground bg-secondary px-2 py-1 rounded-md">
          Elevance · United · Aetna · 2020–2025
        </span>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
          >
            <RefreshCw size={14} />
          </button>
        )}
        <button className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
          <Bell size={14} />
        </button>
      </div>
    </header>
  );
}
