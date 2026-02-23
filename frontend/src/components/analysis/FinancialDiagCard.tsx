import type { FinancialDiagnosis } from "../../types";
import { formatWon } from "../../utils/format";

interface Props {
  financial: FinancialDiagnosis;
}

const GRADE_STYLES: Record<string, { bg: string; text: string }> = {
  "우수": { bg: "bg-green-950/50", text: "text-green-400" },
  "양호": { bg: "bg-blue-950/50", text: "text-blue-400" },
  "보통": { bg: "bg-amber-950/50", text: "text-amber-400" },
  "주의": { bg: "bg-red-950/50", text: "text-red-400" },
};

const RENT_GRADE_STYLES: Record<string, { bg: string; text: string }> = {
  "적정": { bg: "bg-green-950/50", text: "text-green-400" },
  "주의": { bg: "bg-amber-950/50", text: "text-amber-400" },
  "과다": { bg: "bg-red-950/50", text: "text-red-400" },
};

export function FinancialDiagCard({ financial }: Props) {
  const gs = GRADE_STYLES[financial.grade] ?? GRADE_STYLES["보통"];
  const rs = RENT_GRADE_STYLES[financial.rent_grade] ?? RENT_GRADE_STYLES["주의"];

  const vsAvgColor =
    financial.vs_city_avg >= 100 ? "text-green-400" : "text-red-400";
  const vsAvgSign = financial.vs_city_avg >= 100 ? "+" : "";

  return (
    <div className="space-y-3">
      {/* 등급 + 서울 대비 */}
      <div className="flex items-center justify-between">
        <span className={`text-sm font-bold px-3 py-1 rounded ${gs.bg} ${gs.text}`}>
          {financial.grade}
        </span>
        <div className="text-right">
          <div className={`text-sm font-bold ${vsAvgColor}`}>
            {vsAvgSign}{(financial.vs_city_avg - 100).toFixed(0)}%
          </div>
          <div className="text-[10px] text-slate-500">서울 평균 대비</div>
        </div>
      </div>

      {/* 매출/원가/임대료/이익 */}
      <div className="grid grid-cols-4 gap-1.5">
        <div className="bg-blue-950/40 border border-blue-800/30 rounded-lg p-2 text-center">
          <div className="text-xs font-bold text-blue-300">
            {formatWon(financial.estimated_monthly_revenue)}
          </div>
          <div className="text-[10px] text-blue-400/70">점포당 매출</div>
        </div>
        <div className="bg-red-950/40 border border-red-800/30 rounded-lg p-2 text-center">
          <div className="text-xs font-bold text-red-300">
            {formatWon(financial.estimated_monthly_cost)}
          </div>
          <div className="text-[10px] text-red-400/70">추정 원가</div>
        </div>
        <div className="bg-amber-950/40 border border-amber-800/30 rounded-lg p-2 text-center">
          <div className="text-xs font-bold text-amber-300">
            {formatWon(financial.estimated_monthly_rent)}
          </div>
          <div className="text-[10px] text-amber-400/70 flex items-center justify-center gap-0.5">
            임대료
            <span className={`text-[9px] px-1 rounded ${rs.bg} ${rs.text}`}>
              {financial.rent_grade}
            </span>
          </div>
        </div>
        <div className="bg-green-950/40 border border-green-800/30 rounded-lg p-2 text-center">
          <div className={`text-xs font-bold ${financial.estimated_profit >= 0 ? "text-green-300" : "text-red-300"}`}>
            {formatWon(financial.estimated_profit)}
          </div>
          <div className="text-[10px] text-green-400/70">실질 이익</div>
        </div>
      </div>

      {/* 원가율 / 임대료 비율 / 수익률 / 안정성 */}
      <div className="space-y-1.5">
        <div className="flex justify-between items-center">
          <span className="text-xs text-slate-400">원가율</span>
          <div className="flex items-center gap-2">
            <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-red-500 rounded-full"
                style={{ width: `${financial.cost_ratio}%`, opacity: 0.7 }}
              />
            </div>
            <span className="text-xs font-medium text-slate-300 w-10 text-right">
              {financial.cost_ratio}%
            </span>
          </div>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-xs text-slate-400">임대료 비율</span>
          <div className="flex items-center gap-2">
            <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-amber-500 rounded-full"
                style={{ width: `${Math.min(financial.rent_ratio, 100)}%`, opacity: 0.7 }}
              />
            </div>
            <span className="text-xs font-medium text-slate-300 w-10 text-right">
              {financial.rent_ratio}%
            </span>
          </div>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-xs text-slate-400">실질 수익률</span>
          <div className="flex items-center gap-2">
            <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${financial.profit_margin >= 0 ? "bg-green-500" : "bg-red-500"}`}
                style={{ width: `${Math.max(financial.profit_margin, 0)}%`, opacity: 0.7 }}
              />
            </div>
            <span className="text-xs font-medium text-slate-300 w-10 text-right">
              {financial.profit_margin}%
            </span>
          </div>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-xs text-slate-400">매출 안정성</span>
          <div className="flex items-center gap-2">
            <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded-full"
                style={{ width: `${financial.stability_score}%`, opacity: 0.7 }}
              />
            </div>
            <span className="text-xs font-medium text-slate-300 w-10 text-right">
              {financial.stability_score}점
            </span>
          </div>
        </div>
      </div>

      {/* 서울 평균 비교 */}
      <div className="bg-slate-800/30 rounded-lg p-2">
        <div className="flex justify-between text-xs">
          <span className="text-slate-500">이 상권 점포 매출</span>
          <span className="text-slate-300 font-medium">{formatWon(financial.sales_per_store)}</span>
        </div>
        <div className="flex justify-between text-xs mt-1">
          <span className="text-slate-500">서울 평균 점포 매출</span>
          <span className="text-slate-300 font-medium">{formatWon(financial.city_avg_per_store)}</span>
        </div>
      </div>

      <p className="text-xs text-slate-500 leading-relaxed">{financial.recommendation}</p>
    </div>
  );
}
