import { cn } from "@/lib/utils";

export function Card({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("bg-card border border-border rounded-xl", className)} {...props}>
      {children}
    </div>
  );
}
