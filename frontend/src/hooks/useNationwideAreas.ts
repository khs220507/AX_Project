import { useState, useEffect, useCallback } from "react";
import { fetchRegionDongs } from "../api/client";
import type { DongSummary } from "../types";

export function useNationwideAreas(
  sidoCode: string,
  businessType?: string
) {
  const [dongs, setDongs] = useState<DongSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (sidoCode === "11") {
      setDongs([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRegionDongs(sidoCode, {
        business_type: businessType || undefined,
      });
      setDongs(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "데이터 로드 실패");
      setDongs([]);
    } finally {
      setLoading(false);
    }
  }, [sidoCode, businessType]);

  useEffect(() => {
    load();
  }, [load]);

  return { dongs, loading, error, reload: load };
}
