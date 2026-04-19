"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/header";
import { StatCard } from "@/components/stat-card";
import { SimpleBarChart } from "@/components/charts/bar-chart";
import { COMPANY_COLORS, type StatsResponse } from "@/lib/types";

const MOCK_STATS: StatsResponse = {
  total_documents: 71,
  total_chunks: 0,
  companies: ["Elevance Health", "UnitedHealth Group", "Aetna (CVS Health)"],
  years: [2020, 2021, 2022, 2023, 2024, 2025],
  company_doc_counts: { "Elevance Health": 23, "UnitedHealth Group": 24, "Aetna (CVS Health)": 24 },
};

export default function OverviewPage() {
  const [stats, setStats] = useState<StatsResponse>(MOCK_STATS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/stats")
      .then(r => r.json())
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const docData = Object.entries(stats.company_doc_counts).map(([company, count]) => ({
    label: company.split(" ")[0],
    value: count,
    color: COMPANY_COLORS[company] ?? "#2563eb",
  }));

  const yearData = stats.years.map(y => ({ label: String(y), value: 4 }));

  return (
    <div className="flex flex-col flex-1 overflow-auto">
      <Header title="Overview" subtitle="Competitive Intelligence · All competitors · 2020–2025" />
      <div className="flex-1 p-6 space-y-6">

        {/* KPI row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Total Documents" value={loading ? "…" : stats.total_documents.toString()} sub="Earnings call transcripts" />
          <StatCard label="Competitors Tracked" value={stats.companies.length.toString()} sub="Elevance · United · Aetna" />
          <StatCard label="Vector Chunks" value={loading ? "…" : stats.total_chunks > 0 ? stats.total_chunks.toLocaleString() : "Not indexed"} sub="Run ingest script first" />
          <StatCard label="Coverage" value={stats.years.length > 0 ? `${Math.min(...stats.years)}–${Math.max(...stats.years)}` : "N/A"} sub={`${stats.years.length} years`} />
        </div>

        {/* Charts row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 bg-card border border-border rounded-lg p-4">
            <p className="text-xs font-medium text-muted-foreground mb-4">Documents by Competitor</p>
            <div className="h-48">
              <SimpleBarChart data={docData} valueFormatter={v => `${v} docs`} />
            </div>
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <p className="text-xs font-medium text-muted-foreground mb-4">Coverage by Year</p>
            <div className="h-48">
              <SimpleBarChart data={yearData} color="#2563eb" valueFormatter={v => `${v}Q`} />
            </div>
          </div>
        </div>

        {/* Coverage table */}
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-border">
            <p className="text-xs font-medium text-muted-foreground">Data Coverage</p>
          </div>
          <div className="divide-y divide-border">
            {stats.companies.map(company => (
              <div key={company} className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full" style={{ background: COMPANY_COLORS[company] ?? "#888" }} />
                  <span className="text-sm text-foreground">{company}</span>
                </div>
                <div className="flex items-center gap-6 text-xs text-muted-foreground">
                  <span>{stats.company_doc_counts[company] ?? 0} docs</span>
                  <span>2020–2025</span>
                  <span>Earnings Calls</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Getting started */}
        <div className="bg-card border border-border rounded-lg p-4">
          <p className="text-xs font-medium text-muted-foreground mb-3">Getting Started</p>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
            {[
              { step: "1", title: "Index Documents", desc: "Run: python scripts/ingest_and_index.py", done: stats.total_chunks > 0 },
              { step: "2", title: "Add API Key", desc: "Set ANTHROPIC_API_KEY in backend/.env", done: false },
              { step: "3", title: "Ask Questions", desc: "Go to Ask / Search to query the engine", done: false },
            ].map(item => (
              <div key={item.step} className="flex items-start gap-3 p-3 rounded-md bg-secondary/30">
                <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5 ${item.done ? "bg-emerald-500/20 text-emerald-400" : "bg-primary/20 text-primary"}`}>
                  {item.done ? "✓" : item.step}
                </div>
                <div>
                  <p className="text-xs font-medium text-foreground">{item.title}</p>
                  <p className="text-[11px] text-muted-foreground mt-0.5">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
