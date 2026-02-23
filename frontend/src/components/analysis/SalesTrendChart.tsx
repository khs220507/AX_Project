import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { QuarterlyTrend } from "../../types";
import { formatWon } from "../../utils/format";

interface Props {
  quarters: QuarterlyTrend[];
}

export function SalesTrendChart({ quarters }: Props) {
  if (!quarters.length) {
    return (
      <div className="text-center text-slate-500 py-8 text-sm">
        매출 데이터가 없습니다
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={quarters} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis
          dataKey="quarter"
          tick={{ fontSize: 11, fill: "#94a3b8" }}
          tickFormatter={(v: string) => v.replace(/^\d{2}/, "")}
          stroke="#334155"
        />
        <YAxis
          tick={{ fontSize: 11, fill: "#94a3b8" }}
          tickFormatter={(v: number) => formatWon(v)}
          width={65}
          stroke="#334155"
        />
        <Tooltip
          formatter={(v: number) => [formatWon(v), "매출"]}
          labelFormatter={(l: string) => `${l} 분기`}
        />
        <Line
          type="monotone"
          dataKey="sales"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
