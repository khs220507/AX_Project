import type { DeliveryOptimization } from "../../types";
import { scoreToColor } from "../../utils/colors";

interface Props {
  delivery: DeliveryOptimization;
}

export function DeliveryOptCard({ delivery }: Props) {
  const color = scoreToColor(delivery.delivery_score);

  return (
    <div className="space-y-3">
      {/* 배달 적합도 점수 */}
      <div className="flex items-center gap-4">
        <div className="relative w-16 h-16">
          <svg viewBox="0 0 100 100" className="w-full h-full">
            <circle cx="50" cy="50" r="42" fill="none" stroke="#1e293b" strokeWidth="8" />
            <circle
              cx="50" cy="50" r="42" fill="none" stroke={color} strokeWidth="8"
              strokeDasharray={2 * Math.PI * 42}
              strokeDashoffset={2 * Math.PI * 42 * (1 - delivery.delivery_score / 100)}
              strokeLinecap="round"
              transform="rotate(-90 50 50)"
              style={{ transition: "stroke-dashoffset 1s ease-out" }}
            />
            <text x="50" y="55" textAnchor="middle" fontSize="20" fontWeight="bold" fill="#e2e8f0">
              {delivery.delivery_score}
            </text>
          </svg>
        </div>
        <div className="flex-1">
          <div className="text-sm font-semibold text-slate-200">배달 적합도</div>
          <div className="text-xs text-slate-500 mt-0.5">
            {delivery.delivery_score >= 70
              ? "배달 수요 매우 높음"
              : delivery.delivery_score >= 50
              ? "배달 수요 적당"
              : "오프라인 방문 중심"}
          </div>
        </div>
      </div>

      {/* 지표 그리드 */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-slate-800/50 rounded-lg p-2 text-center">
          <div className="text-sm font-bold text-amber-400">{delivery.night_demand_ratio}%</div>
          <div className="text-[10px] text-slate-500">야간 수요</div>
        </div>
        <div className="bg-slate-800/50 rounded-lg p-2 text-center">
          <div className="text-sm font-bold text-violet-400">{delivery.weekend_demand_ratio}%</div>
          <div className="text-[10px] text-slate-500">주말 수요</div>
        </div>
        <div className="bg-slate-800/50 rounded-lg p-2 text-center">
          <div className="text-sm font-bold text-cyan-400">{delivery.delivery_store_ratio}%</div>
          <div className="text-[10px] text-slate-500">배달업종 비율</div>
        </div>
        <div className="bg-slate-800/50 rounded-lg p-2 text-center">
          <div className="text-sm font-bold text-slate-300">{delivery.delivery_competition}개</div>
          <div className="text-[10px] text-slate-500">경쟁 점포</div>
        </div>
      </div>

      {/* 추천 배달 시간 */}
      {delivery.recommended_times.length > 0 && (
        <div>
          <div className="text-xs font-medium text-slate-500 mb-1">추천 배달 시간</div>
          <div className="flex gap-1.5">
            {delivery.recommended_times.map((t, i) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded-full text-xs font-medium"
                style={{
                  backgroundColor: i === 0 ? "#1e3a5f" : "#1e293b",
                  color: i === 0 ? "#60a5fa" : "#94a3b8",
                }}
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      <p className="text-xs text-slate-500 leading-relaxed">{delivery.recommendation}</p>
    </div>
  );
}
