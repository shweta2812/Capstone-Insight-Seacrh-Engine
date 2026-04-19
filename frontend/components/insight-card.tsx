import { cn } from "@/lib/utils";

const TAG_STYLES: Record<string, string> = {
  Strategy:   "bg-blue-500/15 text-blue-400 border-blue-500/20",
  Financial:  "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
  Product:    "bg-amber-500/15 text-amber-400 border-amber-500/20",
  Market:     "bg-red-500/15 text-red-400 border-red-500/20",
  Technology: "bg-teal-500/15 text-teal-400 border-teal-500/20",
  Insight:    "bg-purple-500/15 text-purple-400 border-purple-500/20",
};

interface InsightCardProps {
  tag: string;
  body: string;
  company?: string;
  period?: string;
}

export function InsightCard({ tag, body, company, period }: InsightCardProps) {
  const style = TAG_STYLES[tag] ?? TAG_STYLES.Insight;
  return (
    <div className="bg-white border border-border rounded-xl p-4 shadow-sm border-l-[3px] border-l-primary">
      <div className="flex items-start gap-3">
        <span className={cn("inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase shrink-0 mt-0.5", style)}>
          {tag}
        </span>
        <p className="text-sm text-foreground/85 leading-relaxed">{body}</p>
      </div>
      {(company || period) && (
        <p className="text-[11px] text-muted-foreground mt-2 ml-0">
          {company} {period && `· ${period}`}
        </p>
      )}
    </div>
  );
}
