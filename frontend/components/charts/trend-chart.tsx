"use client";

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";

type DataPoint = Record<string, string | number>;

interface TrendChartProps {
  data: DataPoint[];
  lines: { key: string; label: string; color: string; yAxisId?: string }[];
  rightAxis?: boolean;
  xKey?: string;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-border rounded-lg px-3 py-2 shadow-md text-xs">
      <p className="text-muted-foreground mb-1">{label}</p>
      {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color }} className="font-medium">
          {p.name}: {p.value?.toLocaleString?.() ?? p.value}
        </p>
      ))}
    </div>
  );
};

export function TrendChart({ data, lines, rightAxis, xKey = "period" }: TrendChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 4, right: 4, left: -10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e5ef" vertical={false} />
        <XAxis
          dataKey={xKey}
          tick={{ fill: "#8a96b0", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          yAxisId="left"
          tick={{ fill: "#8a96b0", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        {rightAxis && (
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fill: "#8a96b0", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
        )}
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: "11px", color: "#8a96b0", paddingTop: "8px" }} />
        {lines.map(l => (
          <Line
            key={l.key}
            type="monotone"
            dataKey={l.key}
            name={l.label}
            stroke={l.color}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            yAxisId={l.yAxisId ?? "left"}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
