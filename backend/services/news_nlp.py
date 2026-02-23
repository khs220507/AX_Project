"""뉴스 자연어처리 서비스 (로컬 모델, 무료)

- 감성분석: snunlp/KR-FinBert-SC (한국어 금융/비즈니스 감성분석)
- 키워드 추출: kiwipiepy (한국어 형태소 분석기)
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# 모델은 지연 로딩 (첫 요청 시 로드)
_sentiment_pipeline: Any = None
_kiwi: Any = None

# 감성분석 라벨 매핑
LABEL_MAP = {
    "positive": "긍정",
    "negative": "부정",
    "neutral": "중립",
    "LABEL_0": "부정",
    "LABEL_1": "중립",
    "LABEL_2": "긍정",
}


def _get_sentiment_pipeline():
    """감성분석 파이프라인 지연 로딩"""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        logger.info("Loading KR-FinBert-SC sentiment model...")
        try:
            from transformers import pipeline
            _sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="snunlp/KR-FinBert-SC",
                tokenizer="snunlp/KR-FinBert-SC",
                truncation=True,
                max_length=512,
            )
            logger.info("Sentiment model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load sentiment model: {e}")
            _sentiment_pipeline = "FAILED"
    return _sentiment_pipeline if _sentiment_pipeline != "FAILED" else None


def _get_kiwi():
    """kiwipiepy 형태소 분석기 지연 로딩"""
    global _kiwi
    if _kiwi is None:
        logger.info("Loading kiwipiepy...")
        try:
            from kiwipiepy import Kiwi
            _kiwi = Kiwi()
            logger.info("Kiwipiepy loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load kiwipiepy: {e}")
            _kiwi = "FAILED"
    return _kiwi if _kiwi != "FAILED" else None


def analyze_sentiment(text: str) -> dict:
    """단일 텍스트 감성분석"""
    pipe = _get_sentiment_pipeline()
    if pipe is None:
        return {"label": "중립", "score": 0.5}

    try:
        result = pipe(text[:512])[0]
        label = LABEL_MAP.get(result["label"], result["label"])
        return {"label": label, "score": round(result["score"], 3)}
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        return {"label": "중립", "score": 0.5}


def analyze_batch_sentiment(texts: list[str]) -> list[dict]:
    """배치 감성분석"""
    pipe = _get_sentiment_pipeline()
    if pipe is None:
        return [{"label": "중립", "score": 0.5} for _ in texts]

    try:
        truncated = [t[:512] for t in texts]
        results = pipe(truncated, batch_size=8)
        return [
            {"label": LABEL_MAP.get(r["label"], r["label"]), "score": round(r["score"], 3)}
            for r in results
        ]
    except Exception as e:
        logger.error(f"Batch sentiment error: {e}")
        return [{"label": "중립", "score": 0.5} for _ in texts]


def extract_keywords(texts: list[str], top_n: int = 10) -> list[dict]:
    """텍스트에서 핵심 키워드 추출 (명사 빈도 기반)"""
    kiwi = _get_kiwi()
    if kiwi is None:
        return []

    # 불용어
    stopwords = {
        "것", "수", "등", "중", "위", "때", "점", "곳", "말", "일", "더", "달",
        "년", "월", "원", "억", "만", "명", "개", "건", "측", "뉴스", "기자",
        "씨", "대", "전", "후", "이번", "올해", "지난", "최근", "관련",
    }

    noun_counts: dict[str, int] = {}
    for text in texts:
        try:
            tokens = kiwi.tokenize(text)
            for token in tokens:
                # NNG(일반명사), NNP(고유명사)만 추출
                if token.tag in ("NNG", "NNP") and len(token.form) >= 2:
                    word = token.form
                    if word not in stopwords:
                        noun_counts[word] = noun_counts.get(word, 0) + 1
        except Exception:
            continue

    # 빈도 높은 순 정렬
    sorted_keywords = sorted(noun_counts.items(), key=lambda x: x[1], reverse=True)

    return [
        {"keyword": word, "count": count}
        for word, count in sorted_keywords[:top_n]
    ]


def compute_overall_sentiment(sentiments: list[dict]) -> dict:
    """전체 뉴스에 대한 종합 감성 점수 산출"""
    if not sentiments:
        return {"score": 50, "label": "중립", "positive": 0, "negative": 0, "neutral": 0}

    pos_count = sum(1 for s in sentiments if s["label"] == "긍정")
    neg_count = sum(1 for s in sentiments if s["label"] == "부정")
    neu_count = sum(1 for s in sentiments if s["label"] == "중립")
    total = len(sentiments)

    # 긍정 비율 기반 0~100 점수
    # 긍정 = +1, 중립 = 0, 부정 = -1 → 정규화
    raw_score = (pos_count - neg_count) / total  # -1 ~ +1
    score = int((raw_score + 1) * 50)  # 0 ~ 100

    if score >= 60:
        label = "긍정"
    elif score <= 40:
        label = "부정"
    else:
        label = "중립"

    return {
        "score": score,
        "label": label,
        "positive": pos_count,
        "negative": neg_count,
        "neutral": neu_count,
    }
