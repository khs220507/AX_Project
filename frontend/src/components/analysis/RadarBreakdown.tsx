import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from "recharts";
import type { ScoreBreakdownItem } from "../../types";

interface Props {
  breakdown: ScoreBreakdownItem[];
}

export function RadarBreakdown({ breakdown }: Props) {
  const data = breakdown.map((b) => ({
    category: b.category,
    score: b.score,
    fullMark: 100,
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <RadarChart data={data} cx="50%" cy="50%" outerRadius="70%">
        <PolarGrid stroke="#334155" />
        <PolarAngleAxis
          dataKey="category"
          tick={{ fontSize: 12, fill: "#94a3b8" }}
        />
        <PolarRadiusAxis
          angle={30}
          domain={[0, 100]}
          tick={{ fontSize: 10 }}
        />
        <Radar
          dataKey="score"
          stroke="#3b82f6"
          fill="#3b82f6"
          fillOpacity={0.25}
          strokeWidth={2}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
