"use client";

import { useState } from "react";
import { Header } from "@/components/header";
import { InsightCard } from "@/components/insight-card";
import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

const COMPANIES = ["Elevance Health", "UnitedHealth Group", "Aetna (CVS Health)"];
const YEARS = [2025, 2024, 2023, 2022, 2021, 2020];
const QUARTERS = ["Q1", "Q2", "Q3", "Q4"];

const TAG_RE = /\[(\w+)\]\s*/;

function parseBullets(text: string) {
  return text
    .split("\n")
    .filter(l => l.trim().match(/^[•\-*]/))
    .map(l => {
      const clean = l.replace(/^[•\-*]\s*/, "");
      const m = clean.match(TAG_RE);
      return { tag: m ? m[1] : "Insight", body: clean.replace(TAG_RE, "").trim() };
    });
}

export default function InsightsPage() {
  const [company, setCompany] = useState(COMPANIES[0]);
  const [year, setYear] = useState(2024);
  const [quarter, setQuarter] = useState("Q3");
  const [insights, setInsights] = useState<{ tag: string; body: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const generate = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/insights", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company, year, quarter }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setInsights(parseBullets(data.insights));
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col flex-1 overflow-auto">
      <Header title="Insights" subtitle="AI-generated competitive intelligence from earnings calls" />
      <div className="flex-1 p-6 space-y-5">

        {/* Selectors */}
        <div className="flex items-center gap-3 flex-wrap">
          {COMPANIES.map(c => (
            <button
              key={c}
              onClick={() => setCompany(c)}
              className={cn(
                "text-xs px-3 py-1.5 rounded-md border transition-colors",
                company === c
                  ? "bg-primary/20 border-primary/40 text-primary"
                  : "border-border text-muted-foreground hover:border-primary/30 hover:text-foreground"
              )}
            >
              {c.split(" ")[0]}
            </button>
          ))}
          <div className="flex-1" />
          <select
            value={year}
            onChange={e => setYear(Number(e.target.value))}
            className="text-xs px-2 py-1.5 rounded-md border border-border bg-secondary text-muted-foreground"
          >
            {YEARS.map(y => <option key={y}>{y}</option>)}
          </select>
          <select
            value={quarter}
            onChange={e => setQuarter(e.target.value)}
            className="text-xs px-2 py-1.5 rounded-md border border-border bg-secondary text-muted-foreground"
          >
            {QUARTERS.map(q => <option key={q}>{q}</option>)}
          </select>
          <button
            onClick={generate}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-1.5 rounded-md bg-primary text-primary-foreground text-xs font-medium hover:bg-primary/80 disabled:opacity-50 transition-colors"
          >
            <Sparkles size={13} />
            {loading ? "Generating…" : "Generate Insights"}
          </button>
        </div>

        {/* Selected doc info */}
        <div className="bg-card border border-border rounded-lg px-4 py-3 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-foreground">{company}</p>
            <p className="text-xs text-muted-foreground">{year} {quarter} · Earnings Call Transcript</p>
          </div>
          <span className="text-[11px] text-muted-foreground bg-secondary px-2 py-1 rounded">Earnings Call</span>
        </div>

        {error && <p className="text-xs text-red-400">{error}</p>}

        {/* Insights list */}
        {insights.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">
              {insights.length} insights extracted · {company} {year} {quarter}
            </p>
            {insights.map((item, i) => (
              <InsightCard key={i} tag={item.tag} body={item.body} />
            ))}
          </div>
        )}

        {!loading && insights.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Sparkles size={32} className="text-muted-foreground/30 mb-3" />
            <p className="text-sm text-muted-foreground">Select a company, year, and quarter</p>
            <p className="text-xs text-muted-foreground/60 mt-1">Then click Generate Insights to extract competitive intelligence</p>
          </div>
        )}

      </div>
    </div>
  );
}
