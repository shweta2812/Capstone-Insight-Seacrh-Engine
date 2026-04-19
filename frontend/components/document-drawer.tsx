"use client";

import { useEffect, useState } from "react";
import { X, FileText, Newspaper, ExternalLink, Loader2, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface FilingDetail {
  company: string;
  period: string;
  source_type: string;
  char_count: number;
  filename: string;
  text_preview: string;
  summary: string | null;
  insights: string | null;
}

interface NewsArticle {
  filename: string;
  title: string;
  date: string;
  url: string;
  source: string;
  ai_summary: string | null;
}

interface Props {
  open: boolean;
  onClose: () => void;
  mode: "filing" | "news";
  company: string;
  period?: string;        // for filing mode
}

function InsightBlock({ text }: { text: string }) {
  const lines = text.split("\n").filter(Boolean);
  return (
    <div className="space-y-2">
      {lines.map((line, i) => {
        const isBullet = line.startsWith("•") || line.startsWith("-") || line.match(/^\d+\./);
        return (
          <p key={i} className={cn(
            "text-xs leading-relaxed",
            isBullet ? "text-foreground pl-1" : "text-muted-foreground italic"
          )}>
            {line}
          </p>
        );
      })}
    </div>
  );
}

function NewsArticleRow({ article, companyDisplay }: { article: NewsArticle; companyDisplay: string }) {
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<string | null>(article.ai_summary);

  const fetchSummary = async () => {
    if (summary) { setExpanded(!expanded); return; }
    setLoading(true);
    setExpanded(true);
    try {
      const res = await fetch(
        `/api/news/summarize?filename=${encodeURIComponent(article.filename)}&company_display=${encodeURIComponent(companyDisplay)}`,
        { method: "POST" }
      );
      const data = await res.json();
      setSummary(data.insights);
    } catch {
      setSummary("Failed to generate summary.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        onClick={fetchSummary}
        className="w-full text-left p-3 hover:bg-secondary/20 transition-colors"
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-foreground leading-snug line-clamp-2">{article.title}</p>
            <p className="text-[10px] text-muted-foreground mt-1">{article.date} · {article.source}</p>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            {article.url && (
              <a href={article.url} target="_blank" rel="noopener noreferrer"
                onClick={e => e.stopPropagation()}
                className="text-muted-foreground hover:text-primary transition-colors">
                <ExternalLink size={11} />
              </a>
            )}
            <Sparkles size={11} className={cn("transition-colors", summary ? "text-primary" : "text-muted-foreground/40")} />
          </div>
        </div>
      </button>
      {expanded && (
        <div className="px-3 pb-3 pt-1 border-t border-border bg-secondary/10">
          {loading
            ? <div className="flex items-center gap-2 text-xs text-muted-foreground py-2">
                <Loader2 size={12} className="animate-spin" /> Generating AI insights…
              </div>
            : summary
              ? <InsightBlock text={summary} />
              : null
          }
        </div>
      )}
    </div>
  );
}

export function DocumentDrawer({ open, onClose, mode, company, period }: Props) {
  const [filing, setFiling] = useState<FilingDetail | null>(null);
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setFiling(null);
    setNews([]);
    setLoading(true);

    if (mode === "filing" && period) {
      fetch(`/api/documents/filing?company=${encodeURIComponent(company)}&period=${encodeURIComponent(period)}`)
        .then(r => r.json())
        .then(setFiling)
        .catch(() => {})
        .finally(() => setLoading(false));
    } else if (mode === "news") {
      fetch(`/api/news/list?company_display=${encodeURIComponent(company)}`)
        .then(r => r.json())
        .then(setNews)
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [open, mode, company, period]);

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/30 z-40" onClick={onClose} />

      {/* Drawer */}
      <div className="fixed right-0 top-0 h-full w-[520px] max-w-full bg-white shadow-2xl z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border shrink-0">
          <div className="flex items-center gap-2">
            {mode === "filing"
              ? <FileText size={16} className="text-primary" />
              : <Newspaper size={16} className="text-primary" />
            }
            <div>
              <p className="text-sm font-semibold text-foreground">{company}</p>
              <p className="text-[11px] text-muted-foreground">
                {mode === "filing" ? period : "Latest News"}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-md hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors">
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {loading && (
            <div className="flex items-center justify-center py-16 gap-2 text-muted-foreground text-sm">
              <Loader2 size={16} className="animate-spin" /> Loading…
            </div>
          )}

          {/* Filing view */}
          {!loading && mode === "filing" && filing && (
            <>
              <div className="flex gap-2 flex-wrap">
                <Badge variant="outline">{filing.source_type.replace("_", " ").toUpperCase()}</Badge>
                <Badge variant="outline">{(filing.char_count / 1000).toFixed(0)}k chars</Badge>
                <Badge variant="outline">{filing.filename}</Badge>
              </div>

              {/* AI Summary */}
              {filing.summary && (
                <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
                  <p className="text-[11px] font-semibold text-primary mb-2 flex items-center gap-1">
                    <Sparkles size={11} /> AI SUMMARY
                  </p>
                  <p className="text-xs text-foreground leading-relaxed">{filing.summary}</p>
                </div>
              )}

              {/* AI Insights */}
              {filing.insights && (
                <div className="bg-secondary/30 border border-border rounded-lg p-4">
                  <p className="text-[11px] font-semibold text-muted-foreground mb-3 flex items-center gap-1">
                    <Sparkles size={11} /> COMPETITIVE INSIGHTS
                  </p>
                  <InsightBlock text={filing.insights} />
                </div>
              )}

              {!filing.summary && !filing.insights && (
                <div className="text-xs text-muted-foreground bg-secondary/20 rounded-lg p-4">
                  AI insights not yet generated. Set ANTHROPIC_API_KEY to enable auto-summarization.
                </div>
              )}

              {/* Text preview */}
              <div>
                <p className="text-[11px] font-semibold text-muted-foreground mb-2">DOCUMENT PREVIEW</p>
                <pre className="text-[11px] text-muted-foreground leading-relaxed whitespace-pre-wrap font-sans bg-secondary/20 rounded-lg p-4 max-h-80 overflow-y-auto">
                  {filing.text_preview}
                </pre>
              </div>
            </>
          )}

          {/* News view */}
          {!loading && mode === "news" && (
            <>
              <p className="text-xs text-muted-foreground">
                {news.length} articles · Click any article to generate AI competitive insights
              </p>
              <div className="space-y-2">
                {news.map(article => (
                  <NewsArticleRow key={article.filename} article={article} companyDisplay={company} />
                ))}
                {news.length === 0 && (
                  <p className="text-xs text-muted-foreground py-8 text-center">No news articles found.</p>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
