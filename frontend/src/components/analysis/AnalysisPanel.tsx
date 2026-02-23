import { useState, useEffect } from "react";
import { ScoreGauge } from "./ScoreGauge";
import { RadarBreakdown } from "./RadarBreakdown";
import { SalesTrendChart } from "./SalesTrendChart";
import { PredictionChart } from "./PredictionChart";
import { StoreCategoryChart } from "./StoreCategoryChart";
import { ClosureStatsCard } from "./ClosureStatsCard";
import { NewsTrendCard } from "./NewsTrendCard";
import { CustomerProfileCard } from "./CustomerProfileCard";
import { DemandChart } from "./DemandChart";
import { DeliveryOptCard } from "./DeliveryOptCard";
import { MenuTrendCard } from "./MenuTrendCard";
import { SurvivalCard } from "./SurvivalCard";
import { FinancialDiagCard } from "./FinancialDiagCard";
import { StrategyCard } from "./StrategyCard";
import { BusinessTipsCard } from "./BusinessTipsCard";
import { PolicyCard } from "./PolicyCard";
import { useAnalysis } from "../../hooks/useAnalysis";
import { usePrediction } from "../../hooks/usePrediction";
import { useAdvancedModels } from "../../hooks/useAdvancedModels";
import { useNationwideAnalysis } from "../../hooks/useNationwideAnalysis";
import { useNewsTrend } from "../../hooks/useNewsTrend";
import { fetchPolicies } from "../../api/client";
import { formatWon } from "../../utils/format";
import { gradeToColor, scoreToColor } from "../../utils/colors";
import type { AreaSummary, DongSummary, PolicyResponse } from "../../types";

const SEOUL_TABS = [
  { key: "overview", label: "종합" },
  { key: "customer", label: "고객·수요" },
  { key: "sales", label: "매출·재무" },
  { key: "survival", label: "생존·경쟁" },
  { key: "strategy", label: "전략" },
  { key: "policy", label: "정책" },
  { key: "tips", label: "경영팁" },
] as const;

type SeoulTab = (typeof SEOUL_TABS)[number]["key"];

interface Props {
  isSeoul: boolean;
  selectedSido: string;
  selectedArea: AreaSummary | null;
  selectedDong: DongSummary | null;
  businessType: string;
}

export function AnalysisPanel({
  isSeoul,
  selectedSido,
  selectedArea,
  selectedDong,
  businessType,
}: Props) {
  const [activeTab, setActiveTab] = useState<SeoulTab>("overview");

  // 서울 훅
  const { analysis, trends, loading: analysisLoading } = useAnalysis(
    isSeoul ? selectedArea?.code ?? null : null,
    businessType
  );
  const { prediction, loading: predictionLoading } = usePrediction(
    isSeoul ? selectedArea?.code ?? null : null,
    businessType
  );
  const { models, loading: modelsLoading } = useAdvancedModels(
    isSeoul ? selectedArea?.code ?? null : null,
    businessType
  );

  // 비서울 훅
  const { analysis: nwAnalysis, loading: nwLoading } = useNationwideAnalysis(
    selectedSido,
    !isSeoul ? selectedDong?.adong_cd ?? null : null,
    businessType
  );

  // 뉴스 트렌드
  const newsAreaName = isSeoul
    ? selectedArea?.name ?? null
    : selectedDong?.adong_nm ?? null;
  const { news, loading: newsLoading } = useNewsTrend(
    newsAreaName,
    analysis?.business_type
  );

  // 정책 정보
  const [policies, setPolicies] = useState<PolicyResponse | null>(null);
  const [policiesLoading, setPoliciesLoading] = useState(false);

  useEffect(() => {
    if (!businessType) {
      setPolicies(null);
      return;
    }
    let cancelled = false;
    setPoliciesLoading(true);
    fetchPolicies(businessType)
      .then((data) => { if (!cancelled) setPolicies(data); })
      .catch(() => { if (!cancelled) setPolicies(null); })
      .finally(() => { if (!cancelled) setPoliciesLoading(false); });
    return () => { cancelled = true; };
  }, [businessType]);

  // 빈 상태
  if (!selectedArea && !selectedDong) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-500">
        <svg
          className="w-16 h-16 mb-4 text-slate-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
        <p className="text-sm">
          {isSeoul ? "지도에서 상권을 클릭하여" : "지도에서 행정동을 클릭하여"}
        </p>
        <p className="text-sm">분석 결과를 확인하세요</p>
      </div>
    );
  }

  // ── 서울 모드 ──
  if (isSeoul && selectedArea) {
    const loading = analysisLoading || predictionLoading;

    return (
      <div className="flex flex-col h-full analysis-panel">
        {/* 상권 헤더 (고정) */}
        <div className="shrink-0 bg-[#111a2e] rounded-xl border border-slate-700/50 p-4 mb-3">
          <div className="flex items-center justify-between mb-1">
            <div>
              <h2 className="text-lg font-bold text-slate-100">
                {selectedArea.name}
              </h2>
              <p className="text-sm text-slate-400">
                {selectedArea.district} / {selectedArea.area_type}
              </p>
            </div>
            {analysis && (
              <span
                className="text-xs font-semibold px-2 py-1 rounded"
                style={{
                  backgroundColor: gradeToColor(analysis.grade) + "20",
                  color: gradeToColor(analysis.grade),
                }}
              >
                {analysis.grade}
              </span>
            )}
          </div>
          {analysis && (
            <p className="text-xs text-slate-500 leading-relaxed line-clamp-2">
              {analysis.recommendation}
            </p>
          )}
        </div>

        {/* 탭 바 (고정) */}
        <div className="shrink-0 flex gap-1 mb-3 bg-[#0d1321] rounded-lg p-1">
          {SEOUL_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 text-xs font-medium py-1.5 px-1 rounded-md transition-all ${
                activeTab === tab.key
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* 로딩 */}
        {loading && (
          <div className="text-center py-8">
            <div className="inline-block w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-slate-500 mt-2">분석 중...</p>
          </div>
        )}

        {/* 탭 컨텐츠 (스크롤) */}
        <div className="flex-1 overflow-y-auto space-y-4 min-h-0">
          {/* ── 종합 탭 ── */}
          {activeTab === "overview" && (
            <>
              {analysis && !loading && (
                <Card title="입지점수">
                  <ScoreGauge score={analysis.total_score} grade={analysis.grade} />
                </Card>
              )}

              {analysis?.district_info && analysis.district_info.district_type !== "데이터없음" && !loading && (
                <Card title="지구유형">
                  <div className="flex items-center gap-3 mb-3">
                    <span className={`px-3 py-1.5 rounded-full text-sm font-bold ${
                      analysis.district_info.district_type === "업무지구"
                        ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                        : analysis.district_info.district_type === "주택지구"
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                        : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                    }`}>
                      {analysis.district_info.district_type}
                    </span>
                    <span className="text-xs text-slate-500">
                      직주비율 {analysis.district_info.ratio}:1
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="bg-slate-800/50 rounded p-2">
                      <div className="text-xs text-slate-500">직장인구</div>
                      <div className="text-sm font-semibold text-slate-200">{analysis.district_info.worker_pop.toLocaleString()}명</div>
                    </div>
                    <div className="bg-slate-800/50 rounded p-2">
                      <div className="text-xs text-slate-500">상주인구</div>
                      <div className="text-sm font-semibold text-slate-200">{analysis.district_info.resident_pop.toLocaleString()}명</div>
                    </div>
                    <div className="bg-slate-800/50 rounded p-2">
                      <div className="text-xs text-slate-500">세대수</div>
                      <div className="text-sm font-semibold text-slate-200">{analysis.district_info.household.toLocaleString()}</div>
                    </div>
                  </div>
                </Card>
              )}

              {analysis && !loading && (
                <Card title="항목별 분석">
                  <RadarBreakdown breakdown={analysis.breakdown} />
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    {analysis.breakdown.map((b) => (
                      <div
                        key={b.category}
                        className="flex justify-between text-xs px-2 py-1 bg-slate-800/50 rounded"
                      >
                        <span className="text-slate-400">{b.category}</span>
                        <span className="font-medium text-slate-200">{b.score}점</span>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {analysis?.closure_stats && !loading && (
                <Card title="개폐업 현황">
                  <ClosureStatsCard stats={analysis.closure_stats} />
                </Card>
              )}
            </>
          )}

          {/* ── 고객·수요 탭 ── */}
          {activeTab === "customer" && (
            <>
              {models?.customer && !modelsLoading && (
                <Card title="고객 특성 분석">
                  <CustomerProfileCard customer={models.customer} />
                </Card>
              )}

              {models?.demand && !modelsLoading && (
                <Card title="수요 예측">
                  <DemandChart demand={models.demand} />
                </Card>
              )}

              {modelsLoading && <LoadingCard text="고객·수요 분석 중..." />}
            </>
          )}

          {/* ── 매출·재무 탭 ── */}
          {activeTab === "sales" && (
            <>
              {trends && !loading && (
                <Card title={`매출 트렌드 (${analysis?.business_type ?? ""})`}>
                  <SalesTrendChart quarters={trends.quarters} />
                </Card>
              )}

              {prediction && trends && !loading && (
                <Card title="매출 예측">
                  {prediction.predicted_next_quarter > 0 && (
                    <div className="flex items-baseline gap-2 mb-3">
                      <span className="text-xl font-bold text-amber-500">
                        {formatWon(prediction.predicted_next_quarter)}
                      </span>
                      <span
                        className={`text-sm font-medium ${
                          prediction.growth_rate >= 0 ? "text-green-400" : "text-red-400"
                        }`}
                      >
                        {prediction.growth_rate >= 0 ? "+" : ""}
                        {prediction.growth_rate}%
                      </span>
                    </div>
                  )}
                  <PredictionChart
                    prediction={prediction}
                    historicalQuarters={trends.quarters}
                  />
                </Card>
              )}

              {models?.financial && !modelsLoading && (
                <Card title="재무 진단">
                  <FinancialDiagCard financial={models.financial} />
                </Card>
              )}

              {(loading || modelsLoading) && !trends && !models?.financial && (
                <LoadingCard text="매출·재무 분석 중..." />
              )}
            </>
          )}

          {/* ── 생존·경쟁 탭 ── */}
          {activeTab === "survival" && (
            <>
              {models?.survival && !modelsLoading && (
                <Card title="생존 예측">
                  <SurvivalCard survival={models.survival} />
                </Card>
              )}

              {models?.menu_trend && !modelsLoading && (
                <Card title="메뉴 트렌드">
                  <MenuTrendCard menuTrend={models.menu_trend} />
                </Card>
              )}

              {news && !newsLoading && (
                <Card title="뉴스 트렌드">
                  <NewsTrendCard news={news} />
                </Card>
              )}
              {newsLoading && <LoadingCard text="NLP 분석 중..." />}
              {modelsLoading && !models?.survival && <LoadingCard text="생존·경쟁 분석 중..." />}
            </>
          )}

          {/* ── 전략 탭 ── */}
          {activeTab === "strategy" && (
            <>
              {models?.strategy && !modelsLoading && (
                <Card title="경영전략 추천">
                  <StrategyCard strategy={models.strategy} />
                </Card>
              )}

              {models?.delivery && !modelsLoading && (
                <Card title="배달 최적화">
                  <DeliveryOptCard delivery={models.delivery} />
                </Card>
              )}

              {analysis &&
                analysis.missing_biz_recommendations.length > 0 &&
                !loading && (
                  <BizRecommendationSection
                    recommendations={analysis.missing_biz_recommendations}
                    showSales={true}
                  />
                )}

              {modelsLoading && !models?.strategy && <LoadingCard text="전략 분석 중..." />}
            </>
          )}

          {/* ── 정책 탭 ── */}
          {activeTab === "policy" && (
            <>
              {policies && !policiesLoading && (
                <Card title="정부 지원정책">
                  <PolicyCard policies={policies} />
                </Card>
              )}
              {policiesLoading && <LoadingCard text="정책 정보 조회 중..." />}
              {!policies && !policiesLoading && (
                <div className="text-center py-8 text-sm text-slate-500">
                  정책 정보를 불러올 수 없습니다
                </div>
              )}
            </>
          )}

          {/* ── 경영팁 탭 ── */}
          {activeTab === "tips" && (
            <>
              {models?.tips && models.tips.length > 0 && !modelsLoading && (
                <Card title="맞춤 경영팁">
                  <BusinessTipsCard
                    tips={models.tips}
                    businessType={models.business_type}
                  />
                </Card>
              )}

              {modelsLoading && <LoadingCard text="경영팁 분석 중..." />}
            </>
          )}
        </div>
      </div>
    );
  }

  // ── 비서울 모드 (스크롤 유지) ──
  if (!isSeoul && selectedDong) {
    return (
      <div className="space-y-4 analysis-panel">
        {/* 동 헤더 */}
        <div className="bg-[#111a2e] rounded-xl border border-slate-700/50 p-4">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h2 className="text-lg font-bold text-slate-100">
                {selectedDong.adong_nm.replace(/.*?(시|도)\s/, "")}
              </h2>
              <p className="text-sm text-slate-400">
                {selectedDong.signgu_nm} / {selectedDong.total_stores}개 점포
              </p>
            </div>
            {nwAnalysis && (
              <span
                className="text-xs font-semibold px-2 py-1 rounded"
                style={{
                  backgroundColor: gradeToColor(nwAnalysis.grade) + "20",
                  color: gradeToColor(nwAnalysis.grade),
                }}
              >
                {nwAnalysis.grade}
              </span>
            )}
          </div>
          {nwAnalysis && (
            <p className="text-sm text-slate-400 leading-relaxed">
              {nwAnalysis.recommendation}
            </p>
          )}
          <div className="mt-2 px-3 py-2 bg-amber-950/30 border border-amber-700/30 rounded-lg">
            <p className="text-xs text-amber-400">
              점포 데이터 기반 분석입니다. 매출/유동인구/예측 분석은 서울
              지역에서만 제공됩니다.
            </p>
          </div>
        </div>

        {nwLoading && (
          <div className="text-center py-8">
            <div className="inline-block w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-slate-500 mt-2">분석 중...</p>
          </div>
        )}

        {nwAnalysis && !nwLoading && (
          <Card title="상권 점수">
            <ScoreGauge score={nwAnalysis.total_score} grade={nwAnalysis.grade} />
          </Card>
        )}

        {nwAnalysis && !nwLoading && (
          <Card title="항목별 분석">
            <RadarBreakdown breakdown={nwAnalysis.breakdown} />
            <div className="grid grid-cols-2 gap-2 mt-2">
              {nwAnalysis.breakdown.map((b) => (
                <div
                  key={b.category}
                  className="flex justify-between text-xs px-2 py-1 bg-slate-800/50 rounded"
                >
                  <span className="text-slate-400">{b.category}</span>
                  <span className="font-medium text-slate-200">{b.score}점</span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {nwAnalysis &&
          nwAnalysis.store_summary.category_distribution.length > 0 &&
          !nwLoading && (
            <Card title="업종 분포">
              <StoreCategoryChart
                categories={nwAnalysis.store_summary.category_distribution}
              />
            </Card>
          )}

        {news && !newsLoading && (
          <Card title="뉴스 트렌드">
            <NewsTrendCard news={news} />
          </Card>
        )}
        {newsLoading && <LoadingCard text="NLP 분석 중..." />}

        {nwAnalysis &&
          nwAnalysis.missing_biz_recommendations.length > 0 &&
          !nwLoading && (
            <BizRecommendationSection
              recommendations={nwAnalysis.missing_biz_recommendations}
              showSales={false}
            />
          )}
      </div>
    );
  }

  return (
    <div className="text-center py-8">
      <div className="inline-block w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      <p className="text-sm text-slate-500 mt-2">분석 중...</p>
    </div>
  );
}

// ── 공통 카드 래퍼 ──
function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-[#111a2e] rounded-xl border border-slate-700/50 p-4">
      <h3 className="text-sm font-semibold text-slate-200 mb-2">{title}</h3>
      {children}
    </div>
  );
}

function LoadingCard({ text }: { text: string }) {
  return (
    <div className="bg-[#111a2e] rounded-xl border border-slate-700/50 p-4">
      <div className="text-center py-4">
        <div className="inline-block w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-xs text-slate-500 mt-1">{text}</p>
      </div>
    </div>
  );
}

// ── 공통 미진출 업종 추천 컴포넌트 ──
function BizRecommendationSection({
  recommendations,
  showSales,
}: {
  recommendations: {
    business_code: string;
    business_name: string;
    score: number;
    avg_sales_citywide: number;
    reason: string;
  }[];
  showSales: boolean;
}) {
  return (
    <Card title="이 지역에 없는 업종 추천">
      <p className="text-xs text-slate-500 mb-3">
        현재 상권에 미진출된 업종 중 창업 유망 업종
      </p>
      <div className="space-y-2">
        {recommendations.map((rec, i) => {
          const color = scoreToColor(rec.score);
          return (
            <div
              key={rec.business_code}
              className="flex items-center gap-3 p-2.5 rounded-lg border border-slate-700/50 bg-slate-800/50"
            >
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0"
                style={{ backgroundColor: color }}
              >
                {i + 1}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-200">
                    {rec.business_name}
                  </span>
                  <span
                    className="text-xs font-medium px-1.5 py-0.5 rounded"
                    style={{ backgroundColor: color + "20", color }}
                  >
                    {rec.score}점
                  </span>
                </div>
                <div className="text-xs text-slate-500 mt-0.5">{rec.reason}</div>
                {showSales && rec.avg_sales_citywide > 0 && (
                  <div className="text-xs text-slate-500 mt-0.5">
                    서울 평균 매출: {formatWon(rec.avg_sales_citywide)}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
