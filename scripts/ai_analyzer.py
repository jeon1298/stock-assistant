import os
import json
import time
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"

# ===== 경로 설정 =====
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SCREENING_FILE = os.path.join(DATA_DIR, "screening_result.json")

# ===== 애널리스트 팀 시스템 프롬프트 (멀티 에셋 버전) =====
ANALYST_SYSTEM_PROMPT = """
당신은 3명의 애널리스트로 구성된 멀티 에셋 투자 분석 팀입니다.
단기 스윙 트레이딩(2~5일) 전문이며 한국/미국 종목을 50:50 비율로 분석합니다.
분석 대상: 주식(한국/미국), 원자재, 채권 ETF, 달러/환율, 섹터 ETF
이미 1차 필터링(거래량, RSI, 모멘텀)을 통과한 데이터가 입력됩니다.

---

👤 애널리스트 1 — 마이크 (Mike, 미국)
- 미국 중심 사고방식
- S&P500, 나스닥, 연준 정책, 달러 흐름을 기준으로 판단
- 글로벌 매크로가 미국 시장에 미치는 영향 우선 분석
- 한국 종목도 미국 수출/반도체/공급망 연계 관점으로 평가
- 원자재/채권은 미국 금리·달러 사이클 관점에서 해석

👤 애널리스트 2 — 지훈 (한국)
- 한국 중심 사고방식
- KOSPI/KOSDAQ 수급, 외국인/기관 동향, 환율 민감도 우선 분석
- 미국 종목도 한국 경제/수출 영향 관점으로 평가
- 국내 정책, 실적 시즌, 테마주 흐름 반영
- 원자재/채권은 원/달러 환율 및 국내 수입물가 관점에서 해석

👤 팀장 — 알렉스 (Alex, 중립국 스위스 출신)
- 마이크와 지훈의 분석을 종합
- 어느 한쪽에 치우치지 않고 리스크/기회를 균형있게 판단
- 최종 추천 종목과 의견 불일치 시 중재 역할
- 최종 결론 및 투자 판단 제시
- 주식 외 자산(원자재/채권ETF/달러/섹터ETF)에 대한 멀티 에셋 보조 추천 권한 보유
- 현재 매크로 환경을 종합하여 포트폴리오 헤지 또는 기회 자산 제안 가능

---

출력 형식:

🇺🇸 마이크의 분석
- 미국 추천 종목 (최대 2개): 종목명/티커 | 이유 | 목표가 | 손절가
- 원자재/달러 코멘트 (1줄): 미국 금리·달러 사이클 관점
- 한국 종목 코멘트 (1줄)

🇰🇷 지훈의 분석
- 한국 추천 종목 (최대 2개): 종목명/코드 | 이유 | 목표가 | 손절가
- 원자재/환율 코멘트 (1줄): 원/달러 및 수입물가 관점
- 미국 종목 코멘트 (1줄)

⚖️ 알렉스의 최종 결정
▶ 주식 최종 추천
- 한국 1~2개 / 미국 1~2개
- 마이크 vs 지훈 의견 차이 요약 (있을 경우)

▶ 멀티 에셋 보조 추천 (해당 시)
- 자산명/티커 | 방향(롱/숏) | 근거 (1줄) | 추천 비중(%)
- 자산명/티커 | 방향(롱/숏) | 근거 (1줄) | 추천 비중(%)
※ 조건: 주식 리스크 높음 / 헤지 필요 / 매크로 이벤트 임박 시 작성
※ 해당 없을 경우: "현재 주식 중심 포지션 유지, 보조 추천 없음"

▶ 이번 분석의 핵심 리스크 (1줄)
▶ 현재 시장 국면 태그: [리스크온 / 리스크오프 / 혼조 / 관망]

---

토큰 절약 원칙:
- 각 애널리스트는 핵심만 간결하게 작성
- 중복 설명 금지
- 수치 근거 위주로 서술
- 멀티 에셋 추천은 매크로 환경이 명확할 때만 작성 (남발 금지)
"""

# ===== 스크리닝 결과 저장 =====
def save_screening_result(us_stocks: list, kr_stocks: list, text: str):
    """스크리닝 결과를 JSON 파일로 저장"""
    os.makedirs(DATA_DIR, exist_ok=True)
    data = {
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "us_stocks": us_stocks,
        "kr_stocks": kr_stocks,
        "text": text,
    }
    with open(SCREENING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 스크리닝 결과 저장 완료: {SCREENING_FILE}")


# ===== 스크리닝 결과 불러오기 =====
def load_screening_result():
    """오늘 저장된 스크리닝 결과 불러오기 (당일만 유효)"""
    if not os.path.exists(SCREENING_FILE):
        return None
    try:
        with open(SCREENING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        saved_date = data["saved_at"].split(" ")[0]
        today = datetime.now().strftime("%Y-%m-%d")
        if saved_date == today:
            print(f"✅ 오늘 스크리닝 결과 로드: {data['saved_at']} 기준")
            return data["text"]
        else:
            print(f"⚠️ 저장된 결과 오래됨 ({saved_date}) → 새로 스크리닝 필요")
            return None
    except Exception as e:
        print(f"⚠️ 스크리닝 결과 로드 실패: {e}")
        return None


# ===== 핵심 함수: 분석만 담당 =====
def analyze_stocks(
    screener_text: str,
    economic_text: str = "",
    news_text: str = "",
    etf_text: str = "",
) -> str:
    """
    수집된 데이터를 받아 Gemini 애널리스트 팀 분석 결과 반환
    데이터 수집은 main.py에서 담당 → 여기선 분석만!

    Args:
        screener_text : stock_screener.format_for_ai() 결과
        economic_text : economic_collector.format_for_ai() 결과
        news_text     : news_collector.format_for_ai() 결과
        etf_text      : ETF 섹터 현황 텍스트
    Returns:
        마이크/지훈/알렉스 팀의 분석 결과 텍스트
    """
    if not GEMINI_API_KEY:
        raise ValueError("❌ GEMINI_API_KEY가 설정되지 않았습니다.")

    # 데이터 통합 (없는 항목은 자동 스킵)
    sections = []
    if screener_text:
        sections.append(screener_text)
    if economic_text:
        sections.append(economic_text)
    if news_text:
        sections.append(news_text)
    if etf_text:
        sections.append(etf_text)

    full_input = "\n\n".join(sections)

    client = genai.Client(api_key=GEMINI_API_KEY)

    for attempt in range(3):
        try:
            print(f"🤖 Gemini 애널리스트 팀 분석 중... (시도 {attempt + 1}/3)")
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=ANALYST_SYSTEM_PROMPT,
                ),
                contents=full_input,
            )
            print("✅ 분석 완료!")
            return response.text

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                if attempt < 2:
                    print("⚠️ 요청 한도 초과 → 30초 후 재시도...")
                    time.sleep(30)
                else:
                    return (
                        "❌ Gemini 한도 초과: 잠시 후 다시 실행해주세요.\n"
                        "💡 내일 오전 자동 리셋됩니다."
                    )
            elif "404" in error_msg:
                return f"❌ 모델 없음: {GEMINI_MODEL}"
            else:
                return f"❌ Gemini 분석 오류: {error_msg}"

    return "❌ 분석 실패: 최대 재시도 횟수 초과"


# ===== 테스트 실행 =====
# main.py 완성 전 단독 테스트용
# main.py 완성 후에는 main.py에서 호출
if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(__file__))

    from stock_screener import screen_stocks, format_for_ai, US_WATCHLIST, KR_WATCHLIST
    import economic_collector as ec
    import news_collector as nc

    # ── 1단계: 스크리닝 ──
    print("=" * 50)
    print("📊 1단계: 스크리닝")
    print("=" * 50)
    screener_text = load_screening_result()
    if screener_text is None:
        print("🔄 새로 스크리닝 시작...")
        us = screen_stocks(US_WATCHLIST, "미국")
        kr = screen_stocks(KR_WATCHLIST, "한국")
        screener_text = format_for_ai(us, kr)
        save_screening_result(us, kr, screener_text)
    print(screener_text)

    # ── 2단계: 경제지표 수집 ──
    print("\n" + "=" * 50)
    print("📊 2단계: 경제지표 수집")
    print("=" * 50)
    try:
        indicators = ec.fetch_all_indicators()
        economic_text = ec.format_for_ai(indicators)
        print(economic_text)
    except Exception as e:
        economic_text = ""
        print(f"⚠️ 경제지표 수집 실패: {e}")

    # ── 3단계: 뉴스 수집 ──
    print("\n" + "=" * 50)
    print("📰 3단계: 뉴스 수집")
    print("=" * 50)
    try:
        news_list = nc.fetch_news(max_per_feed=3)
        news_text = nc.format_for_ai(news_list)
        print(news_text)
    except Exception as e:
        news_text = ""
        print(f"⚠️ 뉴스 수집 실패: {e}")

    # ── 4단계: ETF 현황 ──
    print("\n" + "=" * 50)
    print("📈 4단계: ETF 현황")
    print("=" * 50)
    try:
        import yfinance as yf
        ETF_WATCHLIST = {
            "금/원자재": ["GLD", "SLV", "GDX", "USO", "DBC"],
            "반도체":    ["SOXL", "SOXX", "SMH"],
            "AI/기술":   ["TQQQ", "QQQ", "BOTZ", "ARKK"],
            "방산":      ["ITA", "XAR", "DFEN"],
            "신재생에너지": ["ICLN", "TAN", "QCLN"],
            "우주":      ["UFO", "ARKX"],
            "양자컴퓨팅": ["QTUM"],
            "한국ETF":   ["EWY"],
        }
        etf_lines = ["\n[ETF/레버리지 섹터 현황]"]
        for sector, tickers in ETF_WATCHLIST.items():
            sector_data = []
            for ticker in tickers:
                try:
                    hist = yf.Ticker(ticker).history(period="2d")
                    if hist.empty or len(hist) < 2:
                        continue
                    price = round(hist.iloc[-1]["Close"], 2)
                    change = round(
                        (hist.iloc[-1]["Close"] - hist.iloc[-2]["Close"])
                        / hist.iloc[-2]["Close"] * 100, 2
                    )
                    sector_data.append(f"{ticker} ${price} ({change:+.2f}%)")
                except:
                    continue
            if sector_data:
                etf_lines.append(f"  {sector}: {' | '.join(sector_data)}")
        etf_text = "\n".join(etf_lines)
        print(etf_text)
    except Exception as e:
        etf_text = ""
        print(f"⚠️ ETF 수집 실패: {e}")

    # ── 5단계: Gemini 분석 ──
    print("\n" + "=" * 50)
    print("🤖 5단계: 애널리스트 팀 분석")
    print("=" * 50)
    result = analyze_stocks(
        screener_text=screener_text,
        economic_text=economic_text,
        news_text=news_text,
        etf_text=etf_text,
    )
    print(result)