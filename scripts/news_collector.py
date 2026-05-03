import feedparser
import re
from deep_translator import GoogleTranslator
from datetime import datetime

# ===== 뉴스 RSS 소스 =====
RSS_FEEDS = {
    "한국경제": "https://www.hankyung.com/feed/all-news",
    "연합뉴스_경제": "https://www.yna.co.kr/rss/economy.xml",
    "매일경제": "https://www.mk.co.kr/rss/40300001/",
    "Yahoo_Finance": "https://finance.yahoo.com/news/rssindex",
    "Reuters_Business": "https://feeds.reuters.com/reuters/businessNews",
    "CNBC": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
}

# ===== 한국어 소스 구분 =====
KOREAN_SOURCES = {"한국경제", "연합뉴스_경제", "매일경제"}

# ===== 정밀 키워드 (단어 단위 매칭) =====
# 한국어: 앞뒤로 한글/영문이 붙지 않는 경우만 매칭
KOREAN_KEYWORDS = [
    "FOMC", "금리", "기준금리", "금리인상", "금리인하",
    "채권", "국채", "금값", "금 가격", "금 선물",
    "원유", "WTI", "유가", "구리 가격", "원자재",
    "달러", "환율", "달러인덱스", "DXY", "VIX", "공포지수",
    "KOSPI", "코스피", "KOSDAQ", "코스닥",
    "외국인 순매수", "외국인 순매도", "기관 매수", "기관 매도",
    "반도체", "수급", "실적 발표", "어닝",
]

# 영어: 단어 경계(\b) 활용
ENGLISH_KEYWORDS = [
    "FOMC", "interest rate", "Fed rate", "rate hike", "rate cut",
    "treasury", "bond yield", "10-year yield",
    "gold price", "crude oil", "WTI", "copper", "commodity",
    "dollar index", "DXY", "VIX", "fear index",
    "Nasdaq", "S&P 500", "Dow Jones",
    "earnings", "revenue", "GDP", "inflation", "CPI", "PPI",
]

def is_korean(text):
    """한글 포함 여부로 한국어 판단"""
    return bool(re.search(r'[가-힣]', text))

def match_korean_keywords(text):
    """한국어 키워드 정밀 매칭 (단어 단위)"""
    matched = []
    for kw in KOREAN_KEYWORDS:
        # 키워드 앞뒤에 한글/영문 숫자가 붙지 않는 경우만 매칭
        pattern = r'(?<![가-힣a-zA-Z0-9])' + re.escape(kw) + r'(?![가-힣a-zA-Z0-9])'
        if re.search(pattern, text):
            matched.append(kw)
    return matched

def match_english_keywords(text):
    """영어 키워드 단어 경계 매칭"""
    matched = []
    for kw in ENGLISH_KEYWORDS:
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            matched.append(kw)
    return matched

def translate_to_korean(text):
    """영어 텍스트 한국어 번역"""
    try:
        translated = GoogleTranslator(source='auto', target='ko').translate(text[:400])
        return translated
    except Exception as e:
        return text  # 번역 실패 시 원문 반환

def fetch_news(max_per_feed=5):
    """RSS에서 뉴스 수집 후 정밀 키워드 필터링"""
    all_news = []

    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            count = 0
            korean_source = source in KOREAN_SOURCES

            for entry in feed.entries:
                if count >= max_per_feed:
                    break

                title = entry.get("title", "")
                summary = entry.get("summary", "")[:300]
                link = entry.get("link", "")
                published = entry.get("published", "")
                content = title + " " + summary

                # 소스별 키워드 매칭
                if korean_source:
                    matched = match_korean_keywords(content)
                else:
                    matched = match_english_keywords(content)

                if matched:
                    # 영어 기사 번역
                    if not korean_source:
                        title_ko = translate_to_korean(title)
                        summary_ko = translate_to_korean(summary)
                    else:
                        title_ko = title
                        summary_ko = summary

                    all_news.append({
                        "source": source,
                        "title": title_ko,
                        "summary": summary_ko[:200],
                        "original_title": title if not korean_source else "",
                        "link": link,
                        "published": published,
                        "keywords": matched[:3],
                    })
                    count += 1

        except Exception as e:
            print(f"[오류] {source}: {e}")

    print(f"✅ 뉴스 수집 완료: 총 {len(all_news)}건")
    return all_news

def format_for_ai(news_list):
    """AI 분석용 텍스트 압축 (토큰 절약)"""
    if not news_list:
        return "수집된 뉴스 없음"

    lines = []
    for i, n in enumerate(news_list[:15], 1):
        lines.append(
            f"{i}. [{n['source']}] {n['title']}\n"
            f"   요약: {n['summary']}\n"
            f"   키워드: {', '.join(n['keywords'])}"
        )
    return "\n\n".join(lines)

if __name__ == "__main__":
    print("🔍 뉴스 수집 시작...\n")
    news = fetch_news()

    print("\n===== 수집된 뉴스 목록 =====")
    for i, n in enumerate(news, 1):
        print(f"{i}. [{n['source']}] {n['title']}")
        print(f"   키워드: {', '.join(n['keywords'])}\n")

    print("\n===== AI 전달용 요약 =====")
    print(format_for_ai(news))