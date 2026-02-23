import { useEffect, useMemo, useCallback } from "react";
import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";
import L from "leaflet";
import type { Layer, LeafletMouseEvent } from "leaflet";
import { LEGEND_ITEMS, scoreToColor } from "../../utils/colors";
import { aggregateByDong } from "../../utils/geo";
import type { AreaSummary, DongSummary } from "../../types";

const NO_DATA_COLOR = "#334155";

/** 시도 변경 시 지도 이동 + 지역 경계 제한 */
function MapController({
  center,
  zoom,
  bounds,
  minZoom,
}: {
  center: [number, number];
  zoom: number;
  bounds: L.LatLngBounds;
  minZoom: number;
}) {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, zoom, { duration: 1 });
    map.setMaxBounds(bounds);
    map.setMinZoom(minZoom);
  }, [map, center, zoom, bounds, minZoom]);
  return null;
}

interface Props {
  isSeoul: boolean;
  center: [number, number];
  zoom: number;
  geoJson: GeoJSON.FeatureCollection | null;
  regionBounds: [[number, number], [number, number]];
  regionMinZoom: number;
  // 서울 모드
  areas?: AreaSummary[];
  selectedCode?: string | null;
  onSelectArea?: (area: AreaSummary) => void;
  district?: string; // 선택된 자치구 (서울 모드)
  // 비서울 모드
  dongs?: DongSummary[];
  selectedDongCode?: string | null;
  onSelectDong?: (dong: DongSummary) => void;
}

export function RegionMap({
  isSeoul,
  center,
  zoom,
  geoJson,
  regionBounds,
  regionMinZoom,
  areas = [],
  selectedCode,
  onSelectArea,
  district = "",
  dongs = [],
  selectedDongCode,
  onSelectDong,
}: Props) {
  const leafletBounds = useMemo(
    () => L.latLngBounds(L.latLng(regionBounds[0][0], regionBounds[0][1]), L.latLng(regionBounds[1][0], regionBounds[1][1])),
    [regionBounds],
  );
  // ── 서울 모드: 상권별 동 점수 집계 ──
  const dongScores = useMemo(() => {
    if (!isSeoul || !geoJson || areas.length === 0)
      return new Map<string, ReturnType<typeof aggregateByDong> extends Map<string, infer V> ? V : never>();
    return aggregateByDong(areas, geoJson);
  }, [isSeoul, areas, geoJson]);

  // ── 비서울 모드: 동별 점수 맵 ──
  const nationwideDongMap = useMemo(() => {
    if (isSeoul || dongs.length === 0) return new Map<string, DongSummary>();
    const m = new Map<string, DongSummary>();
    for (const d of dongs) {
      m.set(d.adong_cd, d);
    }
    return m;
  }, [isSeoul, dongs]);

  // ── 공통: 폴리곤 스타일 ──
  const styleFeature = useCallback(
    (feature?: GeoJSON.Feature) => {
      if (!feature) return {};
      const props = feature.properties as { adm_cd: string; adm_nm: string; sggnm: string };
      const admCd = props.adm_cd;

      if (isSeoul) {
        // 구 선택 시: 해당 구가 아닌 폴리곤은 dimmed
        const inDistrict = !district || props.sggnm === district || props.adm_nm.includes(district);
        const dong = dongScores.get(admCd);
        const hasData = dong && dong.avgScore >= 0;

        if (!inDistrict) {
          return {
            fillColor: NO_DATA_COLOR,
            fillOpacity: 0.08,
            color: "#cbd5e1",
            weight: 0.4,
          };
        }
        return {
          fillColor: hasData ? scoreToColor(dong.avgScore) : NO_DATA_COLOR,
          fillOpacity: hasData ? 0.55 : 0.35,
          color: "#475569",
          weight: 0.8,
        };
      } else {
        // 비서울: adm_cd로 매칭
        let dongData: DongSummary | undefined = nationwideDongMap.get(admCd);
        // 프리픽스 매칭
        if (!dongData) {
          for (const [key, d] of nationwideDongMap) {
            if (admCd.slice(0, 5) === key.slice(0, 5) && admCd.slice(0, 8) === key.slice(0, 8)) {
              dongData = d;
              break;
            }
          }
        }
        const hasData = dongData && dongData.total_stores > 0;
        return {
          fillColor: hasData ? scoreToColor(dongData!.density_score) : NO_DATA_COLOR,
          fillOpacity: hasData ? 0.55 : 0.35,
          color: "#475569",
          weight: 0.8,
        };
      }
    },
    [isSeoul, dongScores, nationwideDongMap, district]
  );

  // ── 공통: 이벤트 핸들러 ──
  const onEachFeature = useCallback(
    (feature: GeoJSON.Feature, layer: Layer) => {
      const props = feature.properties as {
        adm_cd: string;
        adm_nm: string;
        sggnm: string;
      };

      if (isSeoul) {
        // 서울 모드: 기존 동작
        const dong = dongScores.get(props.adm_cd);
        const dongName = props.adm_nm.replace("서울특별시 ", "");

        if (dong && dong.avgScore >= 0) {
          layer.bindTooltip(
            `<b>${dongName}</b><br/>평균 ${dong.avgScore}점 (${dong.areaCount}개 상권)`,
            { sticky: true, className: "dong-tooltip" }
          );
        } else {
          layer.bindTooltip(
            `<b>${dongName}</b><br/><span style="color:#9ca3af">데이터 없음</span>`,
            { sticky: true, className: "dong-tooltip" }
          );
        }

        layer.on({
          click: () => {
            if (dong && dong.areas.length > 0 && onSelectArea) {
              const best = dong.areas.reduce((a, b) =>
                a.score > b.score ? a : b
              );
              onSelectArea(best);
            }
          },
          mouseover: (e: LeafletMouseEvent) => {
            const l = e.target;
            l.setStyle({ weight: 2.5, color: "#1e293b", fillOpacity: 0.7 });
            l.bringToFront();
          },
          mouseout: (e: LeafletMouseEvent) => {
            const l = e.target;
            const d = dongScores.get(props.adm_cd);
            const hasData = d && d.avgScore >= 0;
            l.setStyle({
              weight: 0.8,
              color: "#475569",
              fillOpacity: hasData ? 0.55 : 0.15,
            });
          },
        });
      } else {
        // 비서울 모드: 동 점포 데이터
        let dongData: DongSummary | undefined = nationwideDongMap.get(props.adm_cd);
        if (!dongData) {
          for (const [key, d] of nationwideDongMap) {
            if (props.adm_cd.slice(0, 5) === key.slice(0, 5) && props.adm_cd.slice(0, 8) === key.slice(0, 8)) {
              dongData = d;
              break;
            }
          }
        }

        const dongName = props.adm_nm
          .replace(/서울특별시\s?/, "")
          .replace(/부산광역시\s?/, "")
          .replace(/대구광역시\s?/, "")
          .replace(/인천광역시\s?/, "")
          .replace(/광주광역시\s?/, "")
          .replace(/대전광역시\s?/, "")
          .replace(/울산광역시\s?/, "")
          .replace(/세종특별자치시\s?/, "")
          .replace(/경기도\s?/, "")
          .replace(/강원(특별자치)?도\s?/, "")
          .replace(/충청(북|남)도\s?/, "")
          .replace(/전(라|북특별자치)(북|남)?도\s?/, "")
          .replace(/경상(북|남)도\s?/, "")
          .replace(/제주특별자치도\s?/, "");

        if (dongData && dongData.total_stores > 0) {
          layer.bindTooltip(
            `<b>${dongName}</b><br/>${dongData.density_score}점 (${dongData.total_stores}개 점포)`,
            { sticky: true, className: "dong-tooltip" }
          );
        } else {
          layer.bindTooltip(
            `<b>${dongName}</b><br/><span style="color:#9ca3af">데이터 없음</span>`,
            { sticky: true, className: "dong-tooltip" }
          );
        }

        layer.on({
          click: () => {
            if (dongData && onSelectDong) {
              onSelectDong(dongData);
            }
          },
          mouseover: (e: LeafletMouseEvent) => {
            const l = e.target;
            l.setStyle({ weight: 2.5, color: "#1e293b", fillOpacity: 0.7 });
            l.bringToFront();
          },
          mouseout: (e: LeafletMouseEvent) => {
            const l = e.target;
            const hasData = dongData && dongData.total_stores > 0;
            l.setStyle({
              weight: 0.8,
              color: "#475569",
              fillOpacity: hasData ? 0.55 : 0.15,
            });
          },
        });
      }
    },
    [isSeoul, dongScores, nationwideDongMap, onSelectArea, onSelectDong]
  );

  // GeoJSON 재렌더링 키
  const geoKey = useMemo(() => {
    if (isSeoul) {
      return `seoul-${areas.length}-${areas[0]?.score ?? 0}-${district}`;
    }
    return `nw-${dongs.length}-${dongs[0]?.density_score ?? 0}-${center[0]}`;
  }, [isSeoul, areas, dongs, center, district]);

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      className="h-full w-full rounded-xl"
      scrollWheelZoom={true}
      maxBounds={leafletBounds}
      maxBoundsViscosity={1.0}
      minZoom={regionMinZoom}
    >
      <MapController center={center} zoom={zoom} bounds={leafletBounds} minZoom={regionMinZoom} />
      <TileLayer
        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />

      {geoJson && (
        <GeoJSON
          key={geoKey}
          data={geoJson}
          style={styleFeature}
          onEachFeature={onEachFeature}
        />
      )}

      {/* 범례 */}
      <div className="absolute bottom-6 left-3 z-1000 bg-[#111a2e]/95 backdrop-blur border border-slate-700/50 rounded-lg shadow-lg px-3 py-2.5 text-xs">
        <div className="font-bold text-slate-200 mb-1.5">
          {isSeoul ? "창업 적합도" : "상권 밀도"}
        </div>
        {LEGEND_ITEMS.map((item) => (
          <div key={item.label} className="flex items-center gap-2 py-0.5">
            <span
              className="w-4 h-3 rounded-sm inline-block"
              style={{ backgroundColor: item.color, opacity: 0.7 }}
            />
            <span className="text-slate-400">{item.label}</span>
            <span className="text-slate-500 ml-auto">{item.range}</span>
          </div>
        ))}
        <div className="flex items-center gap-2 py-0.5 mt-1 border-t border-slate-700 pt-1">
          <span
            className="w-4 h-3 rounded-sm inline-block"
            style={{ backgroundColor: "#334155", opacity: 0.7 }}
          />
          <span className="text-slate-500">데이터 없음</span>
        </div>
      </div>
    </MapContainer>
  );
}
