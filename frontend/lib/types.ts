export interface Citation {
  ref: number;
  company: string;
  period: string;
  source_type: string;
  filename: string;
  score: number;
  snippet: string;
}

export interface StatsResponse {
  total_documents: number;
  total_companies: number;
  last_updated: string;
  companies: string[];
}

export interface SearchResponse {
  answer: string;
  sources: string[];
  chunks_used: number;
}

export interface TrendPoint {
  date: string;
  value: number;
  company?: string;
  topic?: string;
}

// ── Topic types ────────────────────────────────────────────────────────────────

export interface Topic {
  topic_id: string;
  topic_name: string;
  search_keywords: string[];
  created_at: string;
  last_updated: string | null;
}

export interface TopicArticle {
  title: string;
  url: string;
  date: string;
  source?: string;
  credibility_score: number;
  credibility_tier: string;
  credibility_label: string;
  source_domain: string;
}

export interface CompanySummary {
  company_id: string;
  company_name: string;
  summary: string;
  articles: TopicArticle[];
  last_updated: string | null;
  credibility_tier: string;
  credibility_label: string;
}

export interface TopicOverview {
  topic_id: string;
  topic_name: string;
  search_keywords: string[];
  last_updated: string | null;
  companies: CompanySummary[];
}

export interface OverviewResponse {
  topics: TopicOverview[];
  last_refreshed: string | null;
}

// ── Constants ──────────────────────────────────────────────────────────────────

export const COMPANY_COLORS: Record<string, string> = {
  "Elevance Health": "#1e40af",
  "UnitedHealth Group": "#15803d",
  "Aetna (CVS Health)": "#b91c1c",
  "Cigna Group": "#7e22ce",
  "Humana": "#c2410c",
  "Centene": "#0369a1",
  "Molina Healthcare": "#047857",
  "Oscar Health": "#be185d",
  "Kaiser Permanente": "#92400e",
  "Blue Cross (Anthem CA)": "#1d4ed8",
  "All": "#6b7280",
};

export const TOPIC_LIST = [
  "AI & Technology",
  "Medicare & Medicaid",
  "Pharmacy Benefits",
  "Mental Health",
  "Cost & Premiums",
  "Network & Access",
  "Preventive Care",
  "Regulatory & Policy",
  "Financial Performance",
  "Member Experience",
];

export const CREDIBILITY_CONFIG: Record<string, { label: string; variant: "success" | "default" | "warning" | "secondary" | "outline" }> = {
  "1":  { label: "Official",   variant: "success" },
  "2":  { label: "Verified",   variant: "default" },
  "3":  { label: "General",    variant: "warning" },
  "0B": { label: "Unverified", variant: "secondary" },
};
