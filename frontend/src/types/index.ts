export interface AreaSummary {
  code: string;
  name: string;
  district: string;
  dong: string;
  area_type: string;
  lat: number;
  lng: number;
  score: number;
}

export interface AreaDetail extends AreaSummary {
  floating_pop: number;
  resident_pop: number;
  worker_pop: number;
  store_count: number;
  avg_monthly_sales: number;
}

export interface ScoreBreakdownItem {
  category: string;
  score: number;
  rank_pct: number;
}

export interface BizRecommendation {
  business_code: string;
  business_name: string;
  score: number;
  avg_sales_citywide: number;
  reason: string;
}

export interface ClosureQuarter {
  quarter: string;
  total_stores: number;
  open_stores: number;
  closed_stores: number;
  close_rate: number;
}

export interface ClosureStats {
  total_stores: number;
  open_stores: number;
  closed_stores: number;
  open_rate: number;
  close_rate: number;
  net_change: number;
  quarterly: ClosureQuarter[];
}

export interface DistrictTypeInfo {
  district_type: string;
  worker_pop: number;
  resident_pop: number;
  household: number;
  ratio: number;
}

export interface AnalysisResponse {
  area_code: string;
  area_name: string;
  business_type: string;
  total_score: number;
  grade: string;
  breakdown: ScoreBreakdownItem[];
  recommendation: string;
  district_info: DistrictTypeInfo | null;
  closure_stats: ClosureStats | null;
  missing_biz_recommendations: BizRecommendation[];
}

// ── 뉴스 트렌드 ──

export interface NewsArticle {
  title: string;
  link: string;
  source: string;
  pub_date: string;
  sentiment: string;
  sentiment_score: number;
}

export interface NewsKeyword {
  keyword: string;
  count: number;
}

export interface NewsTrendResponse {
  area_name: string;
  query: string;
  overall_score: number;
  overall_label: string;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  keywords: NewsKeyword[];
  articles: NewsArticle[];
}

export interface PredictRequest {
  area_code: string;
  business_type: string;
}

export interface QuarterlyPrediction {
  quarter: string;
  predicted: number;
  lower: number;
  upper: number;
}

export interface PredictFactor {
  name: string;
  impact: string;
}

export interface PredictResponse {
  area_code: string;
  business_type: string;
  current_quarter_sales: number;
  predicted_next_quarter: number;
  growth_rate: number;
  confidence_lower: number;
  confidence_upper: number;
  quarterly_predictions: QuarterlyPrediction[];
  factors: PredictFactor[];
}

export interface QuarterlyTrend {
  quarter: string;
  sales: number;
  floating_pop: number;
  resident_pop: number;
  worker_pop: number;
  store_count: number;
}

export interface TrendsResponse {
  area_code: string;
  area_name: string;
  business_type: string;
  quarters: QuarterlyTrend[];
}

export interface BusinessType {
  code: string;
  name: string;
}

export const BUSINESS_TYPES: BusinessType[] = [
  { code: "CS100001", name: "한식음식점" },
  { code: "CS100002", name: "중식음식점" },
  { code: "CS100003", name: "일식음식점" },
  { code: "CS100004", name: "양식음식점" },
  { code: "CS100005", name: "제과점" },
  { code: "CS100006", name: "패스트푸드점" },
  { code: "CS100007", name: "치킨전문점" },
  { code: "CS100008", name: "분식전문점" },
  { code: "CS100009", name: "호프-간이주점" },
  { code: "CS100010", name: "커피-음료" },
  { code: "CS200001", name: "일반의류" },
  { code: "CS200002", name: "미용실" },
  { code: "CS200003", name: "편의점" },
  { code: "CS200004", name: "슈퍼마켓" },
  { code: "CS200005", name: "의약품" },
];

export const AREA_TYPES = [
  "골목상권",
  "발달상권",
  "전통시장",
  "관광특구",
];

// 서울 25개 자치구 (이름 + 중심 좌표)
export interface SeoulDistrict {
  name: string;
  center: [number, number];
}

export const SEOUL_DISTRICTS: SeoulDistrict[] = [
  { name: "종로구", center: [37.5735, 126.9790] },
  { name: "중구", center: [37.5641, 126.9979] },
  { name: "용산구", center: [37.5326, 126.9906] },
  { name: "성동구", center: [37.5634, 127.0369] },
  { name: "광진구", center: [37.5385, 127.0823] },
  { name: "동대문구", center: [37.5744, 127.0396] },
  { name: "중랑구", center: [37.6063, 127.0928] },
  { name: "성북구", center: [37.5894, 127.0167] },
  { name: "강북구", center: [37.6396, 127.0257] },
  { name: "도봉구", center: [37.6688, 127.0472] },
  { name: "노원구", center: [37.6542, 127.0568] },
  { name: "은평구", center: [37.6027, 126.9291] },
  { name: "서대문구", center: [37.5791, 126.9368] },
  { name: "마포구", center: [37.5663, 126.9014] },
  { name: "양천구", center: [37.5170, 126.8664] },
  { name: "강서구", center: [37.5509, 126.8495] },
  { name: "구로구", center: [37.4955, 126.8878] },
  { name: "금천구", center: [37.4569, 126.8955] },
  { name: "영등포구", center: [37.5264, 126.8963] },
  { name: "동작구", center: [37.5124, 126.9393] },
  { name: "관악구", center: [37.4781, 126.9515] },
  { name: "서초구", center: [37.4837, 127.0324] },
  { name: "강남구", center: [37.5172, 127.0473] },
  { name: "송파구", center: [37.5146, 127.1050] },
  { name: "강동구", center: [37.5301, 127.1238] },
];

// ── 전국 (Nationwide) 타입 ──

export interface RegionInfo {
  code: string;
  name: string;
  short: string;
  is_seoul: boolean;
  center: [number, number];
  zoom: number;
  bounds: [[number, number], [number, number]]; // [남서, 북동]
  minZoom: number;
}

export const SIDO_LIST: RegionInfo[] = [
  { code: "11", name: "서울특별시", short: "서울", is_seoul: true, center: [37.5665, 126.978], zoom: 12, bounds: [[37.413, 126.764], [37.715, 127.183]], minZoom: 11 },
  { code: "26", name: "부산광역시", short: "부산", is_seoul: false, center: [35.1796, 129.0756], zoom: 12, bounds: [[34.88, 128.75], [35.39, 129.35]], minZoom: 10 },
  { code: "27", name: "대구광역시", short: "대구", is_seoul: false, center: [35.8714, 128.6014], zoom: 12, bounds: [[35.72, 128.35], [36.05, 128.85]], minZoom: 10 },
  { code: "28", name: "인천광역시", short: "인천", is_seoul: false, center: [37.4563, 126.7052], zoom: 11, bounds: [[37.05, 126.20], [37.75, 126.98]], minZoom: 9 },
  { code: "29", name: "광주광역시", short: "광주", is_seoul: false, center: [35.1595, 126.8526], zoom: 12, bounds: [[35.05, 126.70], [35.28, 127.00]], minZoom: 11 },
  { code: "30", name: "대전광역시", short: "대전", is_seoul: false, center: [36.3504, 127.3845], zoom: 12, bounds: [[36.20, 127.25], [36.50, 127.55]], minZoom: 11 },
  { code: "31", name: "울산광역시", short: "울산", is_seoul: false, center: [35.5384, 129.3114], zoom: 11, bounds: [[35.30, 128.95], [35.77, 129.55]], minZoom: 10 },
  { code: "36", name: "세종특별자치시", short: "세종", is_seoul: false, center: [36.4800, 127.2590], zoom: 12, bounds: [[36.35, 127.00], [36.65, 127.45]], minZoom: 11 },
  { code: "41", name: "경기도", short: "경기", is_seoul: false, center: [37.4138, 127.5183], zoom: 9, bounds: [[36.85, 126.35], [38.30, 127.95]], minZoom: 8 },
  { code: "42", name: "강원특별자치도", short: "강원", is_seoul: false, center: [37.8228, 128.1555], zoom: 9, bounds: [[37.00, 127.05], [38.65, 129.40]], minZoom: 7 },
  { code: "43", name: "충청북도", short: "충북", is_seoul: false, center: [36.6357, 127.4912], zoom: 9, bounds: [[36.00, 127.00], [37.15, 128.15]], minZoom: 8 },
  { code: "44", name: "충청남도", short: "충남", is_seoul: false, center: [36.5184, 126.8000], zoom: 9, bounds: [[35.95, 125.90], [37.05, 127.40]], minZoom: 8 },
  { code: "45", name: "전북특별자치도", short: "전북", is_seoul: false, center: [35.7175, 127.1530], zoom: 9, bounds: [[35.28, 126.35], [36.15, 127.90]], minZoom: 8 },
  { code: "46", name: "전라남도", short: "전남", is_seoul: false, center: [34.8679, 126.9910], zoom: 9, bounds: [[33.90, 125.85], [35.50, 127.90]], minZoom: 7 },
  { code: "47", name: "경상북도", short: "경북", is_seoul: false, center: [36.4919, 128.8889], zoom: 9, bounds: [[35.55, 128.05], [37.10, 129.65]], minZoom: 7 },
  { code: "48", name: "경상남도", short: "경남", is_seoul: false, center: [35.4606, 128.2132], zoom: 9, bounds: [[34.55, 127.55], [35.95, 129.00]], minZoom: 8 },
  { code: "50", name: "제주특별자치도", short: "제주", is_seoul: false, center: [33.4996, 126.5312], zoom: 10, bounds: [[33.10, 126.10], [33.95, 127.00]], minZoom: 9 },
];

export interface DongSummary {
  adong_cd: string;
  adong_nm: string;
  sido_cd: string;
  signgu_nm: string;
  total_stores: number;
  target_stores: number;
  density_score: number;
}

export interface CategoryCount {
  category: string;
  count: number;
  percentage: number;
}

export interface StoreSummary {
  total_stores: number;
  category_distribution: CategoryCount[];
  top_businesses: string[];
}

export interface NationwideAnalysisResponse {
  dong_code: string;
  dong_name: string;
  region_name: string;
  data_source: string;
  total_score: number;
  grade: string;
  breakdown: ScoreBreakdownItem[];
  recommendation: string;
  store_summary: StoreSummary;
  missing_biz_recommendations: BizRecommendation[];
}

// ── 고급 분석 모델 ──

export interface TimeSlotData {
  time_slot: string;
  population: number;
  sales: number;
  ratio: number;
}

export interface DayData {
  day: string;
  population: number;
  sales: number;
  ratio: number;
}

export interface DemandAnalysis {
  hourly_population: TimeSlotData[];
  hourly_sales: TimeSlotData[];
  daily_population: DayData[];
  daily_sales: DayData[];
  peak_time: string;
  peak_day: string;
  weekend_ratio: number;
  recommendation: string;
}

export interface AgeGroup {
  age_group: string;
  population: number;
  ratio: number;
}

export interface AgeSales {
  age_group: string;
  sales: number;
}

export interface CustomerProfile {
  male_ratio: number;
  female_ratio: number;
  age_distribution: AgeGroup[];
  main_customer: string;
  sales_by_age: AgeSales[];
  male_sales: number;
  female_sales: number;
  recommendation: string;
}

export interface DeliveryOptimization {
  delivery_score: number;
  night_demand_ratio: number;
  night_sales_ratio: number;
  weekend_demand_ratio: number;
  delivery_store_ratio: number;
  delivery_competition: number;
  recommended_times: string[];
  recommendation: string;
}

export interface BizTrend {
  business_code: string;
  business_name: string;
  growth_rate: number;
  current_sales: number;
  store_count: number;
}

export interface CompetitionItem {
  business_name: string;
  store_count: number;
  competition: number;
  per_store_sales: number;
}

export interface MenuTrend {
  growing_businesses: BizTrend[];
  declining_businesses: BizTrend[];
  competition_map: CompetitionItem[];
  recommendation: string;
}

export interface RiskFactor {
  factor: string;
  impact: string;
  severity: string;
}

export interface SurvivalPrediction {
  survival_1yr: number;
  survival_3yr: number;
  survival_5yr: number;
  avg_quarterly_close_rate: number;
  risk_factors: RiskFactor[];
  positive_factors: RiskFactor[];
  grade: string;
  recommendation: string;
}

export interface FinancialDiagnosis {
  sales_per_store: number;
  city_avg_per_store: number;
  vs_city_avg: number;
  estimated_monthly_revenue: number;
  estimated_monthly_cost: number;
  estimated_monthly_rent: number;
  estimated_profit: number;
  profit_margin: number;
  cost_ratio: number;
  rent_ratio: number;
  rent_grade: string;
  stability_score: number;
  grade: string;
  recommendation: string;
}

export interface StrategyItem {
  title: string;
  description: string;
  priority: string;
  category: string;
}

export interface SWOT {
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}

export interface BusinessStrategy {
  swot: SWOT;
  strategies: StrategyItem[];
  summary: string;
}

export interface BusinessTip {
  category: string;
  title: string;
  description: string;
  source: string;
}

export interface PolicyItem {
  title: string;
  organization: string;
  category: string;
  target: string;
  period: string;
  url: string;
  is_active: boolean;
}

export interface PolicyResponse {
  total_count: number;
  policies: PolicyItem[];
  source: string;
  matched_category: string;
}

export interface AdvancedModelsResponse {
  area_code: string;
  area_name: string;
  business_type: string;
  demand: DemandAnalysis | null;
  customer: CustomerProfile | null;
  delivery: DeliveryOptimization | null;
  menu_trend: MenuTrend | null;
  survival: SurvivalPrediction | null;
  financial: FinancialDiagnosis | null;
  strategy: BusinessStrategy | null;
  tips: BusinessTip[];
}
