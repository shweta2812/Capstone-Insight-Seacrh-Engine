"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  COMPANY_COLORS, CREDIBILITY_CONFIG,
  type TopicOverview, type CompanySummary, type TopicArticle,
} from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { ChevronLeft, ExternalLink } from "lucide-react";

// ── Simple markdown renderer ───────────────────────────────────────────────────
function MarkdownBlock({ text }: { text: string }) {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;

  const renderInline = (s: string) => {
    // Bold **text**
    const parts = s.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((p, idx) =>
      p.startsWith("**") && p.endsWith("**")
        ? <strong key={idx}>{p.slice(2, -2)}</strong>
        : p
    );
  };

  while (i < lines.length) {
    const line = lines[i];
    if (/^#{1,3}\s/.test(line)) {
      elements.push(
        <p key={i} className="text-sm font-semibold text-foreground mt-3 mb-1 first:mt-0">
          {renderInline(line.replace(/^#{1,3}\s/, ""))}
        </p>
      );
    } else if (/^[-•*]\s/.test(line)) {
      elements.push(
        <p key={i} className="text-sm text-foreground leading-relaxed pl-3">
          {"· "}{renderInline(line.replace(/^[-•*]\s/, ""))}
        </p>
      );
    } else if (/^>\s/.test(line)) {
      elements.push(
        <p key={i} className="text-sm text-muted-foreground border-l-2 border-primary/40 pl-3 italic leading-relaxed">
          {renderInline(line.replace(/^>\s/, ""))}
        </p>
      );
    } else if (line.trim() === "" || line.startsWith("---")) {
      elements.push(<div key={i} className="h-2" />);
    } else {
      elements.push(
        <p key={i} className="text-sm text-foreground leading-relaxed">
          {renderInline(line)}
        </p>
      );
    }
    i++;
  }
  return <div className="space-y-1">{elements}</div>;
}

// ── Article row ────────────────────────────────────────────────────────────────
function ArticleRow({ article }: { article: TopicArticle }) {
  const cred = CREDIBILITY_CONFIG[String(article.credibility_tier)] ?? { label: "Unverified", variant: "secondary" as const };

  return (
    <div className="flex items-start gap-3 py-3">
      <div className="flex-1 min-w-0 space-y-1">
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-sm text-foreground hover:text-primary hover:underline font-medium"
        >
          {article.title || article.url}
          <ExternalLink size={11} className="shrink-0 opacity-50" />
        </a>
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant={cred.variant}>{cred.label}</Badge>
          {article.source_domain && (
            <span className="text-[11px] text-muted-foreground bg-secondary px-2 py-0.5 rounded-full">
              {article.source_domain}
            </span>
          )}
          {article.date && (
            <span className="text-[11px] text-muted-foreground">{article.date}</span>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Company chip ───────────────────────────────────────────────────────────────
function CompanyChip({ co, topic_id, active }: { co: CompanySummary; topic_id: string; active: boolean }) {
  const color = COMPANY_COLORS[co.company_name] ?? "#6b7280";
  const initials = co.company_name
    .split(" ")
    .filter(w => w.length > 2)
    .slice(0, 2)
    .map(w => w[0].toUpperCase())
    .join("");

  return (
    <Link
      href={`/topics/${topic_id}/${co.company_id}`}
      className={`shrink-0 flex items-center gap-2 px-3 py-2 rounded-xl border transition-all ${
        active
          ? "border-primary/50 bg-primary/5"
          : "border-border bg-card hover:border-primary/30 hover:bg-secondary/50"
      }`}
    >
      <div
        className="w-6 h-6 rounded-full flex items-center justify-center text-white text-[10px] font-bold shrink-0"
        style={{ background: color }}
      >
        {initials}
      </div>
      <span className="text-xs text-foreground whitespace-nowrap">{co.company_name.split(" ")[0]}</span>
    </Link>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────
export default function CompanyTopicPage() {
  const { topic_id, company_id } = useParams<{ topic_id: string; company_id: string }>();
  const router = useRouter();

  const [topic, setTopic] = useState<TopicOverview | null>(null);
  const [company, setCompany] = useState<CompanySummary | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const res = await api.overview();
      const t = res.topics.find(t => t.topic_id === topic_id) ?? null;
      setTopic(t);
      setCompany(t?.companies.find(c => c.company_id === company_id) ?? null);
    } catch {}
  }, [topic_id, company_id]);

  useEffect(() => {
    fetchData().finally(() => setLoading(false));
  }, [fetchData]);

  const color = COMPANY_COLORS[company?.company_name ?? ""] ?? "#6b7280";
  const initials = (company?.company_name ?? "")
    .split(" ")
    .filter(w => w.length > 2)
    .slice(0, 2)
    .map(w => w[0].toUpperCase())
    .join("");

  // Sort articles: credibility_score desc → date desc
  const sortedArticles = [...(company?.articles ?? [])].sort((a, b) => {
    if (b.credibility_score !== a.credibility_score) return b.credibility_score - a.credibility_score;
    return b.date.localeCompare(a.date);
  });

  const otherCompanies = topic?.companies.filter(c => c.company_id !== company_id) ?? [];

  return (
    <div className="flex flex-col flex-1 overflow-auto">
      {/* Top nav */}
      <header className="h-14 flex items-center justify-between px-6 border-b border-border bg-white shrink-0 shadow-sm">
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={() => router.back()}
            className="text-muted-foreground hover:text-foreground transition-colors shrink-0"
          >
            <ChevronLeft size={18} />
          </button>
          {loading ? (
            <Skeleton className="h-4 w-48" />
          ) : (
            <div className="flex items-center gap-2 min-w-0">
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center text-white text-[10px] font-bold shrink-0"
                style={{ background: color }}
              >
                {initials}
              </div>
              <span className="text-sm font-semibold text-foreground truncate">
                {company?.company_name ?? "Company"}
              </span>
              {topic && (
                <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full shrink-0">
                  {topic.topic_name}
                </span>
              )}
            </div>
          )}
        </div>
        <Link
          href={`/topics/${topic_id}`}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors shrink-0 ml-3"
        >
          ← {topic?.topic_name ?? "Back"}
        </Link>
      </header>

      <div className="flex-1 p-6 space-y-6 max-w-4xl mx-auto w-full">

        {loading ? (
          <div className="space-y-4">
            <Skeleton className="h-5 w-48" />
            <Skeleton className="h-24 w-full rounded-xl" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-4/5" />
            <Skeleton className="h-3 w-3/5" />
          </div>
        ) : !company ? (
          <div className="text-center py-16">
            <p className="text-sm text-muted-foreground">No data found for this company and topic.</p>
            <Link href={`/topics/${topic_id}`} className="text-xs text-primary mt-2 inline-block hover:underline">
              ← Back to {topic?.topic_name}
            </Link>
          </div>
        ) : (
          <>
            {/* AI Summary */}
            <section className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">AI Summary</p>
              <div className="bg-secondary/40 border border-border rounded-xl px-5 py-4">
                {company.summary
                  ? <MarkdownBlock text={company.summary} />
                  : <p className="text-sm text-muted-foreground italic">No summary available. Refresh this topic to generate insights.</p>
                }
                {company.last_updated && (
                  <p className="text-[11px] text-muted-foreground/60 mt-3">
                    Generated {new Date(company.last_updated).toLocaleString("en-US", {
                      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
                    })}
                  </p>
                )}
              </div>
            </section>

            <Separator />

            {/* Articles */}
            <section className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Sources ({sortedArticles.length})
              </p>
              {sortedArticles.length === 0 ? (
                <p className="text-sm text-muted-foreground py-4 italic">No articles found yet.</p>
              ) : (
                <div className="divide-y divide-border">
                  {sortedArticles.map((a, i) => (
                    <ArticleRow key={i} article={a} />
                  ))}
                </div>
              )}
            </section>

            <Separator />

            {/* Other companies chip row */}
            {otherCompanies.length > 0 && (
              <section className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  View another competitor on this topic
                </p>
                <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
                  {otherCompanies.map(co => (
                    <CompanyChip key={co.company_id} co={co} topic_id={topic_id} active={false} />
                  ))}
                </div>
              </section>
            )}
          </>
        )}

      </div>
    </div>
  );
}
