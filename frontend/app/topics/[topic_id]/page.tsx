"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { COMPANY_COLORS, CREDIBILITY_CONFIG, type TopicOverview, type CompanySummary } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { RefreshCw, ChevronLeft, ExternalLink, ChevronDown, ChevronUp } from "lucide-react";

function stripMarkdown(text: string): string {
  return text
    .replace(/#{1,6}\s*/g, "")
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/\*(.+?)\*/g, "$1")
    .replace(/>\s*/g, "")
    .replace(/[-•]\s+/g, "")
    .replace(/\n+/g, " ")
    .trim();
}

function timeAgo(iso: string | null): string {
  if (!iso) return "";
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "Just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

// ── Featured hero card (most recently updated company) ─────────────────────────
function FeaturedCard({ company, topic_id }: { company: CompanySummary; topic_id: string }) {
  const color = COMPANY_COLORS[company.company_name] ?? "#6b7280";
  const initials = company.company_name.split(" ").filter(w => w.length > 2).slice(0, 2).map(w => w[0].toUpperCase()).join("");
  const cred = CREDIBILITY_CONFIG[company.credibility_tier] ?? { label: "Unverified", variant: "secondary" as const };
  const topArticles = company.articles.slice(0, 3);

  return (
    <Link href={`/topics/${topic_id}/${company.company_id}`} className="block group">
      <div className="bg-white border border-[#e0e0e0] rounded-2xl p-6 hover:shadow-md hover:border-[#c0c0c0] transition-all duration-150">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-11 h-11 rounded-full flex items-center justify-center text-white text-sm font-bold shrink-0" style={{ background: color }}>
            {initials}
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <p className="text-base font-semibold text-gray-900 group-hover:text-black">{company.company_name}</p>
              <Badge variant={cred.variant}>{cred.label}</Badge>
              {company.articles[0]?.date && (
                <span className="text-xs text-gray-400">Latest article {company.articles.sort((a,b) => (b.date??'').localeCompare(a.date??''))[0]?.date}</span>
              )}
            </div>
            <p className="text-xs text-gray-400 mt-0.5">Most recent news · {company.articles.length} source{company.articles.length !== 1 ? "s" : ""}</p>
          </div>
        </div>

        <Separator className="mb-4" />

        {/* Full summary (plain text) */}
        <p className="text-sm text-gray-700 leading-relaxed mb-4">
          {company.summary ? stripMarkdown(company.summary) : "No summary available yet."}
        </p>

        {/* Top articles */}
        {topArticles.length > 0 && (
          <div className="space-y-2">
            {topArticles.map((a, i) => (
              <div key={i} className="flex items-start gap-2 text-xs text-gray-500">
                <ExternalLink size={11} className="shrink-0 mt-0.5 text-gray-400" />
                <span className="truncate">{a.title || a.url}</span>
                {a.date && <span className="shrink-0 text-gray-400">{a.date}</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}

// ── Small company card ─────────────────────────────────────────────────────────
function CompanyCard({ company, topic_id }: { company: CompanySummary; topic_id: string }) {
  const color = COMPANY_COLORS[company.company_name] ?? "#6b7280";
  const initials = company.company_name.split(" ").filter(w => w.length > 2).slice(0, 2).map(w => w[0].toUpperCase()).join("");
  const cred = CREDIBILITY_CONFIG[company.credibility_tier] ?? { label: "Unverified", variant: "secondary" as const };
  const domains = [...new Set(company.articles.map(a => a.source_domain).filter(Boolean))].slice(0, 2);

  return (
    <Link href={`/topics/${topic_id}/${company.company_id}`} className="block group">
      <div className="bg-white border border-[#e0e0e0] rounded-xl p-4 h-full flex flex-col gap-3 hover:border-[#c0c0c0] hover:shadow-sm transition-all duration-150">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0" style={{ background: color }}>
            {initials}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-gray-900 truncate group-hover:text-black">{company.company_name}</p>
            <Badge variant={cred.variant} className="mt-0.5">{cred.label}</Badge>
          </div>
        </div>

        <Separator />

        <p className="text-xs text-gray-500 leading-relaxed line-clamp-3 flex-1">
          {company.summary ? stripMarkdown(company.summary) : <span className="italic">No summary yet.</span>}
        </p>

        {domains.length > 0 && (
          <div className="flex gap-1.5 flex-wrap">
            {domains.map(d => (
              <span key={d} className="text-[10px] bg-gray-100 px-2 py-0.5 rounded-full text-gray-500 truncate max-w-[120px]">{d}</span>
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}

function SkeletonFeatured() {
  return (
    <div className="bg-white border border-[#e0e0e0] rounded-2xl p-6 space-y-4 animate-pulse">
      <div className="flex items-center gap-3">
        <Skeleton className="w-11 h-11 rounded-full" />
        <div className="space-y-1.5">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-3 w-24" />
        </div>
      </div>
      <Skeleton className="h-px w-full" />
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-11/12" />
      <Skeleton className="h-3 w-4/5" />
      <Skeleton className="h-3 w-3/5" />
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="bg-white border border-[#e0e0e0] rounded-xl p-4 space-y-3 animate-pulse">
      <div className="flex items-center gap-3">
        <Skeleton className="w-9 h-9 rounded-full" />
        <div className="flex-1 space-y-1.5">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-3 w-16 rounded-full" />
        </div>
      </div>
      <Skeleton className="h-px w-full" />
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-4/5" />
      <Skeleton className="h-3 w-3/5" />
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────
export default function TopicPage() {
  const { topic_id } = useParams<{ topic_id: string }>();
  const router = useRouter();

  const [topic, setTopic] = useState<TopicOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showUnverified, setShowUnverified] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const res = await api.overview();
      const found = res.topics.find(t => t.topic_id === topic_id) ?? null;
      setTopic(found);
    } catch {}
  }, [topic_id]);

  useEffect(() => {
    fetchData().finally(() => setLoading(false));
  }, [fetchData]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await api.topics.refresh(topic_id);
      const prevUpdated = topic?.last_updated ?? null;
      let tries = 0;
      const poll = async () => {
        tries++;
        const res = await api.overview().catch(() => null);
        if (res) {
          const found = res.topics.find(t => t.topic_id === topic_id);
          if (found && found.last_updated !== prevUpdated) {
            setTopic(found);
            setRefreshing(false);
            return;
          }
        }
        if (tries < 36) setTimeout(poll, 5000);
        else { await fetchData(); setRefreshing(false); }
      };
      setTimeout(poll, 5000);
    } catch {
      setRefreshing(false);
    }
  };

  // Pick the company with the most recent article date
  const allCompanies = topic?.companies ?? [];
  const latestArticleDate = (c: CompanySummary) =>
    c.articles.map(a => a.date ?? "").sort().at(-1) ?? "";
  const withSummary = allCompanies.filter(c => c.summary && c.articles.length > 0);
  const featured = withSummary.sort((a, b) =>
    latestArticleDate(b).localeCompare(latestArticleDate(a))
  )[0] ?? allCompanies[0] ?? null;

  const rest = allCompanies.filter(c => c.company_id !== featured?.company_id);
  const verifiedRest = rest.filter(c => c.credibility_tier !== "0B");
  const unverifiedRest = rest.filter(c => c.credibility_tier === "0B");

  return (
    <div className="flex flex-col flex-1 overflow-auto bg-[#f7f7f7]">
      {/* Top nav */}
      <header className="h-14 flex items-center justify-between px-6 border-b border-[#e8e8e8] bg-white shrink-0">
        <div className="flex items-center gap-3">
          <button onClick={() => router.back()} className="text-gray-400 hover:text-gray-700 transition-colors">
            <ChevronLeft size={18} />
          </button>
          {loading ? (
            <Skeleton className="h-4 w-40" />
          ) : (
            <div>
              <h1 className="text-sm font-semibold text-gray-900">{topic?.topic_name ?? "Topic"}</h1>
              <p className="text-xs text-gray-400">{topic?.companies.length ?? 10} competitors · Competitive Intelligence</p>
            </div>
          )}
        </div>
        <Button variant="ghost" size="sm" onClick={handleRefresh} disabled={refreshing || loading}>
          <RefreshCw size={13} className={refreshing ? "animate-spin" : ""} />
          {refreshing ? "Refreshing…" : "Refresh"}
        </Button>
      </header>

      <div className="flex-1 overflow-auto">
        <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">

          {/* Keyword pills */}
          {!loading && topic && topic.search_keywords.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs text-gray-400">Keywords:</span>
              {topic.search_keywords.map(kw => (
                <span key={kw} className="text-xs bg-blue-50 text-blue-600 px-2.5 py-1 rounded-full border border-blue-100">{kw}</span>
              ))}
            </div>
          )}

          {loading ? (
            <div className="space-y-6">
              <SkeletonFeatured />
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
              </div>
            </div>
          ) : !topic ? (
            <div className="text-center py-16">
              <p className="text-sm text-gray-400">Topic not found.</p>
              <Link href="/" className="text-xs text-blue-500 mt-2 inline-block hover:underline">← Back to Overview</Link>
            </div>
          ) : (
            <>
              {/* Featured: most recently updated */}
              {featured && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold tracking-widest text-gray-400 uppercase">Latest insight</p>
                  <FeaturedCard company={featured} topic_id={topic_id} />
                </div>
              )}

              {/* Rest of companies */}
              {verifiedRest.length > 0 && (
                <div className="space-y-3">
                  <p className="text-xs font-semibold tracking-widest text-gray-400 uppercase">Other competitors</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {verifiedRest.map(co => (
                      <CompanyCard key={co.company_id} company={co} topic_id={topic_id} />
                    ))}
                  </div>
                </div>
              )}

              {/* Unverified toggle */}
              {unverifiedRest.length > 0 && (
                <div>
                  <button
                    onClick={() => setShowUnverified(v => !v)}
                    className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-700 transition-colors"
                  >
                    {showUnverified ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                    {showUnverified ? "Hide" : "Show"} unverified sources ({unverifiedRest.length})
                  </button>
                  {showUnverified && (
                    <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 opacity-50">
                      {unverifiedRest.map(co => (
                        <CompanyCard key={co.company_id} company={co} topic_id={topic_id} />
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}

        </div>
      </div>
    </div>
  );
}
