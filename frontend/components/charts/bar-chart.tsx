"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LabelList,
} from "recharts";

interface SimpleBarChartProps {
  data: { label: string; value: number; color?: string }[];
  color?: string;
  valueFormatter?: (v: number) => string;
  horizontal?: boolean;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomTooltip = ({ active, payload, label, valueFormatter }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-xs shadow-md">
      <p className="text-gray-400 mb-0.5">{label}</p>
      <p className="text-gray-800 font-semibold">
        {valueFormatter ? valueFormatter(payload[0].value) : payload[0].value}
      </p>
    </div>
  );
};

function HorizontalBars({ data, color, valueFormatter }: SimpleBarChartProps) {
  const max = Math.max(...data.map(d => d.value));
  return (
    <div className="flex flex-col justify-around h-full py-1 gap-2">
      {data.map((d, i) => {
        const pct = max > 0 ? (d.value / max) * 100 : 0;
        const barColor = d.color ?? color ?? "#2563eb";
        return (
          <div key={i} className="flex items-center gap-3">
            <span className="text-[11px] text-gray-400 w-[110px] shrink-0 truncate text-right leading-tight">
              {d.label}
            </span>
            <div className="flex-1 relative h-[18px] flex items-center">
              <div className="absolute inset-0 rounded-full bg-gray-100" />
              <div
                className="absolute left-0 h-full rounded-full"
                style={{
                  width: `${pct}%`,
                  background: `linear-gradient(90deg, ${barColor}70 0%, ${barColor} 100%)`,
                  boxShadow: `0 0 10px ${barColor}33`,
                }}
              />
            </div>
            <span className="text-[11px] font-medium text-gray-500 w-16 shrink-0 text-right tabular-nums">
              {valueFormatter ? valueFormatter(d.value) : d.value}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function SimpleBarChart({ data, color = "#2563eb", valueFormatter, horizontal }: SimpleBarChartProps) {
  if (horizontal) return <HorizontalBars data={data} color={color} valueFormatter={valueFormatter} />;

  const mapped = data.map((d, i) => ({
    name: d.label,
    value: d.value,
    color: d.color ?? color,
    gradId: `ci-grad-${i}`,
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={mapped} margin={{ top: 22, right: 4, left: -10, bottom: 0 }} barCategoryGap="38%">
        <defs>
          {mapped.map(d => (
            <linearGradient key={d.gradId} id={d.gradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={d.color} stopOpacity={1} />
              <stop offset="100%" stopColor={d.color} stopOpacity={0.25} />
            </linearGradient>
          ))}
        </defs>
        <XAxis dataKey="name" tick={{ fill: "#8a96b0", fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: "#8a96b0", fontSize: 10 }} axisLine={false} tickLine={false} width={36} />
        <Tooltip content={<CustomTooltip valueFormatter={valueFormatter} />} cursor={{ fill: "rgba(61,90,241,0.04)", radius: 4 } as object} />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          <LabelList
            dataKey="value"
            position="top"
            formatter={(v: unknown) => (valueFormatter ? valueFormatter(v as number) : String(v))}
            style={{ fill: "#8a96b0", fontSize: 10 }}
          />
          {mapped.map((entry, i) => <Cell key={i} fill={`url(#${entry.gradId})`} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
