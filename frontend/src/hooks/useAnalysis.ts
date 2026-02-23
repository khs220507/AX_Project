import { useState, useEffect } from "react";
import { fetchAnalysis, fetchTrends } from "../api/client";
import type { AnalysisResponse, TrendsResponse } from "../types";

export function useAnalysis(areaCode: string | null, businessType: string) {
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [trends, setTrends] = useState<TrendsResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!areaCode) {
      setAnalysis(null);
      setTrends(null);
      return;
    }

    let cancelled = false;
    setLoading(true);

    Promise.all([
      fetchAnalysis(areaCode, businessType),
      fetchTrends(areaCode, businessType),
    ])
      .then(([analysisData, trendsData]) => {
        if (!cancelled) {
          setAnalysis(analysisData);
          setTrends(trendsData);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setAnalysis(null);
          setTrends(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [areaCode, businessType]);

  return { analysis, trends, loading };
}
