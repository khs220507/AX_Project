import type { SurvivalPrediction } from "../../types";

interface Props {
  survival: SurvivalPrediction;
}

const GRADE_COLORS: Record<string, { bg: string; text: string }> = {
  "안전": { bg: "bg-green-950/50", text: "text-green-400" },
  "양호": { bg: "bg-blue-950/50", text: "text-blue-400" },
  "주의": { bg: "bg-amber-950/50", text: "text-amber-400" },
  "위험": { bg: "bg-red-950/50", text: "text-red-400" },
};

export function SurvivalCard({ survival }: Props) {
  const gc = GRADE_COLORS[survival.grade] ?? GRADE_COLORS["주의"];

  const bars = [
    { label: "1년", value: survival.survival_1yr, color: "#22c55e" },
    { label: "3년", value: survival.survival_3yr, color: "#3b82f6" },
    { label: "5년", value: survival.survival_5yr, color: "#8b5cf6" },
  ];

  return (
    <div className="space-y-3">
      {/* 등급 */}
      <div className="flex items-center justify-between">
        <span className={`text-sm font-bold px-3 py-1 rounded ${gc.bg} ${gc.text}`}>
          {survival.grade}
        </span>
        <span className="text-xs text-slate-500">
          분기 평균 폐업률 {survival.avg_quarterly_close_rate}%
        </span>
      </div>

      {/* 생존률 바 */}
      <div className="space-y-2">
        {bars.map((bar) => (
          <div key={bar.label}>
            <div className="flex justify-between text-xs mb-0.5">
              <span className="text-slate-400">{bar.label} 생존율</span>
              <span className="font-bold" style={{ color: bar.color }}>
                {bar.value}%
              </span>
            </div>
            <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${bar.value}%`,
                  backgroundColor: bar.color,
                  opacity: 0.8,
                  transition: "width 1s ease-out",
                }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* 위험/긍정 요인 */}
      <div className="grid grid-cols-2 gap-2">
        {survival.risk_factors.length > 0 && (
          <div>
            <div className="text-xs font-medium text-red-400 mb-1">위험 요인</div>
            {survival.risk_factors.slice(0, 3).map((r) => (
              <div key={r.factor} className="text-[10px] text-slate-400 py-0.5 flex items-start gap-1">
                <span className="text-red-500 shrink-0 mt-0.5">&#x25CF;</span>
                <span>{r.factor}: {r.impact}</span>
              </div>
            ))}
          </div>
        )}
        {survival.positive_factors.length > 0 && (
          <div>
            <div className="text-xs font-medium text-green-400 mb-1">긍정 요인</div>
            {survival.positive_factors.slice(0, 3).map((p) => (
              <div key={p.factor} className="text-[10px] text-slate-400 py-0.5 flex items-start gap-1">
                <span className="text-green-500 shrink-0 mt-0.5">&#x25CF;</span>
                <span>{p.factor}: {p.impact}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <p className="text-xs text-slate-500 leading-relaxed">{survival.recommendation}</p>
    </div>
  );
}
