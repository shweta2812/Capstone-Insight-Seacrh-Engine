"use client";

import { useState, useRef, useEffect } from "react";
import { Header } from "@/components/header";
import { Send, Trash2, ChevronDown, ChevronUp, FileText, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { DocumentDrawer } from "@/components/document-drawer";
import type { Citation } from "@/lib/types";

interface Turn {
  question: string;
  answer: string;
  citations: Citation[];
}

const SUGGESTIONS = [
  "What are Elevance's key strategic priorities for 2024?",
  "How is UnitedHealth growing Medicare Advantage?",
  "What technology investments are competitors making?",
  "Compare medical loss ratios across competitors.",
  "What did competitors say about Medicaid redeterminations?",
  "How is Aetna's CVS integration affecting performance?",
];

const COMPANY_FILTERS = ["All", "Elevance Health", "UnitedHealth Group", "Aetna (CVS Health)",
  "Cigna Group", "Humana", "Centene", "Molina Healthcare", "Oscar Health"];
const COMPANY_KEY_MAP: Record<string, string> = {
  "Elevance Health": "elevance", "UnitedHealth Group": "united",
  "Aetna (CVS Health)": "aetna", "Cigna Group": "cigna",
  "Humana": "humana", "Centene": "centene",
  "Molina Healthcare": "molina", "Oscar Health": "oscar",
};

/** Renders answer text with [Source N] turned into clickable inline chips */
function AnswerText({
  text,
  citations,
  onSourceClick,
  activeSource,
}: {
  text: string;
  citations: Citation[];
  onSourceClick: (ref: number) => void;
  activeSource: number | null;
}) {
  const parts = text.split(/(\[Source \d+\])/g);
  return (
    <p className="text-sm text-foreground/85 leading-relaxed whitespace-pre-wrap">
      {parts.map((part, i) => {
        const m = part.match(/\[Source (\d+)\]/);
        if (m) {
          const ref = parseInt(m[1]);
          const active = activeSource === ref;
          return (
            <button
              key={i}
              onClick={() => onSourceClick(ref)}
              className={cn(
                "inline-flex items-center gap-0.5 text-[11px] px-1.5 py-0.5 rounded font-medium transition-colors mx-0.5 align-baseline",
                active
                  ? "bg-primary text-primary-foreground"
                  : "bg-primary/15 text-primary hover:bg-primary/25 border border-primary/30"
              )}
            >
              <FileText size={9} />
              {part}
            </button>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </p>
  );
}

/** Inline snippet panel shown when a [Source N] is clicked */
function SourceSnippetPanel({
  citation,
  onClose,
  onOpenFull,
}: {
  citation: Citation;
  onClose: () => void;
  onOpenFull: () => void;
}) {
  return (
    <div className="mt-2 rounded-lg border border-primary/20 bg-blue-50/60 p-3 text-xs space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-primary">[Source {citation.ref}]</span>
          <span className="text-muted-foreground">{citation.company} · {citation.period}</span>
          <span className="text-muted-foreground/60">{citation.source_type}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onOpenFull}
            className="text-[11px] text-primary hover:underline font-medium"
          >
            View full doc →
          </button>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X size={12} />
          </button>
        </div>
      </div>
      <blockquote className="border-l-2 border-primary/30 pl-2 text-muted-foreground leading-relaxed italic">
        {citation.snippet}
      </blockquote>
      <div className="text-[10px] text-muted-foreground/50">
        Relevance score: {(citation.score * 100).toFixed(0)}% · {citation.filename}
      </div>
    </div>
  );
}

export default function SearchPage() {
  const [history, setHistory] = useState<Turn[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [companyFilter, setCompanyFilter] = useState("All");
  const [yearFilter, setYearFilter] = useState("All");
  const [activeSource, setActiveSource] = useState<{ turnIdx: number; ref: number } | null>(null);
  const [drawer, setDrawer] = useState<{ open: boolean; company: string; period: string }>({
    open: false, company: "", period: "",
  });
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, loading]);

  const ask = async (q: string) => {
    if (!q.trim() || loading) return;
    setLoading(true);
    setError("");
    setActiveSource(null);
    const filters: Record<string, string> = {};
    if (companyFilter !== "All") filters.company = COMPANY_KEY_MAP[companyFilter] ?? companyFilter.toLowerCase();
    if (yearFilter !== "All") filters.year = yearFilter;

    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, filters, history: history.slice(-5) }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setHistory(h => [...h, { question: q, answer: data.answer, citations: data.citations ?? [] }]);
      setQuestion("");
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleSourceClick = (turnIdx: number, ref: number) => {
    setActiveSource(prev =>
      prev?.turnIdx === turnIdx && prev?.ref === ref ? null : { turnIdx, ref }
    );
  };

  const openDrawer = (company: string, period: string) =>
    setDrawer({ open: true, company, period });

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <Header title="Ask / Search" subtitle="RAG-powered Q&A · Grounded in earnings call transcripts" />

      <div className="flex-1 flex flex-col overflow-hidden p-6 gap-4">

        {/* Filters */}
        <div className="flex items-center gap-2 shrink-0 flex-wrap">
          <span className="text-xs text-muted-foreground">Filter:</span>
          {COMPANY_FILTERS.map(co => (
            <button
              key={co}
              onClick={() => setCompanyFilter(co)}
              className={cn(
                "text-xs px-3 py-1.5 rounded-md border transition-colors",
                companyFilter === co
                  ? "bg-primary/20 border-primary/40 text-primary"
                  : "border-border text-muted-foreground hover:border-primary/30 hover:text-foreground"
              )}
            >
              {co}
            </button>
          ))}
          <select
            value={yearFilter}
            onChange={e => setYearFilter(e.target.value)}
            className="text-xs px-2 py-1.5 rounded-md border border-border bg-secondary text-muted-foreground"
          >
            <option>All</option>
            {[2025,2024,2023,2022,2021,2020,2019].map(y => <option key={y}>{y}</option>)}
          </select>
        </div>

        {/* Suggested questions */}
        {history.length === 0 && (
          <div className="shrink-0">
            <p className="text-xs text-muted-foreground mb-2">Suggested questions</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => ask(s)}
                  className="text-xs px-3 py-1.5 rounded-md border border-border bg-secondary/30 text-muted-foreground hover:text-foreground hover:border-primary/30 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Chat history */}
        <div className="flex-1 overflow-y-auto space-y-4 min-h-0">
          {history.map((turn, turnIdx) => (
            <div key={turnIdx} className="space-y-2">
              {/* User question */}
              <div className="flex justify-end">
                <div className="max-w-[75%] bg-primary/15 border border-primary/20 rounded-lg px-4 py-3 text-sm text-foreground">
                  {turn.question}
                </div>
              </div>

              {/* AI answer */}
              <div className="flex justify-start">
                <div className="max-w-[90%] bg-card border border-border rounded-lg px-4 py-3 space-y-2">
                  <AnswerText
                    text={turn.answer}
                    citations={turn.citations}
                    onSourceClick={ref => handleSourceClick(turnIdx, ref)}
                    activeSource={activeSource?.turnIdx === turnIdx ? activeSource.ref : null}
                  />

                  {/* Inline snippet panel */}
                  {activeSource?.turnIdx === turnIdx && (() => {
                    const cit = turn.citations.find(c => c.ref === activeSource.ref);
                    return cit ? (
                      <SourceSnippetPanel
                        citation={cit}
                        onClose={() => setActiveSource(null)}
                        onOpenFull={() => openDrawer(cit.company, cit.period)}
                      />
                    ) : null;
                  })()}

                  {/* Citation pills */}
                  {turn.citations.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-2 border-t border-border/50">
                      {turn.citations.map(c => (
                        <button
                          key={c.ref}
                          onClick={() => openDrawer(c.company, c.period)}
                          className="text-[11px] px-2 py-0.5 rounded-full bg-secondary border border-border text-muted-foreground hover:bg-primary/10 hover:border-primary/40 hover:text-primary transition-colors"
                          title={`Open ${c.company} ${c.period}`}
                        >
                          [{c.ref}] {c.company} · {c.period}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-card border border-border rounded-lg px-4 py-3">
                <div className="flex gap-1">
                  {[0,1,2].map(i => (
                    <div key={i} className="w-1.5 h-1.5 rounded-full bg-primary/50 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                  ))}
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {error && <p className="text-xs text-red-400 shrink-0">{error}</p>}

        {/* Input */}
        <div className="shrink-0 flex items-end gap-2">
          <textarea
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(question); } }}
            placeholder="Ask about competitor strategy, financials, products, or market positioning…"
            rows={2}
            className="flex-1 resize-none bg-card border border-border rounded-lg px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors"
          />
          <div className="flex flex-col gap-2">
            <button
              onClick={() => ask(question)}
              disabled={loading || !question.trim()}
              className="p-2.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/80 disabled:opacity-40 transition-colors"
            >
              <Send size={16} />
            </button>
            <button
              onClick={() => { setHistory([]); setActiveSource(null); }}
              className="p-2.5 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:border-primary/30 transition-colors"
            >
              <Trash2 size={16} />
            </button>
          </div>
        </div>

      </div>

      <DocumentDrawer
        open={drawer.open}
        onClose={() => setDrawer(d => ({ ...d, open: false }))}
        mode="filing"
        company={drawer.company}
        period={drawer.period}
      />
    </div>
  );
}
