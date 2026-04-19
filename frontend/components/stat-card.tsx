import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string;
  sub?: string;
  trend?: number;
  className?: string;
}

export function StatCard({ label, value, sub, trend, className }: StatCardProps) {
  return (
    <div className={cn("bg-white border border-border rounded-xl p-5 shadow-sm", className)}>
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className="text-2xl font-semibold text-foreground tracking-tight">{value}</p>
      {(sub || trend !== undefined) && (
        <div className="flex items-center gap-2 mt-1.5">
          {trend !== undefined && (
            <span className={cn("text-xs font-medium", trend >= 0 ? "text-emerald-400" : "text-red-400")}>
              {trend >= 0 ? "▲" : "▼"} {Math.abs(trend)}%
            </span>
          )}
          {sub && <span className="text-xs text-muted-foreground">{sub}</span>}
        </div>
      )}
    </div>
  );
}
