import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from "recharts";
import type { DemandAnalysis } from "../../types";

interface Props {
  demand: DemandAnalysis;
}

export function DemandChart({ demand }: Props) {
  const hourlyData = demand.hourly_population.map((h, i) => ({
    name: h.time_slot.replace("시", ""),
    유동인구: h.population,
    매출: demand.hourly_sales[i]?.sales ?? 0,
  }));

  const dailyData = demand.daily_population.map((d, i) => ({
    name: d.day,
    유동인구: d.population,
    매출: demand.daily_sales[i]?.sales ?? 0,
  }));

  return (
    <div className="space-y-4">
      {/* 피크 정보 */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-amber-950/40 border border-amber-800/30 rounded-lg p-2.5 text-center">
          <div className="text-sm font-bold text-amber-300">{demand.peak_time}</div>
          <div className="text-xs text-amber-400/70">피크 시간대</div>
        </div>
        <div className="bg-violet-950/40 border border-violet-800/30 rounded-lg p-2.5 text-center">
          <div className="text-sm font-bold text-violet-300">{demand.peak_day}요일</div>
          <div className="text-xs text-violet-400/70">피크 요일</div>
        </div>
        <div className="bg-cyan-950/40 border border-cyan-800/30 rounded-lg p-2.5 text-center">
          <div className="text-sm font-bold text-cyan-300">{demand.weekend_ratio}%</div>
          <div className="text-xs text-cyan-400/70">주말 비중</div>
        </div>
      </div>

      {/* 시간대별 차트 */}
      <div>
        <div className="text-xs font-medium text-slate-500 mb-1.5">시간대별 유동인구</div>
        <ResponsiveContainer width="100%" height={130}>
          <BarChart data={hourlyData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} stroke="#334155" />
            <YAxis tick={{ fontSize: 9, fill: "#94a3b8" }} width={35} stroke="#334155" />
            <Tooltip
              contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "8px", color: "#e2e8f0" }}
              formatter={(value: number) => [value.toLocaleString(), ""]}
            />
            <Bar dataKey="유동인구" radius={[2, 2, 0, 0]}>
              {hourlyData.map((entry, i) => (
                <Cell
                  key={i}
                  fill={entry.name === demand.peak_time.replace("시", "") ? "#f59e0b" : "#3b82f6"}
                  fillOpacity={0.8}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* 요일별 차트 */}
      <div>
        <div className="text-xs font-medium text-slate-500 mb-1.5">요일별 유동인구</div>
        <ResponsiveContainer width="100%" height={130}>
          <BarChart data={dailyData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} stroke="#334155" />
            <YAxis tick={{ fontSize: 9, fill: "#94a3b8" }} width={35} stroke="#334155" />
            <Tooltip
              contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "8px", color: "#e2e8f0" }}
              formatter={(value: number) => [value.toLocaleString(), ""]}
            />
            <Bar dataKey="유동인구" radius={[2, 2, 0, 0]}>
              {dailyData.map((entry, i) => (
                <Cell
                  key={i}
                  fill={i >= 5 ? "#a855f7" : "#6366f1"}
                  fillOpacity={0.8}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <p className="text-xs text-slate-500 leading-relaxed">{demand.recommendation}</p>
    </div>
  );
}
