import { BUSINESS_TYPES, AREA_TYPES, SIDO_LIST, SEOUL_DISTRICTS } from "../../types";

interface Props {
  selectedSido: string;
  onSidoChange: (v: string) => void;
  isSeoul: boolean;
  district: string;
  onDistrictChange: (v: string) => void;
  search: string;
  onSearchChange: (v: string) => void;
  areaType: string;
  onAreaTypeChange: (v: string) => void;
  businessType: string;
  onBusinessTypeChange: (v: string) => void;
  areaCount: number;
}

const selectClass =
  "border border-slate-600 rounded-lg px-3 py-1.5 text-sm bg-slate-800 text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500";

export function FilterPanel({
  selectedSido,
  onSidoChange,
  isSeoul,
  district,
  onDistrictChange,
  search,
  onSearchChange,
  areaType,
  onAreaTypeChange,
  businessType,
  onBusinessTypeChange,
  areaCount,
}: Props) {
  return (
    <div className="flex flex-wrap items-center gap-3 bg-[#111a2e] rounded-xl border border-slate-700/50 px-4 py-3">
      <select
        value={selectedSido}
        onChange={(e) => onSidoChange(e.target.value)}
        className="border border-blue-500/50 rounded-lg px-3 py-1.5 text-sm bg-blue-950 text-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500 font-semibold"
      >
        {SIDO_LIST.map((r) => (
          <option key={r.code} value={r.code}>
            {r.short}
          </option>
        ))}
      </select>

      {isSeoul && (
        <select
          value={district}
          onChange={(e) => onDistrictChange(e.target.value)}
          className={selectClass}
        >
          <option value="">전체 자치구</option>
          {SEOUL_DISTRICTS.map((d) => (
            <option key={d.name} value={d.name}>
              {d.name}
            </option>
          ))}
        </select>
      )}

      {isSeoul && (
        <select
          value={areaType}
          onChange={(e) => onAreaTypeChange(e.target.value)}
          className={selectClass}
        >
          <option value="">전체 상권유형</option>
          {AREA_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      )}

      <select
        value={businessType}
        onChange={(e) => onBusinessTypeChange(e.target.value)}
        className={selectClass}
      >
        {BUSINESS_TYPES.map((b) => (
          <option key={b.code} value={b.code}>
            {b.name}
          </option>
        ))}
      </select>

      {isSeoul && (
        <input
          type="text"
          placeholder="상권명 검색..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="border border-slate-600 rounded-lg px-3 py-1.5 text-sm w-36 bg-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      )}

      <span className="text-xs text-slate-500 ml-auto">
        {isSeoul ? `${areaCount}개 상권` : `${areaCount}개 행정동`}
      </span>
    </div>
  );
}
