"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface TicketDistributionChartProps {
  data: { patternCount: number; ticketCount: number }[];
}

export function TicketDistributionChart({ data }: TicketDistributionChartProps) {
  const chartData = data.map((d) => ({
    name: d.patternCount === 0 ? "No issues" : `${d.patternCount} pattern${d.patternCount > 1 ? "s" : ""}`,
    tickets: d.ticketCount,
    patternCount: d.patternCount,
  }));

  return (
    <div className="h-[250px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} />
          <YAxis stroke="#9ca3af" fontSize={12} />
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
          <Bar
            dataKey="tickets"
            fill="#3b82f6"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
