import os
import json
import yfinance as yf
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ===== 경로 설정 =====
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
WATCHLIST_FILE = os.path.join(DATA_DIR, "watchlist.json")

# ===== 기본 하드코딩 리스트 (폴백용) =====
DEFAULT_US = [
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

DEFAULT_KR = [
    # KOSPI
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
    # KOSDAQ
    "247540.KQ", "086520.KQ", "196170.KQ", "091990.KQ", "263750.KQ",
    "293490.KQ", "035900.KQ", "122870.KQ", "041510.KQ", "357780.KQ",
    "145020.KQ", "112040.KQ", "066970.KQ", "039030.KQ", "067160.KQ",
    "058470.KQ", "214150.KQ", "031980.KQ", "053800.KQ", "096530.KQ",
    "141080.KQ", "236200.KQ", "078600.KQ", "251270.KQ", "054620.KQ",
    "064760.KQ", "060280.KQ", "041020.KQ", "036830.KQ", "091120.KQ",
    "237690.KQ", "108230.KQ", "319400.KQ", "048260.KQ", "073640.KQ",
    "000250.KQ", "086900.KQ", "950130.KQ", "049720.KQ", "024840.KQ",
]

# ===== 유효성 검사 =====
def validate_tickers(ticker_list, sample_size=10):
    """
    yfinance로 티커 샘플 유효성 검사
    샘플의 80% 이상 유효하면 통과
    """
    sample = ticker_list[:sample_size]
    valid_count = 0
    print(f"  🔍 유효성 검사 중 (샘플 {sample_size}개)...")

    for ticker in sample:
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            if not hist.empty:
                valid_count += 1
        except:
            continue

    ratio = valid_count / sample_size
    print(f"  결과: {valid_count}/{sample_size} 유효 ({ratio*100:.0f}%)")
    return ratio >= 0.8

# ===== 저장 / 불러오기 =====
def save_watchlist(us_list, kr_list):
    """워치리스트를 JSON 파일로 저장"""
    os.makedirs(DATA_DIR, exist_ok=True)
    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d"),
        "us": us_list,
        "kr": kr_list,
    }
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  💾 저장 완료: {WATCHLIST_FILE}")

def load_watchlist():
    """
    저장된 워치리스트 불러오기
    없거나 오류 시 하드코딩 기본값 반환
    """
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"  ✅ 워치리스트 로드 성공: {data['updated_at']} 기준")
            return data["us"], data["kr"]
        except Exception as e:
            print(f"  ⚠️ 워치리스트 파일 오류: {e} → 기본값 사용")
    else:
        print("  ⚠️ 저장된 워치리스트 없음 → 기본값 사용")

    return DEFAULT_US, DEFAULT_KR

# ===== 월간 업데이트 여부 확인 =====
def needs_update():
    """
    마지막 업데이트가 이번 달인지 확인
    이번 달에 업데이트 안 했으면 True 반환
    """
    if not os.path.exists(WATCHLIST_FILE):
        return True
    try:
        with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        last = datetime.strptime(data["updated_at"], "%Y-%m-%d")
        now = datetime.now()
        # 이번 달에 이미 업데이트했으면 스킵
        if last.year == now.year and last.month == now.month:
            print(f"  ℹ️ 이번 달 이미 업데이트됨 ({data['updated_at']}) → 스킵")
            return False
    except:
        pass
    return True

# ===== 메인 업데이트 함수 =====
def update_watchlist(force=False):
    """
    워치리스트 업데이트 (매월 1일 호출)

    Args:
        force: True면 날짜 무관하게 강제 업데이트
    Returns:
        (us_list, kr_list) 튜플
    """
    print("\n📋 워치리스트 업데이트 확인 중...")

    if not force and not needs_update():
        return load_watchlist()

    print("  🔄 업데이트 시작...")

    us_ok = validate_tickers(DEFAULT_US)
    kr_ok = validate_tickers(DEFAULT_KR)

    if us_ok and kr_ok:
        save_watchlist(DEFAULT_US, DEFAULT_KR)
        print("  ✅ 워치리스트 업데이트 완료")
        return DEFAULT_US, DEFAULT_KR
    else:
        print("  ⚠️ 유효성 검사 실패 → 기존 리스트 유지")
        return load_watchlist()


# ===== 테스트 실행 =====
if __name__ == "__main__":
    print("=" * 50)
    print("🔄 워치리스트 업데이터 테스트")
    print("=" * 50)

    # 강제 업데이트 테스트
    us, kr = update_watchlist(force=True)

    print(f"\n미국 종목 수: {len(us)}개")
    print(f"한국 종목 수: {len(kr)}개")
    print(f"미국 샘플: {us[:5]}")
    print(f"한국 샘플: {kr[:5]}")