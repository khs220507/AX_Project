import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from "recharts";
import type { CustomerProfile } from "../../types";
import { formatWon } from "../../utils/format";

interface Props {
  customer: CustomerProfile;
}

const AGE_COLORS = ["#94a3b8", "#a78bfa", "#818cf8", "#6366f1", "#4f46e5", "#4338ca"];

export function CustomerProfileCard({ customer }: Props) {
  const ageData = customer.age_distribution.map((a) => ({
    name: a.age_group,
    비율: a.ratio,
    인구: a.population,
  }));

  const salesData = customer.sales_by_age
    .filter((a) => a.sales > 0)
    .map((a) => ({
      name: a.age_group,
      매출: a.sales,
    }));

  return (
    <div className="space-y-3">
      {/* 주 고객층 */}
      <div className="flex items-center justify-center gap-3">
        <div className="bg-indigo-950/50 border border-indigo-800/30 rounded-lg px-4 py-2 text-center">
          <div className="text-sm font-bold text-indigo-300">{customer.main_customer}</div>
          <div className="text-xs text-indigo-400/70">주요 고객층</div>
        </div>
      </div>

      {/* 성별 비율 바 */}
      <div>
        <div className="text-xs font-medium text-slate-500 mb-1.5">성별 분포</div>
        <div className="flex h-6 rounded-full overflow-hidden">
          <div
            className="bg-blue-500 flex items-center justify-center text-[10px] font-medium text-white"
            style={{ width: `${customer.male_ratio}%` }}
          >
            {customer.male_ratio > 15 && `남 ${customer.male_ratio}%`}
          </div>
          <div
            className="bg-pink-500 flex items-center justify-center text-[10px] font-medium text-white"
            style={{ width: `${customer.female_ratio}%` }}
          >
            {customer.female_ratio > 15 && `여 ${customer.female_ratio}%`}
          </div>
        </div>
        {(customer.male_sales > 0 || customer.female_sales > 0) && (
          <div className="flex justify-between text-[10px] text-slate-500 mt-1">
            <span>남성 매출 {formatWon(customer.male_sales)}</span>
            <span>여성 매출 {formatWon(customer.female_sales)}</span>
          </div>
        )}
      </div>

      {/* 연령 분포 차트 */}
      <div>
        <div className="text-xs font-medium text-slate-500 mb-1.5">연령 분포</div>
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={ageData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} stroke="#334155" />
            <YAxis tick={{ fontSize: 9, fill: "#94a3b8" }} width={30} stroke="#334155" unit="%" />
            <Tooltip
              contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "8px", color: "#e2e8f0" }}
              formatter={(value: number, name: string) => [
                name === "비율" ? `${value}%` : value.toLocaleString(),
                name,
              ]}
            />
            <Bar dataKey="비율" radius={[3, 3, 0, 0]}>
              {ageData.map((_, i) => (
                <Cell key={i} fill={AGE_COLORS[i]} fillOpacity={0.85} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* 연령별 매출 */}
      {salesData.length > 0 && (
        <div>
          <div className="text-xs font-medium text-slate-500 mb-1.5">연령별 매출</div>
          <ResponsiveContainer width="100%" height={100}>
            <BarChart data={salesData} layout="vertical" margin={{ top: 0, right: 5, left: 5, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis type="number" tick={{ fontSize: 9, fill: "#94a3b8" }} stroke="#334155" />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} width={35} stroke="#334155" />
              <Tooltip
                contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "8px", color: "#e2e8f0" }}
                formatter={(value: number) => [formatWon(value), "매출"]}
              />
              <Bar dataKey="매출" fill="#8b5cf6" fillOpacity={0.8} radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <p className="text-xs text-slate-500 leading-relaxed">{customer.recommendation}</p>
    </div>
  );
}
