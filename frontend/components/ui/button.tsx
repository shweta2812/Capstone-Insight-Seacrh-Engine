import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "ghost" | "outline" | "destructive";
  size?: "sm" | "md" | "icon";
}

export function Button({ variant = "default", size = "md", className, children, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-1.5 font-medium rounded-md transition-colors focus:outline-none disabled:opacity-50 disabled:pointer-events-none",
        variant === "default"     && "bg-primary text-primary-foreground hover:bg-primary/90",
        variant === "ghost"       && "text-muted-foreground hover:text-foreground hover:bg-secondary",
        variant === "outline"     && "border border-border text-foreground hover:bg-secondary",
        variant === "destructive" && "bg-red-600 text-white hover:bg-red-700",
        size === "sm"   && "text-xs px-3 py-1.5",
        size === "md"   && "text-sm px-4 py-2",
        size === "icon" && "w-8 h-8 p-0",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
