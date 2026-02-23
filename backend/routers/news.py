"""뉴스 트렌드 분석 API"""

from fastapi import APIRouter, Query
from models.schemas import NewsTrendResponse, NewsArticle, NewsKeyword
from services.news_crawler import crawl_google_news, build_search_queries
from services.news_nlp import (
    analyze_batch_sentiment,
    extract_keywords,
    compute_overall_sentiment,
)

router = APIRouter(prefix="/api")


@router.get("/news/trend", response_model=NewsTrendResponse)
async def get_news_trend(
    area_name: str = Query(..., description="상권/지역 이름"),
    business_type: str = Query("", description="업종명 (예: 한식음식점)"),
):
    """상권/지역 관련 뉴스 크롤링 + 감성분석 + 키워드 추출"""
    # 1. 검색 쿼리 생성
    queries = build_search_queries(area_name, business_type)

    # 2. 뉴스 크롤링
    all_articles: list[dict] = []
    seen_titles = set()
    for q in queries:
        articles = await crawl_google_news(q)
        for a in articles:
            if a["title"] not in seen_titles:
                seen_titles.add(a["title"])
                all_articles.append(a)

    if not all_articles:
        return NewsTrendResponse(
            area_name=area_name,
            query=queries[0] if queries else area_name,
            overall_score=50,
            overall_label="중립",
            positive_count=0,
            negative_count=0,
            neutral_count=0,
            keywords=[],
            articles=[],
        )

    # 3. 감성분석 (제목 + 설명 결합)
    texts = [f"{a['title']} {a['description']}" for a in all_articles]
    sentiments = analyze_batch_sentiment(texts)

    # 4. 키워드 추출
    keywords_raw = extract_keywords(texts, top_n=8)
    keywords = [NewsKeyword(**k) for k in keywords_raw]

    # 5. 종합 감성 점수
    overall = compute_overall_sentiment(sentiments)

    # 6. 기사별 감성 결합
    articles = []
    for a, s in zip(all_articles, sentiments):
        articles.append(NewsArticle(
            title=a["title"],
            link=a["link"],
            source=a["source"],
            pub_date=a["pub_date"],
            sentiment=s["label"],
            sentiment_score=s["score"],
        ))

    # 최대 10개만 반환
    return NewsTrendResponse(
        area_name=area_name,
        query=queries[0],
        overall_score=overall["score"],
        overall_label=overall["label"],
        positive_count=overall["positive"],
        negative_count=overall["negative"],
        neutral_count=overall["neutral"],
        keywords=keywords,
        articles=articles[:10],
    )
