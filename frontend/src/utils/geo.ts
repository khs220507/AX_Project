import type { AreaSummary, DongSummary } from "../types";

/** Ray-casting point-in-polygon (works for simple & multi polygons) */
function pointInRing(
  lat: number,
  lng: number,
  ring: number[][]
): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i][1], yi = ring[i][0]; // GeoJSON is [lng, lat]
    const xj = ring[j][1], yj = ring[j][0];
    if (
      yi > lng !== yj > lng &&
      lat < ((xj - xi) * (lng - yi)) / (yj - yi) + xi
    ) {
      inside = !inside;
    }
  }
  return inside;
}

function pointInPolygon(
  lat: number,
  lng: number,
  geometry: { type: string; coordinates: number[][][] | number[][][][] }
): boolean {
  if (geometry.type === "Polygon") {
    const coords = geometry.coordinates as number[][][];
    return pointInRing(lat, lng, coords[0]);
  }
  if (geometry.type === "MultiPolygon") {
    const coords = geometry.coordinates as number[][][][];
    return coords.some((polygon) => pointInRing(lat, lng, polygon[0]));
  }
  return false;
}

export interface DongScore {
  adm_cd: string;
  adm_nm: string;
  sggnm: string;
  avgScore: number;
  areaCount: number;
  areas: AreaSummary[];
}

/** 상권 좌표를 동 폴리곤에 매핑하여 동별 평균 점수 계산 */
export function aggregateByDong(
  areas: AreaSummary[],
  dongGeoJson: GeoJSON.FeatureCollection
): Map<string, DongScore> {
  const dongScores = new Map<string, DongScore>();

  // Initialize all dongs
  for (const feature of dongGeoJson.features) {
    const props = feature.properties as {
      adm_cd: string;
      adm_nm: string;
      sggnm: string;
    };
    dongScores.set(props.adm_cd, {
      adm_cd: props.adm_cd,
      adm_nm: props.adm_nm,
      sggnm: props.sggnm,
      avgScore: -1, // -1 means no data
      areaCount: 0,
      areas: [],
    });
  }

  // Assign each area to a dong
  for (const area of areas) {
    for (const feature of dongGeoJson.features) {
      const props = feature.properties as { adm_cd: string };
      const geom = feature.geometry as {
        type: string;
        coordinates: number[][][] | number[][][][];
      };
      if (pointInPolygon(area.lat, area.lng, geom)) {
        const dong = dongScores.get(props.adm_cd)!;
        dong.areas.push(area);
        dong.areaCount++;
        break;
      }
    }
  }

  // Calculate averages
  for (const dong of dongScores.values()) {
    if (dong.areaCount > 0) {
      dong.avgScore = Math.round(
        dong.areas.reduce((sum, a) => sum + a.score, 0) / dong.areaCount
      );
    }
  }

  return dongScores;
}

/** 비서울 동 점수를 GeoJSON feature에 매핑 */
export interface NationwideDongScore {
  score: number;
  dong: DongSummary;
}

export function mapDongScoresToGeoJson(
  dongs: DongSummary[],
  geoJson: GeoJSON.FeatureCollection
): Map<string, NationwideDongScore> {
  const scoreMap = new Map<string, NationwideDongScore>();
  const dongMap = new Map(dongs.map((d) => [d.adong_cd, d]));

  for (const feature of geoJson.features) {
    const admCd = (feature.properties as { adm_cd: string }).adm_cd;
    // 정확한 매칭 시도
    let dong = dongMap.get(admCd);
    // 없으면 프리픽스 매칭 (8자리 중 앞 5자리)
    if (!dong) {
      for (const [key, d] of dongMap) {
        if (admCd.startsWith(key.slice(0, 5)) && admCd.slice(0, 8) === key.slice(0, 8)) {
          dong = d;
          break;
        }
      }
    }
    if (dong) {
      scoreMap.set(admCd, { score: dong.density_score, dong });
    }
  }

  return scoreMap;
}
