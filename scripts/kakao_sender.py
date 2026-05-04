import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

KAKAO_ACCESS_TOKEN = os.getenv("KAKAO_ACCESS_TOKEN")
KAKAO_REFRESH_TOKEN = os.getenv("KAKAO_REFRESH_TOKEN")
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")


# ===== 토큰 갱신 =====
def refresh_access_token() -> bool:
    global KAKAO_ACCESS_TOKEN
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": KAKAO_REST_API_KEY,
        "refresh_token": KAKAO_REFRESH_TOKEN,
    }
    try:
        res = requests.post(url, data=data)
        result = res.json()
        if "access_token" in result:
            KAKAO_ACCESS_TOKEN = result["access_token"]
            env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
            with open(env_path, "r") as f:
                lines = f.readlines()
            with open(env_path, "w") as f:
                for line in lines:
                    if line.startswith("KAKAO_ACCESS_TOKEN="):
                        f.write(f"KAKAO_ACCESS_TOKEN={result['access_token']}\n")
                    elif line.startswith("KAKAO_REFRESH_TOKEN=") and "refresh_token" in result:
                        f.write(f"KAKAO_REFRESH_TOKEN={result['refresh_token']}\n")
                    else:
                        f.write(line)
            print("✅ Access Token 갱신 완료")
            return True
        else:
            print(f"❌ 토큰 갱신 실패: {result}")
            return False
    except Exception as e:
        print(f"❌ 토큰 갱신 오류: {e}")
        return False

# ===== 통합 전송 함수 =====
def send_report(message: str) -> bool:
    if not KAKAO_ACCESS_TOKEN:
        print("❌ KAKAO_ACCESS_TOKEN이 없습니다.")
        return False

    # GitHub Actions 환경에서는 매번 토큰 갱신
    print("🔄 토큰 갱신 중...")
    refresh_access_token()

    parts = split_message(message)
    total = len(parts)
    print(f"📨 총 {total}개 파트로 분할 전송")

    success = True
    for i, part in enumerate(parts, 1):
        print(f"  전송 중 ({i}/{total}) — {len(part)}자")
        if not send_to_me(part):
            success = False

    return success

# ===== 단일 메시지 전송 (2000자 제한) =====
def send_to_me(message: str) -> bool:
    """
    카카오톡 나에게 보내기
    message는 반드시 2000자 이하로 넘겨야 함
    """
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {
        "Authorization": f"Bearer {KAKAO_ACCESS_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    template = {
        "object_type": "text",
        "text": message,   # ← 자르지 않음! 호출하는 쪽에서 2000자 보장
        "link": {"web_url": "", "mobile_web_url": ""},
    }
    data = {"template_object": json.dumps(template)}

    try:
        res = requests.post(url, headers=headers, data=data)
        result = res.json()

        if res.status_code == 200:
            print("  ✅ 전송 성공")
            return True
        elif result.get("code") == -401:
            print("  ⚠️ 토큰 만료 → 자동 갱신 후 재시도")
            if refresh_access_token():
                return send_to_me(message)
            return False
        else:
            print(f"  ❌ 전송 실패: {result}")
            return False

    except Exception as e:
        print(f"  ❌ 전송 오류: {e}")
        return False


# ===== 메시지 분할 함수 =====
def split_message(message: str) -> list:
    """
    메시지를 애널리스트 단위로 분할
    각 파트가 2000자 초과 시 추가 분할
    """
    # 분할 기준 마커
    markers = [
        "🇺🇸 마이크의 분석",
        "🇰🇷 지훈의 분석",
        "⚖️ 알렉스의 최종 결정",
    ]

    # 마커 위치 찾기
    positions = []
    for marker in markers:
        idx = message.find(marker)
        if idx != -1:
            positions.append(idx)

    # 마커 없으면 강제 분할
    if not positions:
        return [message[i:i+1900] for i in range(0, len(message), 1900)]

    # 마커 기준으로 파트 분리
    raw_parts = []
    positions.append(len(message))  # 끝 위치 추가

    # 헤더 (첫 마커 이전)
    header = message[:positions[0]].strip()
    if header:
        raw_parts.append(header)

    # 각 섹션
    for i in range(len(positions) - 1):
        part = message[positions[i]:positions[i+1]].strip()
        if part:
            raw_parts.append(part)

    # 각 파트가 2000자 초과 시 추가 분할
    final_parts = []
    for part in raw_parts:
        if len(part) <= 1900:
            final_parts.append(part)
        else:
            # 2000자 초과 시 줄바꿈 기준으로 분할
            sub_parts = []
            current = ""
            for line in part.split("\n"):
                if len(current) + len(line) + 1 <= 1900:
                    current += line + "\n"
                else:
                    if current:
                        sub_parts.append(current.strip())
                    current = line + "\n"
            if current:
                sub_parts.append(current.strip())
            final_parts.extend(sub_parts)

    return final_parts


# ===== 통합 전송 함수 =====
def send_report(message: str) -> bool:
    """
    분석 리포트 전송
    애널리스트 단위로 분할해서 순서대로 전송
    """
    if not KAKAO_ACCESS_TOKEN:
        print("❌ KAKAO_ACCESS_TOKEN이 없습니다.")
        return False

    parts = split_message(message)
    total = len(parts)
    print(f"📨 총 {total}개 파트로 분할 전송")

    success = True
    for i, part in enumerate(parts, 1):
        print(f"  전송 중 ({i}/{total}) — {len(part)}자")
        if not send_to_me(part):
            success = False

    return success


# ===== 테스트 실행 =====
if __name__ == "__main__":
    print("=" * 50)
    print("📱 카카오 전송 테스트")
    print("=" * 50)

    test_msg = """📊 주식 어시스턴트 리포트
🕐 2025-05-04 06:00 KST

🇺🇸 마이크의 분석
- 미국 추천 종목: NVDA (엔비디아) | RSI 68, 거래량 3.2x 강세 | 목표가 $145 | 손절가 $132
- ETF 추천: SOXL | 반도체 | AI 수요 지속 강세
- 한국 코멘트: 삼성전자 반도체 수출 호조로 연동 상승 기대

🇰🇷 지훈의 분석
- 한국 추천 종목: 005930 (삼성전자) | 외국인 순매수 지속 | 목표가 75,000원 | 손절가 69,000원
- ETF 추천: EWY | 한국ETF | 원화 강세 + 반도체 호조
- 미국 코멘트: 나스닥 강세 지속 시 국내 기술주 동반 상승 가능

⚖️ 알렉스의 최종 결정
- 최종 추천: 삼성전자 / NVDA / SOXL
- 의견 차이: 없음, 반도체 동반 강세 동의
- 📈 시장 방향: 연준 금리 동결 기조 유지로 기술주 강세 지속 예상
- 🔥 주목 섹터: 반도체, AI
- ⚠️ 핵심 리스크: 미중 무역분쟁 재점화 가능성

⚠️ 본 내용은 투자 참고용이며 투자 결정의 책임은 본인에게 있습니다."""

    send_report(test_msg)