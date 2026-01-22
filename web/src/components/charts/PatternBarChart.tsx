"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { PatternStats } from "@/lib/analytics";

const PATTERN_COLORS: Record<string, string> = {
  AI_QUALITY_FAILURES: "#ef4444",
  AI_WALL_LOOPING: "#f97316",
  IGNORING_CONTEXT: "#eab308",
  RESPONSE_DELAYS: "#3b82f6",
  PREMATURE_CLOSURE: "#8b5cf6",
  P1_SEV1_MISHANDLING: "#ec4899",
};

const PATTERN_LABELS: Record<string, string> = {
  AI_QUALITY_FAILURES: "AI Quality",
  AI_WALL_LOOPING: "AI Wall/Loop",
  IGNORING_CONTEXT: "Ignoring Context",
  RESPONSE_DELAYS: "Response Delays",
  PREMATURE_CLOSURE: "Premature Close",
  P1_SEV1_MISHANDLING: "P1/SEV1 Mishandled",
};

interface PatternBarChartProps {
  data: PatternStats[];
}

export function PatternBarChart({ data }: PatternBarChartProps) {
  const chartData = data.map((d) => ({
    ...d,
    name: PATTERN_LABELS[d.pattern] || d.pattern,
    fill: PATTERN_COLORS[d.pattern] || "#6b7280",
  }));

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis type="number" stroke="#9ca3af" fontSize={12} />
          <YAxis
            type="category"
            dataKey="name"
            stroke="#9ca3af"
            fontSize={12}
            width={95}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#18181b",
              border: "1px solid #3f3f46",
              borderRadius: "8px",
            }}
            labelStyle={{ color: "#fafafa" }}
            itemStyle={{ color: "#a1a1aa" }}
            formatter={(value) => [`${value} tickets`, "Count"]}
          />
          <Bar dataKey="count" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
