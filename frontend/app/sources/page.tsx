"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/header";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, ExternalLink, CheckCircle } from "lucide-react";
import { DocumentDrawer } from "@/components/document-drawer";

interface LastUpdate {
  time: string | null;
  new_docs: number;
  new_articles: number;
  status: string;
}

interface ScraperStatus {
  indexed: Record<string, string[]>;
  news_counts: Record<string, number>;
  sources: Record<string, string>;
  last_update: LastUpdate;
}

export default function SourcesPage() {
  const [status, setStatus] = useState<ScraperStatus | null>(null);
  const [scraping, setScraping] = useState(false);
  const [message, setMessage] = useState("");
  const [drawer, setDrawer] = useState<{ open: boolean; mode: "filing" | "news"; company: string; period?: string }>({
    open: false, mode: "filing", company: "",
  });

  const openFiling = (company: string, period: string) =>
    setDrawer({ open: true, mode: "filing", company, period });
  const openNews = (company: string) =>
    setDrawer({ open: true, mode: "news", company });

  const load = () =>
    fetch("/api/scraper/status")
      .then(r => r.json())
      .then(setStatus)
      .catch(() => {});

  useEffect(() => { load(); }, []);

  const runScraper = async () => {
    setScraping(true);
    setMessage("");
    try {
      const res = await fetch("/api/scraper/run", { method: "POST" });
      const data = await res.json();
      setMessage(data.message);
      setTimeout(load, 5000);
    } catch {
      setMessage("Error starting scraper.");
    } finally {
      setScraping(false);
    }
  };

  return (
    <div className="flex flex-col flex-1 overflow-auto">
      <Header title="Data Sources" subtitle="Web scraping · Auto-update · Coverage tracker" />
      <div className="flex-1 p-6 space-y-5">

        {/* Action banner */}
        <div className="bg-white border border-border rounded-xl p-5 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-foreground">Auto-Update Engine</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Automatically fetches SEC EDGAR filings + live news on startup, then refreshes every 6 hours.
            </p>
            {status?.last_update?.time && (
              <p className="text-xs text-emerald-600 mt-1">
                Last updated: {new Date(status.last_update.time).toLocaleString("en-US")}
                {" · "}+{status.last_update.new_docs} filings, +{status.last_update.new_articles} news articles
              </p>
            )}
            {status?.last_update?.status === "running" && (
              <p className="text-xs text-primary mt-1 flex items-center gap-1">
                <RefreshCw size={10} className="animate-spin" /> Updating in background…
              </p>
            )}
            {status?.last_update?.status?.startsWith("error") && (
              <p className="text-xs text-red-500 mt-1">{status.last_update.status}</p>
            )}
            {message && <p className="text-xs text-primary mt-1">{message}</p>}
          </div>
          <button
            onClick={runScraper}
            disabled={scraping}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/80 disabled:opacity-50 transition-colors shrink-0 ml-4"
          >
            <RefreshCw size={14} className={scraping ? "animate-spin" : ""} />
            {scraping ? "Scanning…" : "Update Now"}
          </button>
        </div>

        {/* How it works */}
        <div className="bg-white border border-border rounded-xl p-5 shadow-sm">
          <p className="text-xs font-semibold text-muted-foreground mb-3">HOW AUTO-UPDATE WORKS</p>
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-3">
            {[
              { step: "1", title: "Scrape", desc: "On startup + every 6 hours: fetches SEC EDGAR filings (10-Q/8-K) and live Google News RSS articles" },
              { step: "2", title: "Detect New", desc: "Compares against already-indexed documents, skips duplicates" },
              { step: "3", title: "Index", desc: "Cleans, chunks, embeds, and stores new docs in ChromaDB vector database" },
              { step: "4", title: "Summarize", desc: "Claude auto-generates key insights and summary for each new document" },
            ].map(item => (
              <div key={item.step} className="flex gap-3 p-3 rounded-lg bg-secondary/30">
                <div className="w-6 h-6 rounded-full bg-primary/15 text-primary text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                  {item.step}
                </div>
                <div>
                  <p className="text-xs font-medium text-foreground">{item.title}</p>
                  <p className="text-[11px] text-muted-foreground mt-0.5">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Coverage by company */}
        <div className="bg-white border border-border rounded-xl shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-border flex items-center justify-between">
            <p className="text-xs font-semibold text-muted-foreground">CURRENT COVERAGE</p>
            <button onClick={load} className="text-xs text-muted-foreground hover:text-primary transition-colors">
              Refresh
            </button>
          </div>
          {status ? (
            <div className="divide-y divide-border">
              {Object.entries(status.indexed).map(([company, periods]) => {
                const sorted = [...periods].sort();
                return (
                  <div key={company} className="px-5 py-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <CheckCircle size={14} className="text-emerald-500" />
                        <span className="text-sm font-medium text-foreground">{company}</span>
                        <Badge variant="success">{periods.length} filings</Badge>
                        {(status?.news_counts?.[company] ?? 0) > 0 && (
                          <button onClick={() => openNews(company)}>
                            <Badge variant="outline" className="cursor-pointer hover:bg-secondary transition-colors">
                              {status.news_counts[company]} news
                            </Badge>
                          </button>
                        )}
                      </div>
                      {status.sources[company] && (
                        <a href={status.sources[company]} target="_blank" rel="noopener noreferrer"
                          className="text-[11px] text-muted-foreground hover:text-primary flex items-center gap-1">
                          IR Page <ExternalLink size={10} />
                        </a>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {sorted.map(p => (
                        <button
                          key={p}
                          onClick={() => openFiling(company, p)}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-secondary border border-border text-muted-foreground hover:bg-primary/10 hover:border-primary/40 hover:text-primary transition-colors cursor-pointer"
                        >
                          {p}
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="px-5 py-8 text-center text-xs text-muted-foreground">Loading…</div>
          )}
        </div>

      </div>

      <DocumentDrawer
        open={drawer.open}
        onClose={() => setDrawer(d => ({ ...d, open: false }))}
        mode={drawer.mode}
        company={drawer.company}
        period={drawer.period}
      />
    </div>
  );
}
