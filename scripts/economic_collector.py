import requests
import os
import json
import yfinance as yf
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()
FRED_API_KEY = os.getenv("FRED_API_KEY")
BOK_API_KEY = os.getenv("BOK_API_KEY")

# ===== 캐시 경로 =====
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(BASE_DIR, "data", "economic_result.json")

# ===== FRED 지표 =====
FRED_INDICATORS = {
    "미국 기준금리":        "FEDFUNDS",
    "미국 10년물 국채금리": "DGS10",
    "미국 2년물 국채금리":  "DGS2",
    "달러인덱스 DXY":       "DTWEXBGS",
    "WTI 원유":             "DCOILWTICO",
    "VIX 공포지수":         "VIXCLS",
    "미국 CPI":             "CPIAUCSL",
}

# ===== 지표별 해석 기준 =====
INDICATOR_GUIDE = {
    "미국 기준금리":        {"unit": "%",  "guide": "5%↑ 고금리 / 3%↓ 완화적"},
    "미국 10년물 국채금리": {"unit": "%",  "guide": "4%↑ 주식부담 / 3%↓ 우호적"},
    "미국 2년물 국채금리":  {"unit": "%",  "guide": "10년물보다 높으면 경기침체 신호"},
    "달러인덱스 DXY":       {"unit": "pt", "guide": "100↑ 강달러 / 95↓ 약달러"},
    "WTI 원유":             {"unit": "$",  "guide": "60↓ 침체우려 / 60~90 중립 / 90↑ 인플레압박"},
    "VIX 공포지수":         {"unit": "pt", "guide": "15↓ 안정 / 15~20 주의 / 20~30 불안 / 30↑ 공포"},
    "미국 CPI":             {"unit": "pt", "guide": "2% 목표 / 3%↑ 금리인하 지연"},
    "한국 기준금리":        {"unit": "%",  "guide": "미국 금리차 비교 중요"},
    "금 가격":              {"unit": "$",  "guide": "상승=안전자산선호 / 하락=위험자산선호"},
    "구리 가격":            {"unit": "$",  "guide": "상승=경기확장 / 하락=경기위축 선행지표"},
    "원/달러 환율(시가)":   {"unit": "원", "guide": "1200↓ 원화강세 / 1200~1400 중립 / 1400↑ 원화약세"},
    "원/달러 환율(종가)":   {"unit": "원", "guide": "1200↓ 원화강세 / 1200~1400 중립 / 1400↑ 원화약세"},
    "KOSPI":                {"unit": "pt", "guide": "2400↓ 약세 / 2400~2800 중립 / 2800↑ 강세"},
    "S&P500":               {"unit": "pt", "guide": "4000↓ 약세 / 4000~5500 중립 / 5500↑ 강세"},
    "NASDAQ100":            {"unit": "pt", "guide": "기술주 방향 / S&P500 대비 기술주 프리미엄 확인"},
}


# ===== 이전 캐시 불러오기 =====
def load_cache() -> dict:
    """저장된 캐시에서 이전 데이터 불러오기"""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # {label: indicator_dict} 형태로 변환
        cached = {}
        for item in data.get("indicators", []):
            cached[item["label"]] = item
        return cached
    except:
        return {}


# ===== FRED 지표 수집 =====
def fetch_fred(series_id, label):
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 5,
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        obs = [o for o in data.get("observations", []) if o["value"] != "."]

        if len(obs) >= 2:
            latest = obs[0]
            previous = obs[1]
            latest_val = float(latest["value"])
            prev_val = float(previous["value"])
            change = latest_val - prev_val
            change_str = f"+{change:.2f}" if change > 0 else f"{change:.2f}"
            return {"label": label, "value": latest_val, "change": change_str, "date": latest["date"]}

        elif len(obs) == 1:
            return {"label": label, "value": float(obs[0]["value"]), "change": "N/A", "date": obs[0]["date"]}

    except Exception as e:
        print(f"[오류] {label}: {e}")

    return {"label": label, "value": None, "change": "N/A", "date": "N/A"}


# ===== yfinance 지표 수집 =====
def fetch_yfinance_indicators():
    """금, 구리, 원/달러, KOSPI, S&P500, NASDAQ100 수집"""
    results = []
    targets = {
        "금 가격":           ("GC=F",   "close"),
        "구리 가격":         ("HG=F",   "close"),
        "원/달러 환율(시가)": ("KRW=X",  "open"),
        "원/달러 환율(종가)": ("KRW=X",  "close"),
        "KOSPI":             ("^KS11",  "close"),
        "S&P500":            ("^GSPC",  "close"),
        "NASDAQ100":         ("^NDX",   "close"),
    }

    for label, (ticker, price_type) in targets.items():
        try:
            hist = yf.Ticker(ticker).history(period="5d")
            if hist.empty:
                raise ValueError("데이터 없음")

            if price_type == "open":
                latest_val = round(hist["Open"].iloc[-1], 2)
                prev_val   = round(hist["Open"].iloc[-2], 2) if len(hist) >= 2 else latest_val
            else:
                latest_val = round(hist["Close"].iloc[-1], 2)
                prev_val   = round(hist["Close"].iloc[-2], 2) if len(hist) >= 2 else latest_val

            change = round(latest_val - prev_val, 2)
            change_str = f"+{change}" if change > 0 else str(change)
            date = str(hist.index[-1].date())

            results.append({"label": label, "value": latest_val, "change": change_str, "date": date})
            print(f"✅ {label}: {latest_val} ({change_str}) [{date}]")

        except Exception as e:
            print(f"❌ {label}: {e}")
            results.append({"label": label, "value": None, "change": "N/A", "date": "N/A"})

    return results


# ===== 한국은행 기준금리 =====
def fetch_bok_rate():
    try:
        url = (
            f"https://ecos.bok.or.kr/api/StatisticSearch/{BOK_API_KEY}/json/kr"
            f"/1/100/722Y001/M/202301/209912/0101000"
        )
        res = requests.get(url, timeout=10)
        data = res.json()
        items = data.get("StatisticSearch", {}).get("row", [])

        if items:
            latest = items[-1]
            prev = items[-2] if len(items) >= 2 else None
            value = float(latest["DATA_VALUE"])
            date = latest["TIME"]
            date_str = f"{date[:4]}-{date[4:6]}"
            change_str = "N/A"
            if prev:
                change = round(value - float(prev["DATA_VALUE"]), 2)
                change_str = f"+{change}" if change > 0 else str(change)
            print(f"✅ 한국 기준금리: {value}% ({change_str}) [{date_str}]")
            return {"label": "한국 기준금리", "value": value, "change": change_str, "date": date_str}

    except Exception as e:
        print(f"❌ 한국 기준금리: {e}")

    return {"label": "한국 기준금리", "value": None, "change": "N/A", "date": "N/A"}


# ===== 전체 수집 (실패 시 이전 캐시 사용) =====
def fetch_all_indicators():
    """
    전체 경제지표 수집
    수집 실패한 지표는 이전 캐시 값 사용
    """
    print("📊 경제지표 수집 시작...\n")
    cache = load_cache()
    results = []

    # FRED 수집
    for label, series_id in FRED_INDICATORS.items():
        data = fetch_fred(series_id, label)

        # 수집 실패 시 캐시에서 복원
        if data["value"] is None and label in cache:
            data = cache[label].copy()
            data["cached"] = True
            print(f"⚠️  {label}: 수집 실패 → 캐시 사용 ({data['date']})")
        elif data["value"]:
            print(f"✅ {label}: {data['value']} ({data['change']}) [{data['date']}]")
        else:
            print(f"❌ {label}: 데이터 없음")

        results.append(data)

    # yfinance 수집
    for item in fetch_yfinance_indicators():
        if item["value"] is None and item["label"] in cache:
            item = cache[item["label"]].copy()
            item["cached"] = True
            print(f"⚠️  {item['label']}: 수집 실패 → 캐시 사용 ({item['date']})")
        results.append(item)

    # 한국은행 기준금리
    bok = fetch_bok_rate()
    if bok["value"] is None and "한국 기준금리" in cache:
        bok = cache["한국 기준금리"].copy()
        bok["cached"] = True
        print(f"⚠️  한국 기준금리: 수집 실패 → 캐시 사용 ({bok['date']})")
    results.append(bok)

    # 캐시 저장 (성공한 것만 업데이트)
    _save_cache(results)

    return results


# ===== 캐시 저장 =====
def _save_cache(indicators: list):
    """수집 결과 캐시 저장 (성공한 항목만 업데이트)"""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

    # 기존 캐시 불러오기
    old_cache = load_cache()

    # 성공한 항목만 업데이트
    for item in indicators:
        if item.get("value") is not None and not item.get("cached"):
            old_cache[item["label"]] = item

    data = {
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "indicators": list(old_cache.values()),
    }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ===== AI 분석용 텍스트 =====
def format_for_ai(indicators):
    lines = ["[경제지표 요약 및 해석 기준]"]
    for d in indicators:
        guide = INDICATOR_GUIDE.get(d["label"], {})
        unit  = guide.get("unit", "")
        interp = guide.get("guide", "")
        cached_mark = " [이전값]" if d.get("cached") else ""

        if d["value"] is not None:
            lines.append(
                f"- {d['label']}: {d['value']}{unit} (전일比 {d['change']}){cached_mark} "
                f"| 기준: {interp} | {d['date']}"
            )
        else:
            lines.append(f"- {d['label']}: 데이터 없음 | 기준: {interp}")

    return "\n".join(lines)


if __name__ == "__main__":
    indicators = fetch_all_indicators()
    print("\n===== AI 전달용 요약 =====")
    print(format_for_ai(indicators))