import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import type { PredictResponse, QuarterlyTrend } from "../../types";
import { formatWon } from "../../utils/format";

interface Props {
  prediction: PredictResponse;
  historicalQuarters: QuarterlyTrend[];
}

export function PredictionChart({ prediction, historicalQuarters }: Props) {
  // 과거 데이터 + 예측 데이터 병합
  const data = [
    ...historicalQuarters.map((q) => ({
      quarter: q.quarter,
      actual: q.sales,
      predicted: null as number | null,
      lower: null as number | null,
      upper: null as number | null,
    })),
    ...prediction.quarterly_predictions.map((p) => ({
      quarter: p.quarter,
      actual: null as number | null,
      predicted: p.predicted,
      lower: p.lower,
      upper: p.upper,
    })),
  ];

  // 마지막 실적과 첫 예측을 연결
  if (historicalQuarters.length > 0 && prediction.quarterly_predictions.length > 0) {
    const lastActual = historicalQuarters[historicalQuarters.length - 1];
    const connectIdx = historicalQuarters.length - 1;
    if (data[connectIdx]) {
      data[connectIdx].predicted = lastActual.sales;
    }
  }

  if (!data.length) {
    return (
      <div className="text-center text-slate-500 py-8 text-sm">
        예측 데이터가 없습니다
      </div>
    );
  }

  // 예측 시작 분기
  const predStartQuarter =
    prediction.quarterly_predictions[0]?.quarter || "";

  return (
    <div>
      <ResponsiveContainer width="100%" height={240}>
        <ComposedChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="quarter"
            tick={{ fontSize: 11, fill: "#94a3b8" }}
            tickFormatter={(v: string) => v.replace(/^\d{2}/, "")}
            stroke="#334155"
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#94a3b8" }}
            tickFormatter={(v: number) => formatWon(v)}
            width={65}
            stroke="#334155"
          />
          <Tooltip
            formatter={(v: number | null, name: string) => {
              if (v === null) return ["-", name];
              const label =
                name === "actual"
                  ? "실적"
                  : name === "predicted"
                    ? "예측"
                    : name;
              return [formatWon(v), label];
            }}
          />
          {predStartQuarter && (
            <ReferenceLine
              x={predStartQuarter}
              stroke="#9ca3af"
              strokeDasharray="3 3"
              label={{ value: "예측", fontSize: 11, fill: "#9ca3af" }}
            />
          )}
          <Area
            type="monotone"
            dataKey="upper"
            stroke="none"
            fill="#f59e0b"
            fillOpacity={0.1}
          />
          <Area
            type="monotone"
            dataKey="lower"
            stroke="none"
            fill="#111a2e"
            fillOpacity={1}
          />
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 4 }}
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="predicted"
            stroke="#f59e0b"
            strokeWidth={2}
            strokeDasharray="6 3"
            dot={{ r: 4 }}
            connectNulls={false}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {prediction.factors.length > 0 && (
        <div className="mt-2 space-y-1">
          {prediction.factors.map((f, i) => (
            <div key={i} className="flex justify-between text-xs px-1">
              <span className="text-slate-400">{f.name}</span>
              <span
                className={
                  f.impact.startsWith("+")
                    ? "text-green-600 font-medium"
                    : f.impact.startsWith("-")
                      ? "text-red-600 font-medium"
                      : "text-slate-500"
                }
              >
                {f.impact}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
