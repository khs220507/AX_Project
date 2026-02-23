import { useState, useMemo, useEffect } from "react";
import { RegionMap } from "../map/RegionMap";
import { FilterPanel } from "../filters/FilterPanel";
import { AnalysisPanel } from "../analysis/AnalysisPanel";
import { useAreas } from "../../hooks/useAreas";
import { useRegionGeoJson } from "../../hooks/useRegionGeoJson";
import { useNationwideAreas } from "../../hooks/useNationwideAreas";
import type { AreaSummary, DongSummary } from "../../types";
import { SIDO_LIST as REGIONS, SEOUL_DISTRICTS } from "../../types";

export function DashboardLayout() {
  // 시도 선택
  const [selectedSido, setSelectedSido] = useState("11");
  const isSeoul = selectedSido === "11";

  // 서울 자치구 선택
  const [district, setDistrict] = useState("");

  // 필터
  const [search, setSearch] = useState("");
  const [areaType, setAreaType] = useState("");
  const [businessType, setBusinessType] = useState("CS100001");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  // 선택 상태
  const [selectedArea, setSelectedArea] = useState<AreaSummary | null>(null);
  const [selectedDong, setSelectedDong] = useState<DongSummary | null>(null);

  // 시도 변경 시 선택 초기화
  useEffect(() => {
    setSelectedArea(null);
    setSelectedDong(null);
    setSearch("");
    setDebouncedSearch("");
    setAreaType("");
    setDistrict("");
  }, [selectedSido]);

  const handleSearchChange = (v: string) => {
    setSearch(v);
    const t = setTimeout(() => setDebouncedSearch(v), 300);
    return () => clearTimeout(t);
  };

  // GeoJSON 지연 로딩
  const { geoJson, loading: geoLoading } = useRegionGeoJson(selectedSido);

  // 서울 데이터
  const seoulFilters = useMemo(
    () => ({
      search: debouncedSearch || undefined,
      area_type: areaType || undefined,
      business_type: businessType || undefined,
      district: district || undefined,
    }),
    [debouncedSearch, areaType, businessType, district]
  );
  const { areas, loading: seoulLoading } = useAreas(
    isSeoul ? seoulFilters : undefined
  );

  // 비서울 데이터
  const { dongs, loading: nationwideLoading } = useNationwideAreas(
    selectedSido,
    businessType
  );

  // 현재 시도 정보 (구 선택 시 해당 구 중심으로 이동)
  const currentRegion = REGIONS.find((r) => r.code === selectedSido);
  const selectedDistrict = district
    ? SEOUL_DISTRICTS.find((d) => d.name === district)
    : null;
  const center: [number, number] = selectedDistrict
    ? selectedDistrict.center
    : (currentRegion?.center ?? [37.5665, 126.978]);
  const zoom = selectedDistrict ? 14 : (currentRegion?.zoom ?? 10);
  const regionBounds = currentRegion?.bounds ?? [[33.0, 124.5], [39.0, 132.0]];
  const regionMinZoom = currentRegion?.minZoom ?? 6;

  const loading = isSeoul ? seoulLoading : nationwideLoading || geoLoading;

  return (
    <div className="h-screen flex flex-col bg-[#0b1120]">
      {/* 헤더 */}
      <header className="bg-[#0f1729] border-b border-slate-700/50 px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
            <span className="text-white text-sm font-bold">AX</span>
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-100">
              전국 상권분석 대시보드
            </h1>
            <p className="text-xs text-slate-500">
              소상공인 AI 경영 컨설팅 솔루션
            </p>
          </div>
        </div>
        <div className="text-xs text-slate-500">
          {isSeoul
            ? "실시간 서울 열린데이터 연동"
            : `${currentRegion?.name ?? ""} | SEMAS 점포 데이터`}
        </div>
      </header>

      {/* 필터 */}
      <div className="px-4 pt-3 shrink-0">
        <FilterPanel
          selectedSido={selectedSido}
          onSidoChange={setSelectedSido}
          isSeoul={isSeoul}
          district={district}
          onDistrictChange={setDistrict}
          search={search}
          onSearchChange={handleSearchChange}
          areaType={areaType}
          onAreaTypeChange={setAreaType}
          businessType={businessType}
          onBusinessTypeChange={setBusinessType}
          areaCount={isSeoul ? areas.length : dongs.length}
        />
      </div>

      {/* 메인 컨텐츠 */}
      <div className="flex-1 flex flex-col md:flex-row gap-4 p-4 min-h-0">
        {/* 지도 */}
        <div className="md:w-2/5 h-[50vh] md:h-full relative">
          {loading && (
            <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 bg-slate-800/90 px-4 py-2 rounded-full shadow text-sm text-slate-300 border border-slate-700">
              {isSeoul ? "상권 데이터 로딩 중..." : "점포 데이터 로딩 중..."}
            </div>
          )}
          <RegionMap
            isSeoul={isSeoul}
            center={center}
            zoom={zoom}
            geoJson={geoJson}
            areas={isSeoul ? areas : undefined}
            selectedCode={selectedArea?.code ?? null}
            onSelectArea={setSelectedArea}
            district={district}
            dongs={!isSeoul ? dongs : undefined}
            selectedDongCode={selectedDong?.adong_cd ?? null}
            onSelectDong={setSelectedDong}
            regionBounds={regionBounds}
            regionMinZoom={regionMinZoom}
          />
        </div>

        {/* 분석 패널 */}
        <div className="md:w-3/5 h-[50vh] md:h-full overflow-y-auto">
          <AnalysisPanel
            isSeoul={isSeoul}
            selectedSido={selectedSido}
            selectedArea={isSeoul ? selectedArea : null}
            selectedDong={!isSeoul ? selectedDong : null}
            businessType={businessType}
          />
        </div>
      </div>
    </div>
  );
}
