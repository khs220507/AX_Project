from pydantic import BaseModel


class AreaSummary(BaseModel):
    code: str
    name: str
    district: str
    dong: str
    area_type: str
    lat: float
    lng: float
    score: int


class AreaDetail(AreaSummary):
    floating_pop: int
    resident_pop: int
    worker_pop: int
    district_type: str = ""          # 업무지구/주택지구/혼합지구
    worker_resident_ratio: float = 0 # 직장/상주 비율
    household: int = 0               # 세대수
    store_count: int
    avg_monthly_sales: int


class ScoreBreakdownItem(BaseModel):
    category: str
    score: int
    rank_pct: float  # 상위 N%


class BizRecommendation(BaseModel):
    business_code: str
    business_name: str
    score: int
    avg_sales_citywide: int
    reason: str


class ClosureStats(BaseModel):
    total_stores: int
    open_stores: int
    closed_stores: int
    open_rate: float       # 개업률 (%)
    close_rate: float      # 폐업률 (%)
    net_change: int        # 순증감
    quarterly: list[dict] = []  # 분기별 개폐업 추이


class DistrictTypeInfo(BaseModel):
    district_type: str          # 업무지구/주택지구/혼합지구
    worker_pop: int
    resident_pop: int
    household: int
    ratio: float


class AnalysisResponse(BaseModel):
    area_code: str
    area_name: str
    business_type: str
    total_score: int
    grade: str
    breakdown: list[ScoreBreakdownItem]
    recommendation: str
    district_info: DistrictTypeInfo | None = None
    closure_stats: ClosureStats | None = None
    missing_biz_recommendations: list[BizRecommendation] = []


class PredictRequest(BaseModel):
    area_code: str
    business_type: str


class QuarterlyPrediction(BaseModel):
    quarter: str
    predicted: int
    lower: int
    upper: int


class PredictFactor(BaseModel):
    name: str
    impact: str


class PredictResponse(BaseModel):
    area_code: str
    business_type: str
    current_quarter_sales: int
    predicted_next_quarter: int
    growth_rate: float
    confidence_lower: int
    confidence_upper: int
    quarterly_predictions: list[QuarterlyPrediction]
    factors: list[PredictFactor]


class QuarterlyTrend(BaseModel):
    quarter: str
    sales: int
    floating_pop: int
    resident_pop: int
    worker_pop: int
    store_count: int


class TrendsResponse(BaseModel):
    area_code: str
    area_name: str
    business_type: str
    quarters: list[QuarterlyTrend]


class BusinessTypeSales(BaseModel):
    business_type: str
    avg_sales: int
    store_count: int


class CompareArea(BaseModel):
    area: AreaSummary
    breakdown: list[ScoreBreakdownItem]
    top_businesses: list[BusinessTypeSales]


class CompareResponse(BaseModel):
    areas: list[CompareArea]


# ── 전국 (Nationwide) 모델 ──

class RegionInfo(BaseModel):
    code: str
    name: str
    short: str
    is_seoul: bool = False
    center: list[float] = []
    zoom: int = 10


class CategoryCount(BaseModel):
    category: str
    count: int
    percentage: float


class StoreSummary(BaseModel):
    total_stores: int
    category_distribution: list[CategoryCount]
    top_businesses: list[str]


class DongSummary(BaseModel):
    adong_cd: str
    adong_nm: str
    sido_cd: str
    signgu_nm: str
    total_stores: int
    target_stores: int
    density_score: int


# ── 뉴스 트렌드 모델 ──

class NewsArticle(BaseModel):
    title: str
    link: str
    source: str
    pub_date: str
    sentiment: str  # 긍정/부정/중립
    sentiment_score: float


class NewsKeyword(BaseModel):
    keyword: str
    count: int


class NewsTrendResponse(BaseModel):
    area_name: str
    query: str
    overall_score: int  # 0~100 (50=중립)
    overall_label: str  # 긍정/부정/중립
    positive_count: int
    negative_count: int
    neutral_count: int
    keywords: list[NewsKeyword]
    articles: list[NewsArticle]


class NationwideAnalysisResponse(BaseModel):
    dong_code: str
    dong_name: str
    region_name: str
    data_source: str = "SEMAS"
    total_score: int
    grade: str
    breakdown: list[ScoreBreakdownItem]
    recommendation: str
    store_summary: StoreSummary
    missing_biz_recommendations: list[BizRecommendation] = []


# ── 고급 분석 모델 ──

class TimeSlotData(BaseModel):
    time_slot: str
    population: int = 0
    sales: int = 0
    ratio: float = 0.0

class DayData(BaseModel):
    day: str
    population: int = 0
    sales: int = 0
    ratio: float = 0.0

class DemandAnalysis(BaseModel):
    hourly_population: list[TimeSlotData]
    hourly_sales: list[TimeSlotData]
    daily_population: list[DayData]
    daily_sales: list[DayData]
    peak_time: str
    peak_day: str
    weekend_ratio: float
    recommendation: str

class AgeGroup(BaseModel):
    age_group: str
    population: int = 0
    ratio: float = 0.0

class AgeSales(BaseModel):
    age_group: str
    sales: int = 0

class CustomerProfile(BaseModel):
    male_ratio: float
    female_ratio: float
    age_distribution: list[AgeGroup]
    main_customer: str
    sales_by_age: list[AgeSales]
    male_sales: int = 0
    female_sales: int = 0
    recommendation: str

class DeliveryOptimization(BaseModel):
    delivery_score: int
    night_demand_ratio: float
    night_sales_ratio: float = 0.0
    weekend_demand_ratio: float
    delivery_store_ratio: float
    delivery_competition: int
    recommended_times: list[str]
    recommendation: str

class BizTrend(BaseModel):
    business_code: str
    business_name: str
    growth_rate: float
    current_sales: int
    store_count: int

class CompetitionItem(BaseModel):
    business_name: str
    store_count: int
    competition: int
    per_store_sales: int

class MenuTrend(BaseModel):
    growing_businesses: list[BizTrend]
    declining_businesses: list[BizTrend]
    competition_map: list[CompetitionItem]
    recommendation: str

class RiskFactor(BaseModel):
    factor: str
    impact: str
    severity: str

class SurvivalPrediction(BaseModel):
    survival_1yr: float
    survival_3yr: float
    survival_5yr: float
    avg_quarterly_close_rate: float
    risk_factors: list[RiskFactor]
    positive_factors: list[RiskFactor]
    grade: str
    recommendation: str

class FinancialDiagnosis(BaseModel):
    sales_per_store: int
    city_avg_per_store: int
    vs_city_avg: float
    estimated_monthly_revenue: int
    estimated_monthly_cost: int
    estimated_monthly_rent: int
    estimated_profit: int
    profit_margin: float
    cost_ratio: float
    rent_ratio: float
    rent_grade: str
    stability_score: int
    grade: str
    recommendation: str

class StrategyItem(BaseModel):
    title: str
    description: str
    priority: str
    category: str

class SWOT(BaseModel):
    strengths: list[str]
    weaknesses: list[str]
    opportunities: list[str]
    threats: list[str]

class BusinessStrategy(BaseModel):
    swot: SWOT
    strategies: list[StrategyItem]
    summary: str

class BusinessTip(BaseModel):
    category: str
    title: str
    description: str
    source: str = ""

class PolicyItem(BaseModel):
    title: str
    organization: str
    category: str
    target: str
    period: str
    url: str
    is_active: bool


class PolicyResponse(BaseModel):
    total_count: int
    policies: list[PolicyItem]
    source: str
    matched_category: str


class AdvancedModelsResponse(BaseModel):
    area_code: str
    area_name: str
    business_type: str
    demand: DemandAnalysis | None = None
    customer: CustomerProfile | None = None
    delivery: DeliveryOptimization | None = None
    menu_trend: MenuTrend | None = None
    survival: SurvivalPrediction | None = None
    financial: FinancialDiagnosis | None = None
    strategy: BusinessStrategy | None = None
    tips: list[BusinessTip] = []
