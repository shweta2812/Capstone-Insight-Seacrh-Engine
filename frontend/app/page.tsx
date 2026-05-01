"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { CREDIBILITY_CONFIG, type OverviewResponse, type TopicOverview } from "@/lib/types";
import { RefreshCw, X } from "lucide-react";

// ── Helpers ────────────────────────────────────────────────────────────────────
function timeAgo(iso: string | null): string {
  if (!iso) return "Never";
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "Just now";
  if (m < 60) return `${m} min ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function stripMarkdown(text: string): string {
  return text
    .replace(/#{1,6}\s*/g, "")       // headings
    .replace(/\*\*(.+?)\*\*/g, "$1") // bold
    .replace(/\*(.+?)\*/g, "$1")     // italic
    .replace(/>\s*/g, "")            // blockquotes
    .replace(/[-•]\s+/g, "")         // bullets
    .replace(/\n+/g, " ")            // newlines
    .trim();
}

function articleType(article: { title?: string; source?: string; source_domain?: string }): string {
  const t = (article.title ?? "").toLowerCase();
  const s = (article.source ?? article.source_domain ?? "").toLowerCase();
  if (/earnings|quarterly results|q[1-4] 20\d\d|annual report/.test(t)) return "Earnings";
  if (/press release|newsroom|ir\.|investor/.test(s) || /ir\.|investor/.test(t)) return "Press Release";
  if (/sec\.gov|10-k|10-q|8-k/.test(s + t)) return "SEC Filing";
  return "News";
}

function latestArticleInfo(t: TopicOverview): { companyName: string; date: string; type: string } | null {
  let best: { companyName: string; date: string; type: string } | null = null;
  for (const c of t.companies) {
    for (const a of c.articles) {
      if (!a.date) continue;
      if (!best || a.date > best.date) {
        best = { companyName: c.company_name, date: a.date, type: articleType(a) };
      }
    }
  }
  return best;
}

function bestCredTier(t: TopicOverview): string {
  for (const tier of ["1", "2", "3", "0B"]) {
    if (t.companies.some(c => c.credibility_tier === tier)) return tier;
  }
  return "0B";
}

// ── Skeleton card ──────────────────────────────────────────────────────────────
function CardSkeleton() {
  return (
    <div className="bg-white border border-[#e8e8e8] rounded-2xl p-5 animate-pulse">
      <div className="flex items-center justify-between mb-3">
        <div className="h-5 bg-gray-100 rounded w-36" />
        <div className="h-5 bg-gray-100 rounded-full w-14" />
      </div>
      <div className="h-3 bg-gray-100 rounded w-full mb-2" />
      <div className="h-3 bg-gray-100 rounded w-4/5 mb-5" />
      <div className="flex items-center justify-between">
        <div className="h-3 bg-gray-100 rounded w-28" />
        <div className="h-5 bg-gray-100 rounded-full w-16" />
      </div>
    </div>
  );
}

// ── Topic card ─────────────────────────────────────────────────────────────────
const CRED_PILL: Record<string, { label: string; cls: string }> = {
  "1":  { label: "Official", cls: "bg-green-50 text-green-700 border border-green-100" },
  "2":  { label: "Press",    cls: "bg-blue-50 text-blue-600 border border-blue-100" },
  "3":  { label: "General",  cls: "bg-amber-50 text-amber-700 border border-amber-100" },
  "0B": { label: "Unverified", cls: "bg-gray-100 text-gray-500 border border-gray-200" },
};

function TopicCard({ topic, onRefresh, isRefreshing, onDelete, deleting }: {
  topic: TopicOverview;
  onRefresh: (id: string) => void;
  isRefreshing: boolean;
  onDelete: (id: string) => void;
  deleting: boolean;
}) {
  const tier = bestCredTier(topic);
  const pill = CRED_PILL[tier] ?? CRED_PILL["0B"];
  const latest = latestArticleInfo(topic);

  return (
    <div className="relative group">
      {/* Delete X — top-left corner */}
      <button
        onClick={e => { e.preventDefault(); e.stopPropagation(); onDelete(topic.topic_id); }}
        disabled={deleting}
        className="absolute -top-2 -left-2 z-10 w-5 h-5 bg-gray-200 hover:bg-red-500 text-gray-500 hover:text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-150 disabled:opacity-50"
        title="Delete topic"
      >
        <X size={10} />
      </button>

      <Link href={`/topics/${topic.topic_id}`} className="block">
        <div className={`bg-white border rounded-2xl p-5 h-full flex flex-col gap-3 hover:shadow-sm transition-all duration-150 cursor-pointer ${isRefreshing ? "border-blue-200 bg-blue-50/30" : "border-[#e0e0e0] hover:border-[#c0c0c0]"}`}>
          {/* Title + count */}
          <div className="flex items-start justify-between gap-3">
            <h3 className="font-semibold text-[15px] text-gray-900 leading-snug group-hover:text-black">
              {topic.topic_name}
            </h3>
            <span className="text-[11px] text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full shrink-0 font-medium">
              {topic.companies.length} co.
            </span>
          </div>

          {/* Latest article info */}
          {latest ? (
            <div className="flex-1">
              <p className="text-[13px] font-medium text-gray-800">{latest.companyName}</p>
              <p className="text-[12px] text-gray-400 mt-0.5">{latest.type} · {latest.date}</p>
            </div>
          ) : (
            <p className="text-[13px] text-gray-400 flex-1 italic">No articles yet — click Refresh</p>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between pt-1">
            {isRefreshing ? (
              <span className="flex items-center gap-1.5 text-[12px] text-blue-500">
                <RefreshCw size={10} className="animate-spin" /> Generating…
              </span>
            ) : (
              <span className="text-[12px] text-gray-400">
                Updated {timeAgo(topic.last_updated)}
              </span>
            )}
            <span className={`text-[11px] font-medium px-2.5 py-0.5 rounded-full ${pill.cls}`}>
              {pill.label}
            </span>
          </div>
        </div>
      </Link>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────
export default function OverviewPage() {
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [topicName, setTopicName] = useState("");
  const [keywords, setKeywords] = useState("");
  const [addingTopic, setAddingTopic] = useState(false);
  const [refreshingTopics, setRefreshingTopics] = useState<Set<string>>(new Set());
  const [deletingTopics, setDeletingTopics] = useState<Set<string>>(new Set());

  const fetchData = useCallback(async () => {
    try {
      const res = await api.overview();
      setData(res);
    } catch {}
  }, []);

  useEffect(() => {
    fetchData().finally(() => setLoading(false));
  }, [fetchData]);

  const handleAdd = async () => {
    if (!topicName.trim()) return;
    setAddingTopic(true);
    const kws = keywords.split(",").map(k => k.trim()).filter(Boolean);
    await api.topics.create(topicName.trim(), kws);
    setTopicName("");
    setKeywords("");
    await fetchData();
    setAddingTopic(false);
  };

  const pollUntilUpdated = useCallback(async (topicIds: string[], onDone?: () => void) => {
    // Poll every 5s for up to 3 minutes
    const startTimes: Record<string, string | null> = {};
    data?.topics.forEach(t => {
      if (topicIds.includes(t.topic_id)) startTimes[t.topic_id] = t.last_updated;
    });

    let tries = 0;
    const poll = async () => {
      const res = await api.overview().catch(() => null);
      if (res) {
        setData(res);
        // Check if all target topics have newer timestamps
        const allDone = topicIds.every(id => {
          const t = res.topics.find(t => t.topic_id === id);
          return t && t.last_updated && t.last_updated !== startTimes[id];
        });
        if (allDone) { onDone?.(); return; }
      }
      tries++;
      if (tries < 36) setTimeout(poll, 5000); // 3 min max
      else onDone?.();
    };
    setTimeout(poll, 6000);
  }, [data]);

  const handleRefreshAll = async () => {
    if (!data) return;
    setRefreshing(true);
    const ids = data.topics.map(t => t.topic_id);
    setRefreshingTopics(new Set(ids));
    await Promise.all(ids.map(id => api.topics.refresh(id).catch(() => {})));
    pollUntilUpdated(ids, () => {
      setRefreshing(false);
      setRefreshingTopics(new Set());
    });
  };

  const handleRefreshTopic = async (id: string) => {
    setRefreshingTopics(prev => new Set([...prev, id]));
    await api.topics.refresh(id).catch(() => {});
    pollUntilUpdated([id], () => {
      setRefreshingTopics(prev => { const s = new Set(prev); s.delete(id); return s; });
    });
  };

  const handleDelete = async (id: string) => {
    setDeletingTopics(prev => new Set([...prev, id]));
    try {
      await api.topics.delete(id);
      await fetchData();
    } catch {}
    setDeletingTopics(prev => { const s = new Set(prev); s.delete(id); return s; });
  };

  const lastRefreshed = data?.last_refreshed ? timeAgo(data.last_refreshed) : null;
  const topicCount = data?.topics.length ?? 0;

  return (
    <div className="flex flex-col flex-1 overflow-auto bg-[#f7f7f7]">
      {/* Top bar */}
      <header className="h-14 flex items-center justify-between px-8 border-b border-[#e8e8e8] bg-white shrink-0">
        <span className="text-sm font-bold text-gray-900">Blue Shield CI Engine</span>
        <span className="text-sm font-semibold text-gray-900">Overview</span>
        <div className="flex items-center gap-3">
          {lastRefreshed && (
            <span className="text-xs text-gray-400">Last refreshed {lastRefreshed}</span>
          )}
          <button className="text-gray-400 hover:text-gray-600 text-lg leading-none">···</button>
        </div>
      </header>

      <div className="flex-1 overflow-auto">
        <div className="max-w-5xl mx-auto px-8 py-10">

          {/* Hero */}
          <div className="mb-8">
            <p className="text-xs font-semibold tracking-widest text-gray-400 uppercase mb-2">
              Competitive Intelligence
            </p>
            <h1 className="text-3xl font-bold text-gray-900 mb-1">Your topic feed</h1>
            <p className="text-[14px] text-gray-500">
              Auto-refreshed on open · {topicCount > 0 ? topicCount : "—"} topics tracked · 10 competitors
            </p>
          </div>

          {/* Add topic row */}
          <div className="flex gap-3 mb-8">
            <input
              className="flex-[0_0_220px] bg-white border border-[#d8d8d8] rounded-xl px-4 py-3 text-[14px] text-gray-700 placeholder:text-gray-400 focus:outline-none focus:border-gray-400"
              placeholder="New topic name (e.g. Mobile)"
              value={topicName}
              onChange={e => setTopicName(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter") handleAdd(); }}
            />
            <input
              className="flex-1 bg-white border border-[#d8d8d8] rounded-xl px-4 py-3 text-[14px] text-gray-700 placeholder:text-gray-400 focus:outline-none focus:border-gray-400"
              placeholder="Keywords (comma separated)"
              value={keywords}
              onChange={e => setKeywords(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter") handleAdd(); }}
            />
            <button
              onClick={handleAdd}
              disabled={addingTopic || !topicName.trim()}
              className="bg-white border border-[#d8d8d8] rounded-xl px-5 py-3 text-[14px] font-medium text-gray-800 hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 transition-colors whitespace-nowrap"
            >
              {addingTopic ? "Adding…" : "+ Add topic"}
            </button>
          </div>

          {/* Topics section */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <p className="text-xs font-semibold tracking-widest text-gray-400 uppercase">
                {loading ? "Loading…" : `Your topics`}
              </p>
              <button
                onClick={handleRefreshAll}
                disabled={refreshing || loading}
                className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-800 disabled:opacity-50 transition-colors"
              >
                <RefreshCw size={12} className={refreshing ? "animate-spin" : ""} />
                {refreshing ? "Refreshing…" : "Refresh all"}
              </button>
            </div>

            {loading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {Array.from({ length: 3 }).map((_, i) => <CardSkeleton key={i} />)}
              </div>
            ) : !data || data.topics.length === 0 ? (
              <div className="bg-white border border-dashed border-[#e0e0e0] rounded-2xl p-14 text-center">
                <p className="text-[15px] text-gray-400 font-medium">No topics yet</p>
                <p className="text-[13px] text-gray-400 mt-1">Add a topic above to start tracking.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {data.topics.map(t => (
                  <TopicCard
                    key={t.topic_id}
                    topic={t}
                    onRefresh={handleRefreshTopic}
                    isRefreshing={refreshingTopics.has(t.topic_id)}
                    onDelete={handleDelete}
                    deleting={deletingTopics.has(t.topic_id)}
                  />
                ))}
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
