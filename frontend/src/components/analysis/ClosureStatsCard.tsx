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
import type { ClosureStats } from "../../types";

interface Props {
  stats: ClosureStats;
}

export function ClosureStatsCard({ stats }: Props) {
  const chartData = stats.quarterly.map((q) => ({
    quarter: q.quarter.replace(/^\d{2}/, ""),
    개업: q.open_stores,
    폐업: q.closed_stores,
    폐업률: q.close_rate,
  }));

  return (
    <div className="space-y-3">
      {/* 요약 카드 */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-blue-950/50 border border-blue-800/30 rounded-lg p-2.5 text-center">
          <div className="text-lg font-bold text-blue-300">
            {stats.total_stores}
          </div>
          <div className="text-xs text-blue-400/70">전체 점포</div>
        </div>
        <div className="bg-green-950/50 border border-green-800/30 rounded-lg p-2.5 text-center">
          <div className="text-lg font-bold text-green-400">
            {stats.open_stores}
          </div>
          <div className="text-xs text-green-400/70">
            개업 ({stats.open_rate}%)
          </div>
        </div>
        <div className="bg-red-950/50 border border-red-800/30 rounded-lg p-2.5 text-center">
          <div className="text-lg font-bold text-red-400">
            {stats.closed_stores}
          </div>
          <div className="text-xs text-red-400/70">
            폐업 ({stats.close_rate}%)
          </div>
        </div>
      </div>

      {/* 순증감 */}
      <div className="flex items-center justify-center gap-2 text-sm">
        <span className="text-slate-500">최근 8분기 순증감</span>
        <span
          className={`font-bold ${
            stats.net_change >= 0 ? "text-green-400" : "text-red-400"
          }`}
        >
          {stats.net_change >= 0 ? "+" : ""}
          {stats.net_change}개
        </span>
      </div>

      {/* 분기별 차트 */}
      {chartData.length > 0 && (
        <ResponsiveContainer width="100%" height={160}>
          <BarChart
            data={chartData}
            margin={{ top: 5, right: 5, left: 5, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="quarter" tick={{ fontSize: 10, fill: "#94a3b8" }} stroke="#334155" />
            <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} width={30} stroke="#334155" />
            <Tooltip
              formatter={(value: number, name: string) => [
                `${value}개`,
                name,
              ]}
              contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "8px", color: "#e2e8f0" }}
            />
            <Bar dataKey="개업" radius={[2, 2, 0, 0]}>
              {chartData.map((_, i) => (
                <Cell key={i} fill="#22c55e" fillOpacity={0.8} />
              ))}
            </Bar>
            <Bar dataKey="폐업" radius={[2, 2, 0, 0]}>
              {chartData.map((_, i) => (
                <Cell key={i} fill="#ef4444" fillOpacity={0.8} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
