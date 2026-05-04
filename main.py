import os
import sys
import json
from datetime import datetime, timezone, timedelta
from dashboard_generator import generate_all

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))

from stock_screener import screen_stocks, format_for_ai
from ai_analyzer import analyze_stocks, save_screening_result, load_screening_result
from telegram_sender import send_report
from watchlist_updater import load_watchlist, update_watchlist
import economic_collector as ec
import news_collector as nc
import yfinance as yf

# ===== 경로 설정 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ECONOMIC_FILE = os.path.join(DATA_DIR, "economic_result.json")
NEWS_FILE = os.path.join(DATA_DIR, "news_result.json")
ETF_FILE = os.path.join(DATA_DIR, "etf_result.json")

# ===== ETF 워치리스트 =====
ETF_WATCHLIST = {
    "금/원자재":    ["GLD", "SLV", "GDX", "USO", "DBC"],
    "반도체":       ["SOXL", "SOXX", "SMH"],
    "AI/기술":      ["TQQQ", "QQQ", "BOTZ", "ARKK"],
    "방산":         ["ITA", "XAR", "DFEN"],
    "신재생에너지":  ["ICLN", "TAN", "QCLN"],
    "우주":         ["UFO", "ARKX"],
    "양자컴퓨팅":   ["QTUM"],
    "한국ETF":      ["EWY"],
}


# ===== 저장 / 불러오기 유틸 =====
def save_data(filepath: str, text: str, expire_hours: int = 24):
    """데이터를 JSON으로 저장"""
    os.makedirs(DATA_DIR, exist_ok=True)
    data = {
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "expire_hours": expire_hours,
        "text": text,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  💾 저장 완료: {os.path.basename(filepath)}")


def load_data(filepath: str) -> str | None:
    """
    저장된 데이터 불러오기
    유효기간 지나면 None 반환
    """
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        saved_at = datetime.strptime(data["saved_at"], "%Y-%m-%d %H:%M")
        expire_hours = data.get("expire_hours", 24)
        elapsed = (datetime.now() - saved_at).total_seconds() / 3600

        if elapsed < expire_hours:
            print(f"  ✅ 캐시 로드: {os.path.basename(filepath)} ({data['saved_at']} 기준, {elapsed:.1f}시간 경과)")
            return data["text"]
        else:
            print(f"  ⚠️ 캐시 만료: {os.path.basename(filepath)} ({elapsed:.1f}시간 경과) → 새로 수집")
            return None

    except Exception as e:
        print(f"  ⚠️ 캐시 로드 실패: {e}")
        return None


# ===== 월간 워치리스트 갱신 =====
def check_monthly_update():
    """매월 1일이면 워치리스트 자동 갱신"""
    today = datetime.now()
    if today.day == 1:
        print("  📅 매월 1일 → 워치리스트 자동 갱신")
        update_watchlist(force=True)
    else:
        print(f"  📅 오늘은 {today.day}일 → 갱신 스킵")


# ===== ETF 수집 =====
def collect_etf() -> str:
    lines = ["[ETF/레버리지 섹터 현황]"]
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
            lines.append(f"  {sector}: {' | '.join(sector_data)}")
    return "\n".join(lines)


# ===== 메인 실행 =====
def run():
    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST)
    print("=" * 50)
    print(f"🚀 주식 어시스턴트 시작: {now.strftime('%Y-%m-%d %H:%M')} KST")
    print("=" * 50)

    # ── Step 1: 워치리스트 갱신 확인 ──
    print("\n📋 Step 1: 워치리스트 확인")
    check_monthly_update()
    us_watchlist, kr_watchlist = load_watchlist()

    # ── Step 2: 주식 스크리닝 (당일 캐시) ──
    print("\n📊 Step 2: 주식 스크리닝")
    screener_text = load_screening_result()
    if screener_text is None:
        print("  🔄 새로 스크리닝 시작...")
        us = screen_stocks(us_watchlist, "미국")
        kr = screen_stocks(kr_watchlist, "한국")
        screener_text = format_for_ai(us, kr)
        save_screening_result(us, kr, screener_text)
    print(screener_text)

    # ── Step 3: 경제지표 수집 (당일 캐시) ──
    print("\n📊 Step 3: 경제지표 수집")
    economic_text = load_data(ECONOMIC_FILE)
    if economic_text is None:
        try:
            print("  🔄 새로 수집 중...")
            indicators = ec.fetch_all_indicators()
            economic_text = ec.format_for_ai(indicators)
            save_data(ECONOMIC_FILE, economic_text, expire_hours=24)
        except Exception as e:
            economic_text = ""
            print(f"  ⚠️ 경제지표 수집 실패: {e}")
    print(economic_text)

    # ── Step 4: 뉴스 수집 (6시간 캐시) ──
    print("\n📰 Step 4: 뉴스 수집")
    news_text = load_data(NEWS_FILE)
    if news_text is None:
        try:
            print("  🔄 새로 수집 중...")
            news_list = nc.fetch_news(max_per_feed=3)
            news_text = nc.format_for_ai(news_list)
            save_data(NEWS_FILE, news_text, expire_hours=6)
        except Exception as e:
            news_text = ""
            print(f"  ⚠️ 뉴스 수집 실패: {e}")
    print(news_text)

    # ── Step 5: ETF 수집 (당일 캐시) ──
    print("\n📈 Step 5: ETF 현황 수집")
    etf_text = load_data(ETF_FILE)
    if etf_text is None:
        try:
            print("  🔄 새로 수집 중...")
            etf_text = collect_etf()
            save_data(ETF_FILE, etf_text, expire_hours=24)
        except Exception as e:
            etf_text = ""
            print(f"  ⚠️ ETF 수집 실패: {e}")
    print(etf_text)

    # ── Step 6: AI 분석 ──
    print("\n🤖 Step 6: 애널리스트 팀 분석")
    analysis_result = analyze_stocks(
        screener_text=screener_text,
        economic_text=economic_text,
        news_text=news_text,
        etf_text=etf_text,
    )
    print(analysis_result)

    # ── Step 7: 대시보드 생성 ──
    print("\n🌐 Step 7: 대시보드 생성")
    try:
        generate_all(indicators, news_list)
    except Exception as e:
        print(f"  ⚠️ 대시보드 생성 실패: {e}")

    # ── Step 8: 텔레그램 전송 ──
    print("\n📱 Step 8: 텔레그램 전송")
    message = f"""📊 주식 어시스턴트 리포트
🕐 {now.strftime('%Y-%m-%d %H:%M')} KST

{analysis_result}

⚠️ 본 내용은 투자 참고용이며 투자 결정의 책임은 본인에게 있습니다."""

    send_report(message)

    print("\n" + "=" * 50)
    print("✅ 모든 작업 완료!")
    print("=" * 50)


if __name__ == "__main__":
    run()