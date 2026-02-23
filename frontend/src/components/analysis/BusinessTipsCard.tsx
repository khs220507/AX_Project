import type { BusinessTip } from "../../types";

interface Props {
  tips: BusinessTip[];
  businessType: string;
}

const CATEGORY_STYLES: Record<string, { icon: string; bg: string; text: string; border: string }> = {
  "고객관리": { icon: "👥", bg: "bg-blue-950/40", text: "text-blue-400", border: "border-blue-800/30" },
  "운영효율": { icon: "⚙️", bg: "bg-emerald-950/40", text: "text-emerald-400", border: "border-emerald-800/30" },
  "마케팅": { icon: "📢", bg: "bg-purple-950/40", text: "text-purple-400", border: "border-purple-800/30" },
  "매출향상": { icon: "📈", bg: "bg-amber-950/40", text: "text-amber-400", border: "border-amber-800/30" },
  "리스크관리": { icon: "🛡️", bg: "bg-red-950/40", text: "text-red-400", border: "border-red-800/30" },
  "트렌드": { icon: "🔥", bg: "bg-orange-950/40", text: "text-orange-400", border: "border-orange-800/30" },
  "배달전략": { icon: "🛵", bg: "bg-cyan-950/40", text: "text-cyan-400", border: "border-cyan-800/30" },
  "재무관리": { icon: "💰", bg: "bg-yellow-950/40", text: "text-yellow-400", border: "border-yellow-800/30" },
};

const DEFAULT_STYLE = { icon: "💡", bg: "bg-slate-800/40", text: "text-slate-400", border: "border-slate-700/30" };

const SOURCE_LABELS: Record<string, string> = {
  base: "업종 기본",
  generic: "일반 경영",
  customer_analysis: "고객 분석",
  demand_analysis: "수요 분석",
  delivery_analysis: "배달 분석",
  financial_analysis: "재무 분석",
  survival_analysis: "생존 분석",
};

export function BusinessTipsCard({ tips, businessType }: Props) {
  // 카테고리별 그룹핑
  const grouped = tips.reduce<Record<string, BusinessTip[]>>((acc, tip) => {
    (acc[tip.category] ??= []).push(tip);
    return acc;
  }, {});

  const categories = Object.keys(grouped);

  return (
    <div className="space-y-3">
      {/* 헤더 */}
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs text-slate-500">
          {businessType} 맞춤 경영팁 {tips.length}건
        </span>
      </div>

      {/* 카테고리별 */}
      {categories.map((cat) => {
        const style = CATEGORY_STYLES[cat] ?? DEFAULT_STYLE;
        const catTips = grouped[cat];
        return (
          <div key={cat}>
            <div className="flex items-center gap-1.5 mb-1.5">
              <span className="text-sm">{style.icon}</span>
              <span className={`text-xs font-bold ${style.text}`}>{cat}</span>
              <span className="text-[10px] text-slate-600">({catTips.length})</span>
            </div>
            <div className="space-y-1.5">
              {catTips.map((tip, i) => (
                <div
                  key={i}
                  className={`${style.bg} border ${style.border} rounded-lg p-2.5`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-xs font-semibold text-slate-200">
                      {tip.title}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800/60 text-slate-500 shrink-0">
                      {SOURCE_LABELS[tip.source] ?? tip.source}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed mt-1">
                    {tip.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {tips.length === 0 && (
        <div className="text-center py-4">
          <p className="text-xs text-slate-500">경영팁을 준비 중입니다...</p>
        </div>
      )}
    </div>
  );
}
