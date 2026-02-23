import { useState, useEffect, useCallback } from "react";
import { fetchAreas } from "../api/client";
import type { AreaSummary } from "../types";

export function useAreas(filters?: {
  search?: string;
  area_type?: string;
  business_type?: string;
}) {
  const [areas, setAreas] = useState<AreaSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    // filters가 undefined이면 fetch 건너뛰기 (비서울 모드)
    if (!filters) {
      setAreas([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAreas({
        search: filters.search || undefined,
        area_type: filters.area_type || undefined,
        business_type: filters.business_type || undefined,
        limit: 500,
      });
      setAreas(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "데이터 로드 실패");
    } finally {
      setLoading(false);
    }
  }, [filters?.search, filters?.area_type, filters?.business_type, filters === undefined]);

  useEffect(() => {
    load();
  }, [load]);

  return { areas, loading, error, reload: load };
}
