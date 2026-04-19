"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/header";
import { Badge } from "@/components/ui/badge";
import { COMPANY_COLORS, type Document } from "@/lib/types";

const COMPANIES_FILTER = ["All", "Elevance Health", "UnitedHealth Group", "Aetna (CVS Health)"];
const YEARS_FILTER = ["All", "2025", "2024", "2023", "2022", "2021", "2020"];

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [company, setCompany] = useState("All");
  const [year, setYear] = useState("All");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Document | null>(null);
  const [preview, setPreview] = useState("");

  useEffect(() => {
    const params = new URLSearchParams();
    if (company !== "All") params.set("company", company);
    if (year !== "All") params.set("year", year);
    fetch(`/api/documents?${params}`)
      .then(r => r.json())
      .then(setDocs)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [company, year]);

  const filtered = docs.filter(d =>
    !search || d.filename.toLowerCase().includes(search.toLowerCase())
  );

  const loadPreview = async (doc: Document) => {
    setSelected(doc);
    try {
      const res = await fetch(`/api/documents/preview?filename=${encodeURIComponent(doc.filename)}`);
      if (res.ok) setPreview(await res.text());
    } catch { setPreview(""); }
  };

  return (
    <div className="flex flex-col flex-1 overflow-auto">
      <Header title="Documents" subtitle="Full transcript library · Browse and preview" />
      <div className="flex-1 p-6 space-y-4">

        {/* Filters */}
        <div className="flex items-center gap-3 flex-wrap">
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search filename…"
            className="text-xs px-3 py-1.5 rounded-md border border-border bg-card text-foreground placeholder:text-muted-foreground w-48 focus:outline-none focus:border-primary/50"
          />
          {COMPANIES_FILTER.map(c => (
            <button
              key={c}
              onClick={() => setCompany(c)}
              className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${company === c ? "bg-primary/20 border-primary/40 text-primary" : "border-border text-muted-foreground hover:border-primary/30"}`}
            >
              {c === "All" ? "All" : c.split(" ")[0]}
            </button>
          ))}
          <select
            value={year}
            onChange={e => setYear(e.target.value)}
            className="text-xs px-2 py-1.5 rounded-md border border-border bg-secondary text-muted-foreground"
          >
            {YEARS_FILTER.map(y => <option key={y}>{y}</option>)}
          </select>
          <span className="text-xs text-muted-foreground ml-auto">{filtered.length} documents</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Document list */}
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            <div className="px-4 py-2.5 border-b border-border">
              <p className="text-xs font-medium text-muted-foreground">Transcripts</p>
            </div>
            <div className="divide-y divide-border/50 max-h-[520px] overflow-y-auto">
              {loading
                ? <div className="px-4 py-6 text-xs text-muted-foreground">Loading…</div>
                : filtered.length === 0
                  ? <div className="px-4 py-6 text-xs text-muted-foreground">No documents found</div>
                  : filtered.map((doc, i) => (
                    <button
                      key={i}
                      onClick={() => loadPreview(doc)}
                      className={`w-full flex items-center justify-between px-4 py-3 text-left hover:bg-secondary/30 transition-colors ${selected?.filename === doc.filename ? "bg-secondary/40" : ""}`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full shrink-0" style={{ background: COMPANY_COLORS[doc.company_display] ?? "#888" }} />
                        <div>
                          <p className="text-xs font-medium text-foreground">{doc.company_display.split(" ")[0]}</p>
                          <p className="text-[11px] text-muted-foreground">{doc.period}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{doc.source_type.replace("_", " ")}</Badge>
                        <span className="text-[10px] text-muted-foreground tabular-nums">{(doc.char_count / 1000).toFixed(0)}k</span>
                      </div>
                    </button>
                  ))
              }
            </div>
          </div>

          {/* Preview */}
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
              <p className="text-xs font-medium text-muted-foreground">
                {selected ? `${selected.company_display} · ${selected.period}` : "Select a document to preview"}
              </p>
              {selected && <span className="text-[10px] text-muted-foreground">{(selected.char_count / 1000).toFixed(0)}k chars</span>}
            </div>
            <div className="p-4 max-h-[520px] overflow-y-auto">
              {preview
                ? <pre className="text-xs text-muted-foreground leading-relaxed whitespace-pre-wrap font-mono">{preview.slice(0, 3000)}{preview.length > 3000 ? "\n\n[… truncated]" : ""}</pre>
                : <p className="text-xs text-muted-foreground/50 italic">No preview available</p>
              }
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
