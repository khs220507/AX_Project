import type { NewsTrendResponse } from "../../types";

interface Props {
  news: NewsTrendResponse;
}

const sentimentColor = (label: string) => {
  switch (label) {
    case "긍정":
      return { bg: "bg-green-950/50", text: "text-green-400", dot: "bg-green-500" };
    case "부정":
      return { bg: "bg-red-950/50", text: "text-red-400", dot: "bg-red-500" };
    default:
      return { bg: "bg-slate-800", text: "text-slate-400", dot: "bg-slate-500" };
  }
};

export function NewsTrendCard({ news }: Props) {
  const overall = sentimentColor(news.overall_label);
  const total =
    news.positive_count + news.negative_count + news.neutral_count || 1;

  return (
    <div className="space-y-3">
      {/* 종합 감성 게이지 */}
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-red-400">부정</span>
            <span className="text-slate-500">중립</span>
            <span className="text-green-400">긍정</span>
          </div>
          <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden relative">
            <div
              className="absolute inset-y-0 left-0 bg-gradient-to-r from-red-500 via-slate-600 to-green-500 rounded-full opacity-60"
              style={{ width: "100%" }}
            />
            <div
              className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-slate-200 border-2 border-slate-900 rounded-full shadow"
              style={{ left: `${news.overall_score}%`, marginLeft: "-6px" }}
            />
          </div>
        </div>
        <span
          className={`text-sm font-bold px-2 py-0.5 rounded ${overall.bg} ${overall.text}`}
        >
          {news.overall_label}
        </span>
      </div>

      {/* 긍정/부정/중립 비율 바 */}
      <div className="flex h-2 rounded-full overflow-hidden">
        {news.positive_count > 0 && (
          <div className="bg-green-500" style={{ width: `${(news.positive_count / total) * 100}%` }} />
        )}
        {news.neutral_count > 0 && (
          <div className="bg-slate-600" style={{ width: `${(news.neutral_count / total) * 100}%` }} />
        )}
        {news.negative_count > 0 && (
          <div className="bg-red-500" style={{ width: `${(news.negative_count / total) * 100}%` }} />
        )}
      </div>
      <div className="flex justify-between text-xs text-slate-500">
        <span>긍정 {news.positive_count}건</span>
        <span>중립 {news.neutral_count}건</span>
        <span>부정 {news.negative_count}건</span>
      </div>

      {/* 핫 키워드 */}
      {news.keywords.length > 0 && (
        <div>
          <div className="text-xs font-medium text-slate-500 mb-1.5">핫 키워드</div>
          <div className="flex flex-wrap gap-1.5">
            {news.keywords.map((kw, i) => (
              <span
                key={kw.keyword}
                className="px-2 py-0.5 rounded-full text-xs font-medium"
                style={{
                  backgroundColor: i < 3 ? "#1e3a5f" : i < 6 ? "#1e293b" : "#0f172a",
                  color: i < 3 ? "#60a5fa" : i < 6 ? "#818cf8" : "#94a3b8",
                  fontSize: `${Math.max(11, 14 - i)}px`,
                }}
              >
                {kw.keyword}
                <span className="ml-0.5 opacity-60">{kw.count}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 뉴스 기사 목록 */}
      {news.articles.length > 0 && (
        <div className="space-y-1.5 mt-1">
          <div className="text-xs font-medium text-slate-500">관련 뉴스</div>
          {news.articles.slice(0, 5).map((article, i) => {
            const sc = sentimentColor(article.sentiment);
            return (
              <a
                key={i}
                href={article.link}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-2 rounded-lg border border-slate-700/50 hover:bg-slate-800/50 transition-colors"
              >
                <div className="flex items-start gap-2">
                  <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${sc.dot}`} />
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                      {article.title}
                    </div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] text-slate-500">{article.source}</span>
                      <span className={`text-[10px] px-1 rounded ${sc.bg} ${sc.text}`}>
                        {article.sentiment}
                      </span>
                    </div>
                  </div>
                </div>
              </a>
            );
          })}
        </div>
      )}

      {news.articles.length === 0 && (
        <div className="text-center text-xs text-slate-500 py-2">
          관련 뉴스가 없습니다
        </div>
      )}
    </div>
  );
}
