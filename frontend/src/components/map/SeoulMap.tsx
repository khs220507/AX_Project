import { useState, useEffect, useMemo, useCallback } from "react";
import { MapContainer, TileLayer, GeoJSON } from "react-leaflet";
import type { Layer, LeafletMouseEvent } from "leaflet";
import { LEGEND_ITEMS, scoreToColor } from "../../utils/colors";
import { aggregateByDong, type DongScore } from "../../utils/geo";
import type { AreaSummary } from "../../types";

const SEOUL_CENTER: [number, number] = [37.5665, 126.978];
const SEOUL_ZOOM = 12;
const NO_DATA_COLOR = "#e5e7eb";

interface Props {
  areas: AreaSummary[];
  selectedCode: string | null;
  onSelectArea: (area: AreaSummary) => void;
}

export function SeoulMap({ areas, selectedCode, onSelectArea }: Props) {
  const [dongGeoJson, setDongGeoJson] = useState<GeoJSON.FeatureCollection | null>(null);

  // Load dong GeoJSON once
  useEffect(() => {
    fetch("/seoul_dong.geojson")
      .then((r) => r.json())
      .then((data: GeoJSON.FeatureCollection) => setDongGeoJson(data))
      .catch((e) => console.error("Failed to load dong GeoJSON:", e));
  }, []);

  // Aggregate scores by dong
  const dongScores = useMemo(() => {
    if (!dongGeoJson || areas.length === 0) return new Map<string, DongScore>();
    return aggregateByDong(areas, dongGeoJson);
  }, [areas, dongGeoJson]);

  // Style each dong polygon based on score
  const styleFeature = useCallback(
    (feature?: GeoJSON.Feature) => {
      if (!feature) return {};
      const admCd = (feature.properties as { adm_cd: string }).adm_cd;
      const dong = dongScores.get(admCd);
      const hasData = dong && dong.avgScore >= 0;

      return {
        fillColor: hasData ? scoreToColor(dong.avgScore) : NO_DATA_COLOR,
        fillOpacity: hasData ? 0.55 : 0.15,
        color: "#64748b",
        weight: 0.8,
      };
    },
    [dongScores]
  );

  // Event handlers for each dong polygon
  const onEachFeature = useCallback(
    (feature: GeoJSON.Feature, layer: Layer) => {
      const props = feature.properties as {
        adm_cd: string;
        adm_nm: string;
        sggnm: string;
      };
      const dong = dongScores.get(props.adm_cd);
      const dongName = props.adm_nm.replace("서울특별시 ", "");

      // Tooltip
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

      // Click: select the best-scoring area in this dong
      layer.on({
        click: () => {
          if (dong && dong.areas.length > 0) {
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
          const admCd = (feature.properties as { adm_cd: string }).adm_cd;
          const d = dongScores.get(admCd);
          const hasData = d && d.avgScore >= 0;
          l.setStyle({
            weight: 0.8,
            color: "#64748b",
            fillOpacity: hasData ? 0.55 : 0.15,
          });
        },
      });
    },
    [dongScores, onSelectArea]
  );

  // Key to force GeoJSON re-render when scores change
  const geoKey = useMemo(
    () => `dong-${areas.length}-${areas[0]?.score ?? 0}`,
    [areas]
  );

  return (
    <MapContainer
      center={SEOUL_CENTER}
      zoom={SEOUL_ZOOM}
      className="h-full w-full rounded-xl"
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {dongGeoJson && (
        <GeoJSON
          key={geoKey}
          data={dongGeoJson}
          style={styleFeature}
          onEachFeature={onEachFeature}
        />
      )}

      {/* 범례 */}
      <div className="absolute bottom-6 left-3 z-1000 bg-white/95 backdrop-blur rounded-lg shadow-lg px-3 py-2.5 text-xs">
        <div className="font-bold text-gray-700 mb-1.5">창업 적합도</div>
        {LEGEND_ITEMS.map((item) => (
          <div key={item.label} className="flex items-center gap-2 py-0.5">
            <span
              className="w-4 h-3 rounded-sm inline-block"
              style={{ backgroundColor: item.color, opacity: 0.7 }}
            />
            <span className="text-gray-600">{item.label}</span>
            <span className="text-gray-400 ml-auto">{item.range}</span>
          </div>
        ))}
        <div className="flex items-center gap-2 py-0.5 mt-1 border-t border-gray-200 pt-1">
          <span
            className="w-4 h-3 rounded-sm inline-block"
            style={{ backgroundColor: NO_DATA_COLOR, opacity: 0.5 }}
          />
          <span className="text-gray-400">데이터 없음</span>
        </div>
      </div>
    </MapContainer>
  );
}
