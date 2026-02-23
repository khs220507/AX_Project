import type { BusinessStrategy } from "../../types";

interface Props {
  strategy: BusinessStrategy;
}

const PRIORITY_COLORS: Record<string, { bg: string; text: string }> = {
  high: { bg: "bg-red-950/40", text: "text-red-400" },
  medium: { bg: "bg-amber-950/40", text: "text-amber-400" },
  low: { bg: "bg-green-950/40", text: "text-green-400" },
};

const CATEGORY_ICONS: Record<string, string> = {
  "마케팅": "M",
  "운영": "O",
  "채널": "C",
  "재무": "F",
  "경쟁": "X",
  "리스크": "R",
};

export function StrategyCard({ strategy }: Props) {
  const { swot, strategies } = strategy;

  return (
    <div className="space-y-3">
      {/* SWOT 매트릭스 */}
      <div className="grid grid-cols-2 gap-1.5">
        <div className="bg-blue-950/40 border border-blue-800/30 rounded-lg p-2">
          <div className="text-[10px] font-bold text-blue-400 mb-1">S 강점</div>
          {swot.strengths.slice(0, 3).map((s) => (
            <div key={s} className="text-[10px] text-slate-400 leading-tight py-0.5">{s}</div>
          ))}
          {swot.strengths.length === 0 && <div className="text-[10px] text-slate-600">-</div>}
        </div>
        <div className="bg-red-950/40 border border-red-800/30 rounded-lg p-2">
          <div className="text-[10px] font-bold text-red-400 mb-1">W 약점</div>
          {swot.weaknesses.slice(0, 3).map((w) => (
            <div key={w} className="text-[10px] text-slate-400 leading-tight py-0.5">{w}</div>
          ))}
          {swot.weaknesses.length === 0 && <div className="text-[10px] text-slate-600">-</div>}
        </div>
        <div className="bg-green-950/40 border border-green-800/30 rounded-lg p-2">
          <div className="text-[10px] font-bold text-green-400 mb-1">O 기회</div>
          {swot.opportunities.slice(0, 3).map((o) => (
            <div key={o} className="text-[10px] text-slate-400 leading-tight py-0.5">{o}</div>
          ))}
          {swot.opportunities.length === 0 && <div className="text-[10px] text-slate-600">-</div>}
        </div>
        <div className="bg-amber-950/40 border border-amber-800/30 rounded-lg p-2">
          <div className="text-[10px] font-bold text-amber-400 mb-1">T 위협</div>
          {swot.threats.slice(0, 3).map((t) => (
            <div key={t} className="text-[10px] text-slate-400 leading-tight py-0.5">{t}</div>
          ))}
          {swot.threats.length === 0 && <div className="text-[10px] text-slate-600">-</div>}
        </div>
      </div>

      {/* 전략 카드 목록 */}
      <div className="space-y-1.5">
        {strategies.map((s, i) => {
          const pc = PRIORITY_COLORS[s.priority] ?? PRIORITY_COLORS.medium;
          const icon = CATEGORY_ICONS[s.category] ?? "?";
          return (
            <div
              key={i}
              className="flex items-start gap-2 p-2 rounded-lg border border-slate-700/50 bg-slate-800/30"
            >
              <div className="w-6 h-6 rounded-md bg-slate-700/50 flex items-center justify-center text-[10px] font-bold text-slate-400 shrink-0">
                {icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-semibold text-slate-200">{s.title}</span>
                  <span className={`text-[10px] px-1 py-0 rounded ${pc.bg} ${pc.text}`}>
                    {s.priority === "high" ? "높음" : s.priority === "medium" ? "중간" : "낮음"}
                  </span>
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5 leading-relaxed">
                  {s.description}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 종합 요약 */}
      <div className="bg-slate-800/30 rounded-lg p-2.5">
        <div className="text-[10px] text-slate-500 leading-relaxed">{strategy.summary}</div>
      </div>
    </div>
  );
}
