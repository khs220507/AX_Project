import { scoreToColor } from "../../utils/colors";

interface Props {
  score: number;
  grade: string;
  size?: number;
}

export function ScoreGauge({ score, grade, size = 160 }: Props) {
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - score / 100);
  const color = scoreToColor(score);

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={radius} fill="none" stroke="#1e293b" strokeWidth="8" />
        <circle
          cx="50" cy="50" r={radius} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
          transform="rotate(-90 50 50)" style={{ transition: "stroke-dashoffset 1s ease-out" }}
        />
        <text x="50" y="45" textAnchor="middle" fontSize="22" fontWeight="bold" fill="#e2e8f0">{score}</text>
        <text x="50" y="60" textAnchor="middle" fontSize="10" fill="#64748b">/ 100</text>
      </svg>
      <span className="text-sm font-semibold mt-1 px-3 py-0.5 rounded-full" style={{ backgroundColor: color + "20", color }}>{grade}</span>
    </div>
  );
}
