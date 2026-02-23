import { useState, useEffect } from "react";
import { fetchDongAnalysis } from "../api/client";
import type { NationwideAnalysisResponse } from "../types";

export function useNationwideAnalysis(
  sidoCode: string,
  dongCode: string | null,
  businessType?: string
) {
  const [analysis, setAnalysis] =
    useState<NationwideAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!dongCode || sidoCode === "11") {
      setAnalysis(null);
      return;
    }

    let cancelled = false;
    setLoading(true);

    fetchDongAnalysis(sidoCode, dongCode, businessType)
      .then((data) => {
        if (!cancelled) setAnalysis(data);
      })
      .catch(() => {
        if (!cancelled) setAnalysis(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [sidoCode, dongCode, businessType]);

  return { analysis, loading };
}
