import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { CategoryCount } from "../../types";

interface Props {
  categories: CategoryCount[];
}

export function StoreCategoryChart({ categories }: Props) {
  const data = categories.slice(0, 8).map((c) => ({
    name: c.category,
    count: c.count,
    pct: c.percentage,
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ left: 10, right: 20, top: 5, bottom: 5 }}
      >
        <XAxis type="number" tick={{ fontSize: 11, fill: "#94a3b8" }} stroke="#334155" />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fontSize: 11, fill: "#94a3b8" }}
          width={80}
          stroke="#334155"
        />
        <Tooltip
          formatter={(v: number, _name: string, entry: { payload: { pct: number } }) => [
            `${v}개 (${entry.payload.pct}%)`,
            "점포수",
          ]}
        />
        <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
