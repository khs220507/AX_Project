import { useState, useEffect } from "react";
import { fetchRegionGeoJson } from "../api/client";

const geoJsonCache = new Map<string, GeoJSON.FeatureCollection>();

export function useRegionGeoJson(sidoCode: string) {
  const [geoJson, setGeoJson] = useState<GeoJSON.FeatureCollection | null>(
    null
  );
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setGeoJson(null);

    // 서울은 기존 로컬 파일 사용
    if (sidoCode === "11") {
      fetch("/seoul_dong.geojson")
        .then((r) => r.json())
        .then((data: GeoJSON.FeatureCollection) => setGeoJson(data))
        .catch((e) => console.error("Failed to load Seoul GeoJSON:", e));
      return;
    }

    // 캐시 확인
    if (geoJsonCache.has(sidoCode)) {
      setGeoJson(geoJsonCache.get(sidoCode)!);
      return;
    }

    // 백엔드에서 지연 로딩
    setLoading(true);
    fetchRegionGeoJson(sidoCode)
      .then((data) => {
        geoJsonCache.set(sidoCode, data);
        setGeoJson(data);
      })
      .catch((e) => console.error("Failed to load region GeoJSON:", e))
      .finally(() => setLoading(false));
  }, [sidoCode]);

  return { geoJson, loading };
}
