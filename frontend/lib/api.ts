import type {
  StatsResponse, SearchResponse, TrendPoint,
  Topic, TopicOverview, OverviewResponse,
} from "./types";

const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

async function del<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export const api = {
  // Existing
  stats: () => get<StatsResponse>("/stats"),
  search: (question: string, filters?: Record<string, string>, history?: unknown[]) =>
    post<SearchResponse>("/search", { question, filters, history }),
  trends: (topic: string, companies?: string[]) =>
    get<TrendPoint[]>(
      `/trends?topic=${encodeURIComponent(topic)}${companies?.map(c => `&companies=${encodeURIComponent(c)}`).join("") ?? ""}`
    ),

  // Overview
  overview: () => get<OverviewResponse>("/overview"),

  // Topics CRUD
  topics: {
    list: () => get<{ topics: Topic[] }>("/topics"),
    create: (topic_name: string, search_keywords: string[]) =>
      post<Topic>("/topics", { topic_name, search_keywords }),
    delete: (topic_id: string) => del<{ deleted: string }>(`/topics/${topic_id}`),
    refresh: (topic_id: string) =>
      post<{ status: string; topic_id: string }>(`/topics/${topic_id}/refresh`, {}),
    summary: (topic_id: string) =>
      get<{ topic_id: string; companies: Record<string, unknown> }>(`/topics/${topic_id}/summary`),
  },

  // Dedup stats
  dedupStats: () => get<{ checked: number; duplicates_caught: number; last_run: string | null }>("/dedup/stats"),
};
