import { useState, useEffect } from "react";
import { fetchPrediction } from "../api/client";
import type { PredictResponse } from "../types";

export function usePrediction(areaCode: string | null, businessType: string) {
  const [prediction, setPrediction] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!areaCode) {
      setPrediction(null);
      return;
    }

    let cancelled = false;
    setLoading(true);

    fetchPrediction({ area_code: areaCode, business_type: businessType })
      .then((data) => {
        if (!cancelled) setPrediction(data);
      })
      .catch(() => {
        if (!cancelled) setPrediction(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [areaCode, businessType]);

  return { prediction, loading };
}
