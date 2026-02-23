/** 점수 → 색상 (파란색=창업적합 ~ 빨간색=위험) */
export function scoreToColor(score: number): string {
  if (score >= 80) return "#1d4ed8"; // 진한 파랑 - 매우 적합
  if (score >= 65) return "#3b82f6"; // 파랑 - 적합
  if (score >= 50) return "#a855f7"; // 보라 - 보통
  if (score >= 35) return "#f97316"; // 주황 - 주의
  return "#dc2626";                  // 빨강 - 위험
}

export function scoreToGrade(score: number): string {
  if (score >= 80) return "매우 적합";
  if (score >= 65) return "적합";
  if (score >= 50) return "보통";
  if (score >= 35) return "주의";
  return "위험";
}

export function gradeToColor(grade: string): string {
  switch (grade) {
    case "매우 적합":
      return "#1d4ed8";
    case "적합":
      return "#3b82f6";
    case "보통":
      return "#a855f7";
    case "주의":
      return "#f97316";
    default:
      return "#dc2626";
  }
}

/** 범례 데이터 */
export const LEGEND_ITEMS = [
  { label: "매우 적합", color: "#1d4ed8", range: "80+" },
  { label: "적합", color: "#3b82f6", range: "65~79" },
  { label: "보통", color: "#a855f7", range: "50~64" },
  { label: "주의", color: "#f97316", range: "35~49" },
  { label: "위험", color: "#dc2626", range: "~34" },
];
