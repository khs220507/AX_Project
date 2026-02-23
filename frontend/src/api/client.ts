import axios from "axios";
import type {
  AreaSummary,
  AreaDetail,
  AnalysisResponse,
  PredictRequest,
  PredictResponse,
  TrendsResponse,
  DongSummary,
  NationwideAnalysisResponse,
  NewsTrendResponse,
  AdvancedModelsResponse,
  PolicyResponse,
} from "../types";

const api = axios.create({
  baseURL: "/api",
  timeout: 30000,
});

export async function fetchAreas(params?: {
  search?: string;
  area_type?: string;
  district?: string;
  business_type?: string;
  limit?: number;
}): Promise<AreaSummary[]> {
  const { data } = await api.get("/areas", { params });
  return data;
}

export async function fetchAreaDetail(code: string): Promise<AreaDetail> {
  const { data } = await api.get(`/areas/${code}`);
  return data;
}

export async function fetchAnalysis(
  code: string,
  businessType: string
): Promise<AnalysisResponse> {
  const { data } = await api.get(`/analysis/${code}`, {
    params: { business_type: businessType },
  });
  return data;
}

export async function fetchPrediction(
  req: PredictRequest
): Promise<PredictResponse> {
  const { data } = await api.post("/predict", req);
  return data;
}

export async function fetchTrends(
  code: string,
  businessType: string
): Promise<TrendsResponse> {
  const { data } = await api.get(`/trends/${code}`, {
    params: { business_type: businessType },
  });
  return data;
}

// ── 전국 API ──

export async function fetchRegionDongs(
  sidoCode: string,
  params?: { business_type?: string }
): Promise<DongSummary[]> {
  const { data } = await api.get(`/regions/${sidoCode}/dongs`, { params });
  return data;
}

export async function fetchDongAnalysis(
  sidoCode: string,
  adongCd: string,
  businessType?: string
): Promise<NationwideAnalysisResponse> {
  const { data } = await api.get(`/regions/${sidoCode}/analysis/${adongCd}`, {
    params: { business_type: businessType },
  });
  return data;
}

export async function fetchRegionGeoJson(
  sidoCode: string
): Promise<GeoJSON.FeatureCollection> {
  const { data } = await api.get(`/geojson/${sidoCode}`);
  return data;
}

// ── 고급 분석 모델 API ──

export async function fetchAdvancedModels(
  code: string,
  businessType: string
): Promise<AdvancedModelsResponse> {
  const { data } = await api.get(`/models/${code}`, {
    params: { business_type: businessType },
    timeout: 45000,
  });
  return data;
}

// ── 뉴스 트렌드 API ──

export async function fetchNewsTrend(
  areaName: string,
  businessType?: string
): Promise<NewsTrendResponse> {
  const { data } = await api.get("/news/trend", {
    params: {
      area_name: areaName,
      business_type: businessType || undefined,
    },
    timeout: 60000, // NLP 처리 시간 고려
  });
  return data;
}

// ── 정책 정보 API ──

export async function fetchPolicies(
  businessType?: string
): Promise<PolicyResponse> {
  const { data } = await api.get("/policies", {
    params: { business_type: businessType || undefined },
  });
  return data;
}
