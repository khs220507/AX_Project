import { Circle, Popup } from "react-leaflet";
import { scoreToColor, scoreToGrade } from "../../utils/colors";
import type { AreaSummary } from "../../types";

interface Props {
  area: AreaSummary;
  isSelected: boolean;
  onClick: (area: AreaSummary) => void;
}

/** 실제 지리적 반경(미터)을 사용해 영역을 색칠 */
export function AreaMarker({ area, isSelected, onClick }: Props) {
  const color = scoreToColor(area.score);
  const grade = scoreToGrade(area.score);

  return (
    <Circle
      center={[area.lat, area.lng]}
      radius={isSelected ? 420 : 350}
      pathOptions={{
        fillColor: color,
        fillOpacity: isSelected ? 0.65 : 0.45,
        color: isSelected ? "#1e293b" : color,
        weight: isSelected ? 2.5 : 0.8,
      }}
      eventHandlers={{ click: () => onClick(area) }}
    >
      <Popup>
        <div className="text-center min-w-35">
          <div className="font-bold text-sm">{area.name}</div>
          <div className="text-xs text-gray-500">
            {area.district} / {area.area_type}
          </div>
          <div className="text-lg font-bold mt-1" style={{ color }}>
            {area.score}점
          </div>
          <div
            className="text-xs font-semibold mt-0.5 px-2 py-0.5 rounded-full inline-block"
            style={{ backgroundColor: color + "20", color }}
          >
            {grade}
          </div>
        </div>
      </Popup>
    </Circle>
  );
}
