import requests
import os
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()
FRED_API_KEY = os.getenv("FRED_API_KEY")
BOK_API_KEY = os.getenv("BOK_API_KEY")

# ===== FRED 지표 (수정된 시리즈 ID) =====
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
    "미국 기준금리":        {"unit": "%", "guide": "5%↑ 고금리 / 3%↓ 완화적"},
    "미국 10년물 국채금리": {"unit": "%", "guide": "4%↑ 주식부담 / 3%↓ 우호적"},
    "미국 2년물 국채금리":  {"unit": "%", "guide": "10년물보다 높으면 경기침체 신호"},
    "달러인덱스 DXY":       {"unit": "pt", "guide": "100↑ 강달러 / 95↓ 약달러"},
    "WTI 원유":             {"unit": "$", "guide": "60↓ 침체우려 / 90↑ 인플레압박"},
    "VIX 공포지수":         {"unit": "pt", "guide": "15↓ 안정 / 20~30 불안 / 30↑ 공포"},
    "미국 CPI":             {"unit": "%", "guide": "2% 목표 / 3%↑ 금리인하 지연"},
    "한국 기준금리":        {"unit": "%", "guide": "미국 금리차 비교 중요"},
    "금 가격":              {"unit": "$", "guide": "상승=안전자산선호 / 불확실성증가"},
    "구리 가격":            {"unit": "$", "guide": "상승=경기확장 / 하락=경기위축 선행"},
}

def fetch_fred(series_id, label):
    """FRED API에서 최신 지표값 가져오기"""
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 5,  # 여유있게 가져와서 유효값 탐색
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

            return {
                "label": label,
                "value": latest_val,
                "change": change_str,
                "date": latest["date"],
            }

        elif len(obs) == 1:
            return {
                "label": label,
                "value": float(obs[0]["value"]),
                "change": "N/A",
                "date": obs[0]["date"],
            }

    except Exception as e:
        print(f"[오류] {label}: {e}")

    return {"label": label, "value": None, "change": "N/A", "date": "N/A"}

def fetch_yfinance_indicators():
    """yfinance로 금, 구리 가격 수집 (FRED 대체)"""
    results = []
    targets = {
        "금 가격":  "GC=F",   # 금 선물
        "구리 가격": "HG=F",  # 구리 선물
    }

    for label, ticker in targets.items():
        try:
            data = yf.Ticker(ticker)
            hist = data.history(period="5d")

            if len(hist) >= 2:
                latest_val = round(hist["Close"].iloc[-1], 2)
                prev_val = round(hist["Close"].iloc[-2], 2)
                change = round(latest_val - prev_val, 2)
                change_str = f"+{change}" if change > 0 else str(change)
                date = str(hist.index[-1].date())
            else:
                latest_val = round(hist["Close"].iloc[-1], 2)
                change_str = "N/A"
                date = str(hist.index[-1].date())

            results.append({
                "label": label,
                "value": latest_val,
                "change": change_str,
                "date": date,
            })
            print(f"✅ {label}: {latest_val} ({change_str}) [{date}]")

        except Exception as e:
            print(f"❌ {label}: {e}")
            results.append({"label": label, "value": None, "change": "N/A", "date": "N/A"})

    return results

def fetch_bok_rate():
    """한국은행 ECOS API로 기준금리 최신값 수집"""
    try:
        url = (
            f"https://ecos.bok.or.kr/api/StatisticSearch/{BOK_API_KEY}/json/kr"
            f"/1/100/722Y001/M/202301/209912/0101000"
            #  ↑ 1/1 → 1/100 으로 변경 (최대 100개 가져와서 마지막값 사용)
        )
        res = requests.get(url, timeout=10)
        data = res.json()
        items = data.get("StatisticSearch", {}).get("row", [])

        if items:
            latest = items[-1]  # 마지막 = 최신
            prev = items[-2] if len(items) >= 2 else None

            value = float(latest["DATA_VALUE"])
            date = latest["TIME"]
            date_str = f"{date[:4]}-{date[4:6]}"

            # 전월 대비 변화
            if prev:
                prev_val = float(prev["DATA_VALUE"])
                change = round(value - prev_val, 2)
                change_str = f"+{change}" if change > 0 else str(change)
            else:
                change_str = "N/A"

            print(f"✅ 한국 기준금리: {value}% ({change_str}) [{date_str}]")
            return {
                "label": "한국 기준금리",
                "value": value,
                "change": change_str,
                "date": date_str,
            }

    except Exception as e:
        print(f"❌ 한국 기준금리: {e}")

    return {"label": "한국 기준금리", "value": None, "change": "N/A", "date": "N/A"}

def fetch_all_indicators():
    """전체 경제지표 수집"""
    print("📊 경제지표 수집 시작...\n")
    results = []

    # FRED 지표 수집
    for label, series_id in FRED_INDICATORS.items():
        data = fetch_fred(series_id, label)
        results.append(data)
        if data["value"]:
            print(f"✅ {label}: {data['value']} ({data['change']}) [{data['date']}]")
        else:
            print(f"❌ {label}: 데이터 없음")

    # yfinance로 금/구리 수집
    results += fetch_yfinance_indicators()
    # yfinance 수집 아래에 추가
    results.append(fetch_bok_rate())

    return results

def format_for_ai(indicators):
    """AI 분석용 텍스트 변환 (해석 기준 포함)"""
    lines = ["[경제지표 요약 및 해석 기준]"]

    for d in indicators:
        guide = INDICATOR_GUIDE.get(d["label"], {})
        unit = guide.get("unit", "")
        interpretation = guide.get("guide", "")

        if d["value"]:
            lines.append(
                f"- {d['label']}: {d['value']}{unit} (전일比 {d['change']}) "
                f"| 기준: {interpretation} | {d['date']}"
            )
        else:
            lines.append(f"- {d['label']}: 데이터 없음 | 기준: {interpretation}")

    return "\n".join(lines)

if __name__ == "__main__":
    indicators = fetch_all_indicators()
    print("\n===== AI 전달용 요약 (해석 기준 포함) =====")
    print(format_for_ai(indicators))