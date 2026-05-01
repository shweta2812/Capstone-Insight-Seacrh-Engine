"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Trash2, FileText, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { DocumentDrawer } from "@/components/document-drawer";
import type { Citation } from "@/lib/types";

interface Turn {
  question: string;
  answer: string;
  citations: Citation[];
}

/** Renders inline content: bold + [Source N] chips */
function InlineContent({
  text,
  onSourceClick,
  activeSource,
}: {
  text: string;
  onSourceClick: (ref: number) => void;
  activeSource: number | null;
}) {
  const parts = text.split(/(\[Source \d+\]|\*\*[^*]+\*\*)/g);
  return (
    <>
      {parts.map((part, i) => {
        const srcMatch = part.match(/\[Source (\d+)\]/);
        if (srcMatch) {
          const ref = parseInt(srcMatch[1]);
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
        if (part.startsWith("**") && part.endsWith("**")) {
          return <strong key={i} className="font-semibold text-foreground">{part.slice(2, -2)}</strong>;
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}

function AnswerText({
  text,
  onSourceClick,
  activeSource,
}: {
  text: string;
  onSourceClick: (ref: number) => void;
  activeSource: number | null;
}) {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];

  lines.forEach((line, i) => {
    if (/^#{1,3}\s/.test(line)) {
      elements.push(
        <p key={i} className="text-sm font-semibold text-foreground mt-3 mb-0.5 first:mt-0">
          <InlineContent text={line.replace(/^#{1,3}\s/, "")} onSourceClick={onSourceClick} activeSource={activeSource} />
        </p>
      );
    } else if (/^---+$/.test(line.trim())) {
      elements.push(<hr key={i} className="border-border my-2" />);
    } else if (/^>\s/.test(line)) {
      elements.push(
        <blockquote key={i} className="border-l-2 border-primary/40 pl-3 my-1 text-sm text-muted-foreground italic">
          <InlineContent text={line.replace(/^>\s/, "")} onSourceClick={onSourceClick} activeSource={activeSource} />
        </blockquote>
      );
    } else if (/^[-*•]\s/.test(line)) {
      elements.push(
        <div key={i} className="flex gap-2 text-sm text-foreground/85 leading-relaxed">
          <span className="shrink-0 text-muted-foreground">·</span>
          <span><InlineContent text={line.replace(/^[-*•]\s/, "")} onSourceClick={onSourceClick} activeSource={activeSource} /></span>
        </div>
      );
    } else if (/^\d+\.\s/.test(line)) {
      const num = line.match(/^(\d+)\.\s/)?.[1];
      elements.push(
        <div key={i} className="flex gap-2 text-sm text-foreground/85 leading-relaxed">
          <span className="shrink-0 text-muted-foreground font-medium w-4">{num}.</span>
          <span><InlineContent text={line.replace(/^\d+\.\s/, "")} onSourceClick={onSourceClick} activeSource={activeSource} /></span>
        </div>
      );
    } else if (line.trim() === "") {
      elements.push(<div key={i} className="h-1.5" />);
    } else {
      elements.push(
        <p key={i} className="text-sm text-foreground/85 leading-relaxed">
          <InlineContent text={line} onSourceClick={onSourceClick} activeSource={activeSource} />
        </p>
      );
    }
  });

  return <div className="space-y-0.5">{elements}</div>;
}

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
          <button onClick={onOpenFull} className="text-[11px] text-primary hover:underline font-medium">
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
  const [activeSource, setActiveSource] = useState<{ turnIdx: number; ref: number } | null>(null);
  const [drawer, setDrawer] = useState<{ open: boolean; company: string; period: string }>({
    open: false, company: "", period: "",
  });
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, loading]);

  const ask = async (q: string) => {
    const trimmed = q.trim();
    if (!trimmed || loading) return;

    // Clear input immediately on send
    setQuestion("");
    setLoading(true);
    setError("");
    setActiveSource(null);

    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed, filters: {}, history: history.slice(-5) }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setHistory(h => [...h, { question: trimmed, answer: data.answer, citations: data.citations ?? [] }]);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      ask(question);
    }
  };

  const handleSourceClick = (turnIdx: number, ref: number) => {
    setActiveSource(prev =>
      prev?.turnIdx === turnIdx && prev?.ref === ref ? null : { turnIdx, ref }
    );
  };

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Minimal header */}
      <header className="h-14 flex items-center px-6 border-b border-[#e8e8e8] bg-white shrink-0">
        <h1 className="text-sm font-semibold text-gray-900">Ask AI</h1>
      </header>

      <div className="flex-1 flex flex-col overflow-hidden p-6 gap-4">

        {/* Chat history */}
        <div className="flex-1 overflow-y-auto space-y-4 min-h-0">
          {history.length === 0 && !loading && (
            <div className="flex items-center justify-center h-full">
              <p className="text-sm text-muted-foreground">Ask anything about competitors, strategy, financials, or any general question.</p>
            </div>
          )}

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
                    onSourceClick={ref => handleSourceClick(turnIdx, ref)}
                    activeSource={activeSource?.turnIdx === turnIdx ? activeSource.ref : null}
                  />

                  {activeSource?.turnIdx === turnIdx && (() => {
                    const cit = turn.citations.find(c => c.ref === activeSource.ref);
                    return cit ? (
                      <SourceSnippetPanel
                        citation={cit}
                        onClose={() => setActiveSource(null)}
                        onOpenFull={() => setDrawer({ open: true, company: cit.company, period: cit.period })}
                      />
                    ) : null;
                  })()}

                  {turn.citations.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-2 border-t border-border/50">
                      {turn.citations.map(c => (
                        <button
                          key={c.ref}
                          onClick={() => setDrawer({ open: true, company: c.company, period: c.period })}
                          className="text-[11px] px-2 py-0.5 rounded-full bg-secondary border border-border text-muted-foreground hover:bg-primary/10 hover:border-primary/40 hover:text-primary transition-colors"
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
                  {[0, 1, 2].map(i => (
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
            ref={textareaRef}
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything…"
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
