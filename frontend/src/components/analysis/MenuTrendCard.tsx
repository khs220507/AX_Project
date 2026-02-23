import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from "recharts";
import type { MenuTrend } from "../../types";
import { formatWon } from "../../utils/format";

interface Props {
  menuTrend: MenuTrend;
}

export function MenuTrendCard({ menuTrend }: Props) {
  const growthData = [
    ...menuTrend.growing_businesses.slice(0, 4).map((b) => ({
      name: b.business_name.replace("음식점", "").replace("전문점", ""),
      성장률: b.growth_rate,
      color: "#22c55e",
    })),
    ...menuTrend.declining_businesses.slice(0, 3).map((b) => ({
      name: b.business_name.replace("음식점", "").replace("전문점", ""),
      성장률: b.growth_rate,
      color: "#ef4444",
    })),
  ];

  return (
    <div className="space-y-3">
      {/* 성장/쇠퇴 업종 차트 */}
      {growthData.length > 0 && (
        <div>
          <div className="text-xs font-medium text-slate-500 mb-1.5">업종별 성장률</div>
          <ResponsiveContainer width="100%" height={140}>
            <BarChart data={growthData} layout="vertical" margin={{ top: 0, right: 10, left: 5, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis type="number" tick={{ fontSize: 9, fill: "#94a3b8" }} stroke="#334155" unit="%" />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} width={50} stroke="#334155" />
              <Tooltip
                contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "8px", color: "#e2e8f0" }}
                formatter={(value: number) => [`${value}%`, "성장률"]}
              />
              <Bar dataKey="성장률" radius={[0, 3, 3, 0]}>
                {growthData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} fillOpacity={0.8} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* 경쟁도 맵 */}
      {menuTrend.competition_map.length > 0 && (
        <div>
          <div className="text-xs font-medium text-slate-500 mb-1.5">업종별 경쟁도</div>
          <div className="space-y-1">
            {menuTrend.competition_map.slice(0, 6).map((c) => {
              const maxComp = Math.max(...menuTrend.competition_map.map((x) => x.competition), 1);
              const width = Math.max(10, (c.competition / maxComp) * 100);
              return (
                <div key={c.business_name} className="flex items-center gap-2 text-xs">
                  <span className="w-16 text-slate-400 shrink-0 truncate">
                    {c.business_name.replace("음식점", "").replace("전문점", "")}
                  </span>
                  <div className="flex-1 bg-slate-800/50 rounded-full h-3 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-blue-600 to-blue-400"
                      style={{ width: `${width}%`, transition: "width 0.5s" }}
                    />
                  </div>
                  <span className="text-slate-500 w-8 text-right">{c.competition}</span>
                  {c.per_store_sales > 0 && (
                    <span className="text-slate-600 text-[10px] w-16 text-right">
                      {formatWon(c.per_store_sales)}/점포
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <p className="text-xs text-slate-500 leading-relaxed">{menuTrend.recommendation}</p>
    </div>
  );
}
