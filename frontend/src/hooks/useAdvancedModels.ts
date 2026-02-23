import { useState, useEffect } from "react";
import { fetchAdvancedModels } from "../api/client";
import type { AdvancedModelsResponse } from "../types";

export function useAdvancedModels(areaCode: string | null, businessType: string) {
  const [models, setModels] = useState<AdvancedModelsResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!areaCode) {
      setModels(null);
      return;
    }

    let cancelled = false;
    setLoading(true);

    fetchAdvancedModels(areaCode, businessType)
      .then((data) => {
        if (!cancelled) setModels(data);
      })
      .catch(() => {
        if (!cancelled) setModels(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [areaCode, businessType]);

  return { models, loading };
}
