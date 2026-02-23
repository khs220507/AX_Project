import type { PolicyResponse } from "../../types";

interface Props {
  policies: PolicyResponse;
}

const CATEGORY_STYLES: Record<string, { icon: string; bg: string; text: string }> = {
  "자금": { icon: "W", bg: "bg-green-950/50", text: "text-green-400" },
  "교육": { icon: "E", bg: "bg-blue-950/50", text: "text-blue-400" },
  "컨설팅": { icon: "C", bg: "bg-purple-950/50", text: "text-purple-400" },
  "디지털": { icon: "D", bg: "bg-cyan-950/50", text: "text-cyan-400" },
  "재기": { icon: "R", bg: "bg-amber-950/50", text: "text-amber-400" },
  "기타": { icon: "G", bg: "bg-slate-800", text: "text-slate-400" },
};

export function PolicyCard({ policies }: Props) {
  const sourceLabel = policies.source === "bizinfo" ? "기업마당 실시간" : "주요 상시 지원사업";

  return (
    <div className="space-y-3">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="text-xs text-slate-500">
          {policies.matched_category} 업종 관련 정책 <span className="text-slate-400 font-medium">{policies.total_count}건</span>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">
          {sourceLabel}
        </span>
      </div>

      {/* 정책 목록 */}
      <div className="space-y-2">
        {policies.policies.map((p, i) => {
          const cs = CATEGORY_STYLES[p.category] ?? CATEGORY_STYLES["기타"];
          return (
            <a
              key={i}
              href={p.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block bg-slate-800/40 border border-slate-700/30 rounded-lg p-2.5 hover:bg-slate-800/60 transition-colors"
            >
              <div className="flex items-start gap-2">
                {/* 카테고리 아이콘 */}
                <span className={`flex-shrink-0 w-6 h-6 rounded flex items-center justify-center text-[10px] font-bold ${cs.bg} ${cs.text}`}>
                  {cs.icon}
                </span>

                <div className="flex-1 min-w-0">
                  {/* 제목 */}
                  <div className="text-xs font-medium text-slate-200 leading-snug line-clamp-1">
                    {p.title}
                  </div>

                  {/* 주관기관 + 카테고리 */}
                  <div className="flex items-center gap-1.5 mt-1">
                    <span className="text-[10px] text-slate-500">{p.organization}</span>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded ${cs.bg} ${cs.text}`}>
                      {p.category}
                    </span>
                    {p.is_active && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-green-950/50 text-green-400">
                        신청가능
                      </span>
                    )}
                  </div>

                  {/* 대상 + 기간 */}
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    {p.target} | {p.period}
                  </div>
                </div>

                {/* 외부 링크 아이콘 */}
                <span className="flex-shrink-0 text-slate-600 text-xs mt-0.5">&#8599;</span>
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}
