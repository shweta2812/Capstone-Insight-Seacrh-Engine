"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { X, Send, Trash2, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

interface Citation {
  ref: number;
  company: string;
  period: string;
  source_type: string;
  filename: string;
  score: number;
  snippet: string;
}

interface Turn {
  question: string;
  answer: string;
  citations: Citation[];
}

const STORAGE_KEY = "ci_chat_history";

// ── Inline markdown + [Source N] renderer ──────────────────────────────────────
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
                "inline-flex items-center gap-0.5 text-[10px] px-1.5 py-0.5 rounded font-medium transition-colors mx-0.5 align-baseline",
                active
                  ? "bg-blue-600 text-white"
                  : "bg-blue-50 text-blue-600 hover:bg-blue-100 border border-blue-200"
              )}
            >
              <FileText size={8} />
              {part}
            </button>
          );
        }
        if (part.startsWith("**") && part.endsWith("**")) {
          return <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>;
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
        <p key={i} className="text-[13px] font-semibold text-gray-900 mt-3 mb-0.5 first:mt-0">
          <InlineContent text={line.replace(/^#{1,3}\s/, "")} onSourceClick={onSourceClick} activeSource={activeSource} />
        </p>
      );
    } else if (/^---+$/.test(line.trim())) {
      elements.push(<hr key={i} className="border-gray-200 my-2" />);
    } else if (/^>\s/.test(line)) {
      elements.push(
        <p key={i} className="border-l-2 border-blue-300 pl-2 my-1 text-[12px] text-gray-500 italic">
          <InlineContent text={line.replace(/^>\s/, "")} onSourceClick={onSourceClick} activeSource={activeSource} />
        </p>
      );
    } else if (/^[-*•]\s/.test(line)) {
      elements.push(
        <div key={i} className="flex gap-1.5 text-[13px] text-gray-700 leading-relaxed">
          <span className="shrink-0 text-gray-400 mt-0.5">·</span>
          <span><InlineContent text={line.replace(/^[-*•]\s/, "")} onSourceClick={onSourceClick} activeSource={activeSource} /></span>
        </div>
      );
    } else if (/^\d+\.\s/.test(line)) {
      const num = line.match(/^(\d+)\.\s/)?.[1];
      elements.push(
        <div key={i} className="flex gap-1.5 text-[13px] text-gray-700 leading-relaxed">
          <span className="shrink-0 text-gray-500 font-medium w-4">{num}.</span>
          <span><InlineContent text={line.replace(/^\d+\.\s/, "")} onSourceClick={onSourceClick} activeSource={activeSource} /></span>
        </div>
      );
    } else if (line.trim() === "") {
      elements.push(<div key={i} className="h-1.5" />);
    } else {
      elements.push(
        <p key={i} className="text-[13px] text-gray-700 leading-relaxed">
          <InlineContent text={line} onSourceClick={onSourceClick} activeSource={activeSource} />
        </p>
      );
    }
  });

  return <div className="space-y-0.5">{elements}</div>;
}

// ── Main widget ────────────────────────────────────────────────────────────────
export function AIChatWidget() {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);
  const [history, setHistory] = useState<Turn[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeSource, setActiveSource] = useState<{ turnIdx: number; ref: number } | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load history from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) setHistory(JSON.parse(saved));
    } catch {}
  }, []);

  // Save history to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    } catch {}
  }, [history]);

  // Scroll to bottom on new message
  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, loading, open]);

  // Focus textarea when panel opens
  useEffect(() => {
    if (open) setTimeout(() => textareaRef.current?.focus(), 100);
  }, [open]);

  const ask = useCallback(async (q: string) => {
    const trimmed = q.trim();
    if (!trimmed || loading) return;

    setQuestion("");
    setLoading(true);
    setActiveSource(null);

    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed, filters: {}, history: history.slice(-6) }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setHistory(h => [...h, { question: trimmed, answer: data.answer, citations: data.citations ?? [] }]);
    } catch (e) {
      setHistory(h => [...h, { question: trimmed, answer: `Error: ${e}`, citations: [] }]);
    } finally {
      setLoading(false);
    }
  }, [loading, history]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      ask(question);
    }
  };

  const clearHistory = () => {
    setHistory([]);
    setActiveSource(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  if (!mounted) return null;

  return createPortal(
    <>
      {/* Slide-in panel */}
      <div
        className={cn(
          "fixed top-0 right-0 h-screen w-[380px] bg-white border-l border-gray-200 shadow-xl z-[9998] flex flex-col transition-transform duration-300 ease-in-out",
          open ? "translate-x-0" : "translate-x-full"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center">
              <span className="text-white text-[11px] font-bold">B</span>
            </div>
            <span className="text-sm font-semibold text-gray-900">Ask AI</span>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={clearHistory}
              className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
              title="Clear history"
            >
              <Trash2 size={14} />
            </button>
            <button
              onClick={() => setOpen(false)}
              className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
            >
              <X size={14} />
            </button>
          </div>
        </div>

        {/* Chat area */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
          {history.length === 0 && !loading && (
            <div className="flex items-center justify-center h-full">
              <p className="text-[13px] text-gray-400 text-center leading-relaxed">
                Ask anything about competitors,<br />strategy, financials, or any topic.
              </p>
            </div>
          )}

          {history.map((turn, turnIdx) => (
            <div key={turnIdx} className="space-y-2">
              {/* User bubble */}
              <div className="flex justify-end">
                <div className="max-w-[85%] bg-blue-600 text-white rounded-2xl rounded-tr-sm px-3 py-2 text-[13px] leading-relaxed">
                  {turn.question}
                </div>
              </div>

              {/* AI bubble */}
              <div className="flex justify-start">
                <div className="max-w-[92%] bg-gray-50 border border-gray-100 rounded-2xl rounded-tl-sm px-3 py-2.5 space-y-1.5">
                  <AnswerText
                    text={turn.answer}
                    onSourceClick={ref => setActiveSource(
                      prev => prev?.turnIdx === turnIdx && prev.ref === ref ? null : { turnIdx, ref }
                    )}
                    activeSource={activeSource?.turnIdx === turnIdx ? activeSource.ref : null}
                  />

                  {/* Source snippet inline */}
                  {activeSource?.turnIdx === turnIdx && (() => {
                    const cit = turn.citations.find(c => c.ref === activeSource.ref);
                    return cit ? (
                      <div className="mt-2 rounded-lg border border-blue-100 bg-blue-50 p-2.5 text-[11px] space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-blue-600">[Source {cit.ref}] {cit.company} · {cit.period}</span>
                          <button onClick={() => setActiveSource(null)} className="text-gray-400 hover:text-gray-600">
                            <X size={10} />
                          </button>
                        </div>
                        <p className="text-gray-500 italic leading-relaxed">{cit.snippet}</p>
                      </div>
                    ) : null;
                  })()}

                  {/* Citation chips */}
                  {turn.citations.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1 border-t border-gray-100">
                      {turn.citations.map(c => (
                        <span key={c.ref} className="text-[10px] px-1.5 py-0.5 bg-white border border-gray-200 rounded-full text-gray-500">
                          [{c.ref}] {c.company} · {c.period}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-50 border border-gray-100 rounded-2xl rounded-tl-sm px-3 py-2.5">
                <div className="flex gap-1 items-center h-4">
                  {[0, 1, 2].map(i => (
                    <div
                      key={i}
                      className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input area */}
        <div className="px-3 py-3 border-t border-gray-100 shrink-0">
          <div className="flex items-end gap-2 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 focus-within:border-blue-400 focus-within:bg-white transition-colors">
            <textarea
              ref={textareaRef}
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything…"
              rows={1}
              className="flex-1 resize-none bg-transparent text-[13px] text-gray-800 placeholder:text-gray-400 focus:outline-none leading-relaxed max-h-32 overflow-y-auto"
              style={{ fieldSizing: "content" } as React.CSSProperties}
            />
            <button
              onClick={() => ask(question)}
              disabled={loading || !question.trim()}
              className="shrink-0 w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white hover:bg-blue-700 disabled:opacity-40 transition-colors mb-0.5"
            >
              <Send size={13} />
            </button>
          </div>
          <p className="text-[10px] text-gray-400 text-center mt-1.5">Enter to send · Shift+Enter for new line</p>
        </div>
      </div>

      {/* Backdrop (mobile-friendly) */}
      {open && (
        <div
          className="fixed inset-0 z-[9997] bg-black/10 backdrop-blur-[1px]"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Floating trigger button */}
      <button
        onClick={() => setOpen(o => !o)}
        className={cn(
          "fixed bottom-6 right-6 z-[9999] w-12 h-12 rounded-full bg-blue-600 hover:bg-blue-700 shadow-lg hover:shadow-xl flex items-center justify-center transition-all duration-200",
          open && "opacity-0 pointer-events-none"
        )}
        title="Ask AI"
      >
        <span className="text-white text-lg font-bold leading-none">B</span>
      </button>
    </>,
    document.body
  );
}
