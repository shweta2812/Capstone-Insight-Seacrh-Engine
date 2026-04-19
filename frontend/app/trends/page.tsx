"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/header";
import { TrendChart } from "@/components/charts/trend-chart";
import { SimpleBarChart } from "@/components/charts/bar-chart";
import { COMPANY_COLORS, TOPIC_LIST, type TrendPoint } from "@/lib/types";
import { cn } from "@/lib/utils";

const COMPANIES = ["Elevance Health", "UnitedHealth Group", "Aetna (CVS Health)"];

export default function TrendsPage() {
  const [topic, setTopic] = useState("Medicare");
  const [selectedCos, setSelectedCos] = useState(new Set(COMPANIES));
  const [data, setData] = useState<TrendPoint[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    const q = new URLSearchParams({ topic });
    [...selectedCos].forEach(c => q.append("companies", c));
    fetch(`/api/trends?${q}`)
      .then(r => r.json())
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [topic, selectedCos]);

  const toggleCo = (c: string) => {
    setSelectedCos(prev => {
      const next = new Set(prev);
      next.has(c) ? next.delete(c) : next.add(c);
      return next;
    });
  };

  const lines = [...selectedCos].map(c => ({
    key: c,
    label: c.split(" ")[0],
    color: COMPANY_COLORS[c] ?? "#888",
    yAxisId: "left" as const,
  }));

  // Bar: total mentions by company for selected topic
  const totalBar = [...selectedCos].map(c => ({
    label: c.split(" ")[0],
    value: data.reduce((s, d) => s + ((d[c] as number) ?? 0), 0),
    color: COMPANY_COLORS[c],
  }));

  return (
    <div className="flex flex-col flex-1 overflow-auto">
      <Header title="Trends" subtitle="Topic mention frequency across competitors over time" />
      <div className="flex-1 p-6 space-y-5">

        {/* Controls */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex flex-wrap gap-1.5">
            {TOPIC_LIST.map(t => (
              <button
                key={t}
                onClick={() => setTopic(t)}
                className={cn(
                  "text-xs px-3 py-1.5 rounded-md border transition-colors",
                  topic === t
                    ? "bg-primary/20 border-primary/40 text-primary"
                    : "border-border text-muted-foreground hover:border-primary/30 hover:text-foreground"
                )}
              >
                {t}
              </button>
            ))}
          </div>
          <div className="flex-1" />
          <div className="flex gap-2">
            {COMPANIES.map(c => (
              <button
                key={c}
                onClick={() => toggleCo(c)}
                className={cn(
                  "text-xs px-3 py-1.5 rounded-md border transition-colors",
                  selectedCos.has(c)
                    ? "border-2 font-medium"
                    : "border-border text-muted-foreground opacity-50"
                )}
                style={selectedCos.has(c) ? { borderColor: COMPANY_COLORS[c], color: COMPANY_COLORS[c] } : {}}
              >
                {c.split(" ")[0]}
              </button>
            ))}
          </div>
        </div>

        {/* Main trend chart */}
        <div className="bg-card border border-border rounded-lg p-4">
          <p className="text-xs font-medium text-muted-foreground mb-4">
            "{topic}" Mention Frequency Over Time
          </p>
          <div className="h-64">
            {loading
              ? <div className="h-full flex items-center justify-center text-xs text-muted-foreground">Loading…</div>
              : data.length > 0
                ? <TrendChart data={data} lines={lines} xKey="period" />
                : <div className="h-full flex items-center justify-center text-xs text-muted-foreground">No data — run ingest script first</div>
            }
          </div>
        </div>

        {/* Totals */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-card border border-border rounded-lg p-4">
            <p className="text-xs font-medium text-muted-foreground mb-4">Total "{topic}" Mentions by Competitor</p>
            <div className="h-36">
              <SimpleBarChart data={totalBar} valueFormatter={v => `${v}x`} />
            </div>
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <p className="text-xs font-medium text-muted-foreground mb-3">Topic Reference</p>
            <div className="space-y-1.5">
              {TOPIC_LIST.map(t => (
                <button
                  key={t}
                  onClick={() => setTopic(t)}
                  className={cn(
                    "w-full text-left text-xs px-3 py-2 rounded-md transition-colors",
                    topic === t ? "bg-primary/15 text-primary" : "text-muted-foreground hover:bg-secondary/50"
                  )}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
