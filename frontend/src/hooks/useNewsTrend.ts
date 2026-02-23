import { useState, useEffect, useCallback } from "react";
import { fetchNewsTrend } from "../api/client";
import type { NewsTrendResponse } from "../types";

export function useNewsTrend(areaName: string | null, businessType?: string) {
  const [news, setNews] = useState<NewsTrendResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!areaName) {
      setNews(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchNewsTrend(areaName, businessType);
      setNews(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "뉴스 로드 실패");
      setNews(null);
    } finally {
      setLoading(false);
    }
  }, [areaName, businessType]);

  useEffect(() => {
    load();
  }, [load]);

  return { news, loading, error };
}
