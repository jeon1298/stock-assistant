import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# ===== 스크리닝 기준 =====
SCREEN_CONFIG = {
    "volume_ratio": 2.0,
    "rsi_oversold": 35,
    "rsi_overbought": 70,
    "min_change_pct": 2.0,
    "max_stocks_per_market": 10,
}

# ===== 티커 → 회사명 매핑 =====
TICKER_NAMES = {
    # 미국
    "AAPL": "애플", "MSFT": "마이크로소프트", "NVDA": "엔비디아", "AMZN": "아마존",
    "GOOGL": "구글", "META": "메타", "TSLA": "테슬라", "BRK-B": "버크셔해서웨이",
    "UNH": "유나이티드헬스", "XOM": "엑슨모빌", "JPM": "JP모건", "V": "비자",
    "LLY": "일라이릴리", "AVGO": "브로드컴", "MA": "마스터카드", "HD": "홈디포",
    "CVX": "셰브론", "MRK": "머크", "ABBV": "애브비", "COST": "코스트코",
    "PEP": "펩시코", "ADBE": "어도비", "KO": "코카콜라", "WMT": "월마트",
    "BAC": "뱅크오브아메리카", "CRM": "세일즈포스", "TMO": "써모피셔", "MCD": "맥도날드",
    "CSCO": "시스코", "ACN": "액센츄어", "ABT": "애보트", "PFE": "화이자",
    "LIN": "린데", "DHR": "다나허", "TXN": "텍사스인스트루먼트", "NKE": "나이키",
    "NFLX": "넷플릭스", "AMD": "AMD", "PM": "필립모리스", "INTC": "인텔",
    "QCOM": "퀄컴", "ORCL": "오라클", "UPS": "UPS", "HON": "하니웰",
    "MS": "모건스탠리", "RTX": "RTX", "AMGN": "암젠", "LOW": "로우스",
    "NEE": "넥스트에라에너지", "IBM": "IBM", "INTU": "인튜이트", "CAT": "캐터필러",
    "GS": "골드만삭스", "SPGI": "S&P글로벌", "ELV": "엘레반스헬스", "AMAT": "어플라이드머티리얼즈",
    "BKNG": "부킹홀딩스", "AXP": "아메리칸익스프레스", "DE": "존디어", "GILD": "길리어드",
    "ADI": "아날로그디바이스", "MDLZ": "몬델리즈", "BLK": "블랙록", "ADP": "ADP",
    "REGN": "리제네론", "VRTX": "버텍스파마", "MMC": "마쉬맥레넌", "SYK": "스트라이커",
    "ZTS": "조에티스", "ISRG": "인튜이티브서지컬", "PLD": "프로로지스", "CI": "시그나",
    "MO": "알트리아", "TJX": "TJX", "LRCX": "램리서치", "EOG": "EOG리소시스",
    "BSX": "보스턴사이언티픽", "SO": "서던컴퍼니", "ETN": "이튼", "SCHW": "찰스슈왑",
    "D": "도미니언에너지", "CME": "CME그룹", "SLB": "슐럼버거", "F": "포드",
    "GM": "GM", "HUM": "휴마나", "DUK": "듀크에너지", "CL": "콜게이트",
    "NOC": "노스롭그루먼", "GE": "GE에어로스페이스", "TSM": "TSMC", "ASML": "ASML",
    "SNY": "사노피", "NVO": "노보노디스크", "TM": "도요타", "SHEL": "쉘",
    "AZN": "아스트라제네카", "RY": "로열뱅크캐나다", "SAP": "SAP", "BHP": "BHP",
    # 한국 KOSPI
    "005930": "삼성전자", "000660": "SK하이닉스", "005380": "현대차", "035420": "NAVER",
    "005490": "POSCO홀딩스", "000270": "기아", "068270": "셀트리온", "105560": "KB금융",
    "055550": "신한지주", "012330": "현대모비스", "028260": "삼성물산", "066570": "LG전자",
    "003550": "LG", "096770": "SK이노베이션", "017670": "SK텔레콤", "030200": "KT",
    "086790": "하나금융지주", "032830": "삼성생명", "009150": "삼성전기", "018260": "삼성SDS",
    "011200": "HMM", "010950": "S-Oil", "034020": "두산에너빌리티", "015760": "한국전력",
    "036460": "한국가스공사", "000810": "삼성화재", "033780": "KT&G", "002790": "아모레퍼시픽그룹",
    "010130": "고려아연", "008770": "호텔신라", "009540": "HD한국조선해양", "011170": "롯데케미칼",
    "000100": "유한양행", "004020": "현대제철", "010620": "HD현대미포", "097950": "CJ제일제당",
    "006400": "삼성SDI", "207940": "삼성바이오로직스", "051910": "LG화학", "003490": "대한항공",
    "011780": "금호석유", "009830": "한화솔루션", "000120": "CJ대한통운", "001800": "오리온홀딩스",
    "010140": "삼성중공업", "002380": "KCC", "004170": "신세계", "006280": "녹십자",
    "001040": "CJ", "011790": "SKC", "047050": "포스코인터내셔널", "029780": "삼성카드",
    "003410": "쌍용C&E", "016360": "삼성증권", "018880": "한온시스템", "000080": "하이트진로",
    "002720": "롯데칠성", "001570": "금양", "007070": "GS리테일", "005940": "NH투자증권",
    # 한국 KOSDAQ
    "247540": "에코프로비엠", "086520": "에코프로", "196170": "알테오젠", "091990": "셀트리온헬스케어",
    "263750": "펄어비스", "293490": "카카오게임즈", "035900": "JYP엔터", "122870": "와이지엔터",
    "041510": "에스엠", "357780": "솔브레인", "145020": "휴젤", "112040": "위메이드",
    "066970": "엘앤에프", "039030": "이오테크닉스", "067160": "SOOP", "058470": "리노공업",
    "214150": "클래시스", "031980": "피에스케이", "053800": "안랩", "096530": "씨젠",
    "141080": "레고켐바이오", "236200": "슈프리마", "078600": "대주전자재료", "251270": "넷마블",
    "054620": "APS홀딩스", "064760": "티씨케이", "060280": "큐렉소", "041020": "폴라리스오피스",
    "036830": "솔브레인홀딩스", "091120": "이엠텍", "237690": "에스티팜", "108230": "LX하우시스",
    "319400": "피에스케이홀딩스", "048260": "오스템임플란트", "073640": "테라세미콘",
    "000250": "삼천당제약", "086900": "메디오젠", "950130": "코오롱티슈진",
    "049720": "에이텍", "024840": "KH바텍",
}

def get_company_name(ticker_code):
    """티커 코드로 회사명 반환 (없으면 코드 그대로)"""
    return TICKER_NAMES.get(ticker_code, ticker_code)

# ===== 미국 S&P500 상위 100개 =====
US_WATCHLIST = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B", "UNH", "XOM",
    "JPM", "V", "LLY", "AVGO", "MA", "HD", "CVX", "MRK", "ABBV", "COST",
    "PEP", "ADBE", "KO", "WMT", "BAC", "CRM", "TMO", "MCD", "CSCO", "ACN",
    "ABT", "PFE", "LIN", "DHR", "TXN", "NKE", "NFLX", "AMD", "PM", "INTC",
    "QCOM", "ORCL", "UPS", "HON", "MS", "RTX", "AMGN", "LOW", "NEE", "IBM",
    "INTU", "CAT", "GS", "SPGI", "ELV", "AMAT", "BKNG", "AXP", "DE", "GILD",
    "ADI", "MDLZ", "BLK", "ADP", "REGN", "VRTX", "MMC", "SYK", "ZTS", "ISRG",
    "PLD", "CI", "MO", "TJX", "LRCX", "EOG", "BSX", "SO", "ETN", "SCHW",
    "D", "CME", "SLB", "F", "GM", "HUM", "DUK", "CL", "NOC", "GE",
    "TSM", "ASML", "SNY", "NVO", "TM", "SHEL", "AZN", "RY", "SAP", "BHP",
]

# ===== 한국 100개 워치리스트 =====
KR_WATCHLIST = [
    "005930.KS", "000660.KS", "005380.KS", "035420.KS", "005490.KS",
    "000270.KS", "068270.KS", "105560.KS", "055550.KS", "012330.KS",
    "028260.KS", "066570.KS", "003550.KS", "096770.KS", "017670.KS",
    "030200.KS", "086790.KS", "032830.KS", "009150.KS", "018260.KS",
    "011200.KS", "010950.KS", "034020.KS", "015760.KS", "036460.KS",
    "000810.KS", "033780.KS", "002790.KS", "010130.KS", "008770.KS",
    "009540.KS", "011170.KS", "000100.KS", "004020.KS", "010620.KS",
    "097950.KS", "006400.KS", "207940.KS", "051910.KS", "003490.KS",
    "011780.KS", "009830.KS", "000120.KS", "001800.KS", "010140.KS",
    "002380.KS", "004170.KS", "006280.KS", "001040.KS", "011790.KS",
    "047050.KS", "029780.KS", "003410.KS", "016360.KS", "018880.KS",
    "000080.KS", "002720.KS", "001570.KS", "007070.KS", "005940.KS",
    "247540.KQ", "086520.KQ", "196170.KQ", "091990.KQ", "263750.KQ",
    "293490.KQ", "035900.KQ", "122870.KQ", "041510.KQ", "357780.KQ",
    "145020.KQ", "112040.KQ", "066970.KQ", "039030.KQ", "067160.KQ",
    "058470.KQ", "214150.KQ", "031980.KQ", "053800.KQ", "096530.KQ",
    "141080.KQ", "236200.KQ", "078600.KQ", "251270.KQ", "054620.KQ",
    "064760.KQ", "060280.KQ", "041020.KQ", "036830.KQ", "091120.KQ",
    "237690.KQ", "108230.KQ", "319400.KQ", "048260.KQ", "073640.KQ",
    "000250.KQ", "086900.KQ", "950130.KQ", "049720.KQ", "024840.KQ",
]

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_signal(rsi, change_pct, volume_ratio):
    signals = []
    if rsi <= 35:
        signals.append("과매도반등주목")
    if rsi >= 70:
        signals.append("과매수주의")
    if volume_ratio >= 3.0:
        signals.append("거래량급증")
    if change_pct >= 3.0:
        signals.append("강세")
    if change_pct <= -3.0:
        signals.append("약세")
    return "/".join(signals) if signals else "모니터링"

def screen_stocks(watchlist, market_name, currency="$"):
    print(f"\n{'🇺🇸' if market_name == '미국' else '🇰🇷'} {market_name} 주식 스크리닝 시작...")
    results = []
    total = len(watchlist)

    for i, ticker in enumerate(watchlist, 1):
        try:
            print(f"  [{i}/{total}] {ticker} 처리중...", end="\r")

            data = yf.Ticker(ticker)
            hist = data.history(period="30d")

            if hist is None or hist.empty or len(hist) < 10:
                continue

            latest = hist.iloc[-1]
            prev = hist.iloc[-2]

            if prev["Close"] == 0:
                continue

            change_pct = round((latest["Close"] - prev["Close"]) / prev["Close"] * 100, 2)
            avg_volume = hist["Volume"].iloc[-6:-1].mean()
            volume_ratio = round(latest["Volume"] / avg_volume, 2) if avg_volume > 0 else 0

            rsi_series = calc_rsi(hist["Close"])
            if rsi_series.isna().iloc[-1]:
                continue
            rsi = round(rsi_series.iloc[-1], 1)

            cfg = SCREEN_CONFIG
            is_volume = volume_ratio >= cfg["volume_ratio"]
            is_rsi = rsi <= cfg["rsi_oversold"] or rsi >= cfg["rsi_overbought"]
            is_change = abs(change_pct) >= cfg["min_change_pct"]

            if is_volume or is_rsi or is_change:
                # ✅ 핵심 변경: 티커 코드에서 .KS/.KQ 제거 후 회사명 조회
                display_ticker = ticker.replace(".KS", "").replace(".KQ", "")
                company_name = get_company_name(display_ticker)
                price = round(latest["Close"], 2)
                price_str = f"{int(price)}원" if market_name == "한국" else f"${price}"

                results.append({
                    "ticker": display_ticker,
                    "name": company_name,           # ✅ 회사명 추가
                    "market": market_name,
                    "price_str": price_str,
                    "price": price,
                    "change_pct": change_pct,
                    "volume_ratio": volume_ratio,
                    "rsi": rsi,
                    "signal": get_signal(rsi, change_pct, volume_ratio),
                })

        except Exception:
            continue

    results.sort(key=lambda x: abs(x["change_pct"]), reverse=True)
    top = results[:SCREEN_CONFIG["max_stocks_per_market"]]
    print(f"\n  ✅ {market_name} 스크리닝 완료: {len(results)}개 선별 → 상위 {len(top)}개 전달")
    return top

def format_for_ai(us_stocks, kr_stocks):
    """AI 분석용 텍스트 변환"""
    lines = ["[주식 스크리닝 결과]"]

    lines.append("\n🇺🇸 미국 선별 종목:")
    if us_stocks:
        for s in us_stocks:
            # ✅ "NVDA (엔비디아)" 형태로 출력
            lines.append(
                f"- {s['ticker']} ({s['name']}) | 가격: {s['price_str']} | "
                f"등락: {s['change_pct']}% | 거래량비율: {s['volume_ratio']}x | "
                f"RSI: {s['rsi']} | 신호: {s['signal']}"
            )
    else:
        lines.append("  선별 종목 없음")

    lines.append("\n🇰🇷 한국 선별 종목:")
    if kr_stocks:
        for s in kr_stocks:
            # ✅ "005930 (삼성전자)" 형태로 출력
            lines.append(
                f"- {s['ticker']} ({s['name']}) | 가격: {s['price_str']} | "
                f"등락: {s['change_pct']}% | 거래량비율: {s['volume_ratio']}x | "
                f"RSI: {s['rsi']} | 신호: {s['signal']}"
            )
    else:
        lines.append("  선별 종목 없음")

    return "\n".join(lines)

if __name__ == "__main__":
    us = screen_stocks(US_WATCHLIST, "미국")
    kr = screen_stocks(KR_WATCHLIST, "한국")
    print("\n===== AI 전달용 요약 =====")
    print(format_for_ai(us, kr))