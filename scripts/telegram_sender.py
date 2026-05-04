import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ===== 단일 메시지 전송 (4096자 제한) =====
def send_message(text: str) -> bool:
    """텔레그램 메시지 전송"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    try:
        res = requests.post(url, data=data)
        result = res.json()
        if result.get("ok"):
            print("  ✅ 전송 성공")
            return True
        else:
            print(f"  ❌ 전송 실패: {result}")
            return False
    except Exception as e:
        print(f"  ❌ 전송 오류: {e}")
        return False


# ===== 메시지 분할 전송 =====
def split_message(message: str) -> list:
    """
    메시지를 애널리스트 단위로 분할
    텔레그램 최대 4096자 제한
    """
    MAX_LEN = 4000

    markers = [
        "🇺🇸 마이크의 분석",
        "🇰🇷 지훈의 분석",
        "⚖️ 알렉스의 최종 결정",
    ]

    positions = []
    for marker in markers:
        idx = message.find(marker)
        if idx != -1:
            positions.append(idx)

    if not positions:
        return [message[i:i+MAX_LEN] for i in range(0, len(message), MAX_LEN)]

    raw_parts = []
    positions.append(len(message))

    header = message[:positions[0]].strip()
    if header:
        raw_parts.append(header)

    for i in range(len(positions) - 1):
        part = message[positions[i]:positions[i+1]].strip()
        if part:
            raw_parts.append(part)

    # 각 파트 4000자 초과 시 추가 분할
    final_parts = []
    for part in raw_parts:
        if len(part) <= MAX_LEN:
            final_parts.append(part)
        else:
            sub_parts = []
            current = ""
            for line in part.split("\n"):
                if len(current) + len(line) + 1 <= MAX_LEN:
                    current += line + "\n"
                else:
                    if current:
                        sub_parts.append(current.strip())
                    current = line + "\n"
            if current:
                sub_parts.append(current.strip())
            final_parts.extend(sub_parts)

    return final_parts


# ===== 통합 전송 함수 (main.py에서 호출) =====
def send_report(message: str) -> bool:
    """
    분석 리포트 전송
    애널리스트 단위로 분할해서 순서대로 전송
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 없습니다.")
        return False

    parts = split_message(message)
    total = len(parts)
    print(f"📨 총 {total}개 파트로 분할 전송")

    success = True
    for i, part in enumerate(parts, 1):
        print(f"  전송 중 ({i}/{total}) — {len(part)}자")
        if not send_message(part):
            success = False

    return success


# ===== 테스트 실행 =====
if __name__ == "__main__":
    print("=" * 50)
    print("📱 텔레그램 전송 테스트")
    print("=" * 50)

    test_msg = """📊 주식 어시스턴트 리포트
🕐 2025-05-04 06:00 KST

🇺🇸 마이크의 분석
- NVDA (엔비디아) | 목표가 $145 | 손절가 $132
- ETF: SOXL | 반도체 강세

🇰🇷 지훈의 분석
- 005930 (삼성전자) | 목표가 75,000원 | 손절가 69,000원
- ETF: EWY | 한국ETF

⚖️ 알렉스의 최종 결정
- 최종 추천: 삼성전자 / NVDA / SOXL
- 📈 시장 방향: 기술주 강세 지속
- 🔥 주목 섹터: 반도체, AI
- ⚠️ 핵심 리스크: 미중 무역분쟁

⚠️ 투자 참고용입니다."""

    send_report(test_msg)