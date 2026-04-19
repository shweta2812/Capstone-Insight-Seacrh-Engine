import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "secondary" | "outline" | "success" | "warning";
  className?: string;
}

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span className={cn(
      "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium border",
      variant === "default"   && "bg-primary/15 text-primary border-primary/20",
      variant === "secondary" && "bg-secondary text-secondary-foreground border-border",
      variant === "outline"   && "bg-transparent text-muted-foreground border-border",
      variant === "success"   && "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
      variant === "warning"   && "bg-amber-500/15 text-amber-400 border-amber-500/20",
      className
    )}>
      {children}
    </span>
  );
}
