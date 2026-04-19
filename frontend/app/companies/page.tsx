"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/header";
import { Badge } from "@/components/ui/badge";
import { COMPANY_COLORS } from "@/lib/types";

const QUARTERS = ["Q1", "Q2", "Q3", "Q4"];
const YEARS = [2020, 2021, 2022, 2023, 2024, 2025];

function CoverageMatrix() {
  const [indexed, setIndexed] = useState<Record<string, string[]>>({});

  useEffect(() => {
    fetch("/api/scraper/status")
      .then(r => r.json())
      .then(d => setIndexed(d.indexed ?? {}))
      .catch(() => {});
  }, []);

  const companies = Object.keys(indexed);
  if (companies.length === 0) return null;

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-border">
        <p className="text-xs font-medium text-muted-foreground">Transcript Coverage Matrix</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left px-4 py-2 text-muted-foreground font-medium w-44">Company</th>
              {YEARS.map(y => (
                <th key={y} colSpan={4} className="text-center px-2 py-2 text-muted-foreground font-medium border-l border-border/50">
                  {y}
                </th>
              ))}
            </tr>
            <tr className="border-b border-border bg-secondary/20">
              <th className="px-4 py-1" />
              {YEARS.map(y =>
                QUARTERS.map(q => (
                  <th key={`${y}-${q}`} className="text-center px-1 py-1 text-muted-foreground/60 font-normal">{q}</th>
                ))
              )}
            </tr>
          </thead>
          <tbody>
            {companies.map(co => {
              const periods = new Set(indexed[co]);
              const color = COMPANY_COLORS[co] ?? "#888";
              return (
                <tr key={co} className="border-b border-border/50 hover:bg-secondary/10">
                  <td className="px-4 py-2 font-medium text-foreground/80 whitespace-nowrap">{co}</td>
                  {YEARS.map(y =>
                    QUARTERS.map(q => {
                      const has = periods.has(`${y} ${q}`);
                      return (
                        <td key={`${y}-${q}`} className="text-center px-1 py-2">
                          {has
                            ? <span className="inline-block w-4 h-4 rounded-sm" style={{ background: `${color}40`, border: `1px solid ${color}60` }} />
                            : <span className="inline-block w-4 h-4 rounded-sm bg-border/30" />
                          }
                        </td>
                      );
                    })
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const COMPANIES = [
  {
    name: "Elevance Health",
    ticker: "ELV",
    formerly: "Anthem Inc.",
    description: "One of the largest health insurers in the US. Operates Blue Cross Blue Shield plans in 14 states. Known for Carelon health services division.",
    segments: ["Commercial", "Medicare", "Medicaid", "Carelon Services"],
    docs: 24,
    years: "2020–2025",
  },
  {
    name: "UnitedHealth Group",
    ticker: "UNH",
    formerly: null,
    description: "Largest US health insurer by revenue. Operates UnitedHealthcare (insurance) and Optum (health services, PBM, analytics). Strongest Medicare Advantage position.",
    segments: ["UnitedHealthcare", "OptumHealth", "OptumRx", "OptumInsight"],
    docs: 24,
    years: "2020–2025",
  },
  {
    name: "Aetna (CVS Health)",
    ticker: "CVS",
    formerly: null,
    description: "Acquired by CVS Health in 2018. Operates as part of CVS integrated health model with pharmacy, MinuteClinic, and insurance. Strong employer and Medicare segments.",
    segments: ["Health Benefits", "Pharmacy & Consumer Wellness", "Health Services"],
    docs: 24,
    years: "2020–2024",
  },
  {
    name: "Cigna Group",
    ticker: "CI",
    formerly: null,
    description: "Global health services company with strong employer-sponsored insurance and pharmacy benefits (Evernorth). Significant international presence and behavioral health focus.",
    segments: ["Evernorth Health Services", "Cigna Healthcare", "International"],
    docs: 0,
    years: "via SEC EDGAR",
  },
  {
    name: "Humana",
    ticker: "HUM",
    formerly: null,
    description: "Leader in Medicare Advantage with ~20% market share. Also operates Centerwell primary care clinics and home health services. Strong military/TRICARE contract.",
    segments: ["Insurance", "CenterWell", "Medicare Advantage", "Medicaid"],
    docs: 0,
    years: "via SEC EDGAR",
  },
  {
    name: "Centene",
    ticker: "CNC",
    formerly: null,
    description: "Largest Medicaid managed care organization in the US. Operates WellCare for Medicare and has significant ACA marketplace presence through Ambetter brand.",
    segments: ["Medicaid", "Medicare", "Commercial", "International"],
    docs: 0,
    years: "via SEC EDGAR",
  },
  {
    name: "Molina Healthcare",
    ticker: "MOH",
    formerly: null,
    description: "Focused exclusively on government-sponsored health care programs. Operates Medicaid, Medicare, and Marketplace plans in 19 states.",
    segments: ["Medicaid", "Medicare", "Marketplace"],
    docs: 0,
    years: "via SEC EDGAR",
  },
  {
    name: "Oscar Health",
    ticker: "OSCR",
    formerly: null,
    description: "Technology-first health insurer focused on ACA Marketplace and Medicare Advantage. Known for concierge care teams, digital-first member experience, and +Oscar platform.",
    segments: ["Individual & Family", "Small Group", "Medicare Advantage", "+Oscar Platform"],
    docs: 0,
    years: "via SEC EDGAR",
  },
];

export default function CompaniesPage() {
  return (
    <div className="flex flex-col flex-1 overflow-auto">
      <Header title="Companies" subtitle="Competitor profiles · Earnings call coverage matrix" />
      <div className="flex-1 p-6 space-y-6">

        {/* Company cards */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {COMPANIES.map(co => (
            <div key={co.name} className="bg-card border border-border rounded-lg p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-3 h-3 rounded-full shrink-0" style={{ background: COMPANY_COLORS[co.name] ?? "#888" }} />
                <div>
                  <p className="text-sm font-semibold text-foreground">{co.name}</p>
                  <p className="text-[11px] text-muted-foreground">{co.ticker}{co.formerly ? ` · formerly ${co.formerly}` : ""}</p>
                </div>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed mb-3">{co.description}</p>
              <div className="flex flex-wrap gap-1 mb-3">
                {co.segments.map(s => (
                  <Badge key={s} variant="outline" className="text-[10px]">{s}</Badge>
                ))}
              </div>
              <div className="flex gap-4 text-xs">
                <span className="text-muted-foreground">{co.docs} transcripts</span>
                <span className="text-muted-foreground">{co.years}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Coverage matrix — live from API */}
        <CoverageMatrix />

      </div>
    </div>
  );
}
