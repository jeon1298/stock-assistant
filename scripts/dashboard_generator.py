import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(__file__))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
KST = timezone(timedelta(hours=9))


# ===== 경제지표 카드 생성 =====
def build_cards(indicators: list) -> str:
    cards = ""
    for item in indicators:
        label  = item.get("label", "")
        value  = item.get("value")
        change = item.get("change", "")
        date   = item.get("date", "")

        # 값 없으면 스킵
        if value is None:
            continue

        # 등락 기반 색상
        try:
            change_float = float(str(change).replace("%", ""))
            if change_float > 0:
                color, bg, icon = "#00c896", "rgba(0,200,150,0.08)", "▲"
            elif change_float < 0:
                color, bg, icon = "#ff4d6d", "rgba(255,77,109,0.08)", "▼"
            else:
                color, bg, icon = "#7b8fa6", "rgba(123,143,166,0.08)", "●"
        except:
            color, bg, icon = "#7b8fa6", "rgba(123,143,166,0.08)", "●"

        guide = str(date)

        cards += (
            '<div class="card" style="border-left:3px solid ' + color + ';background:' + bg + ';">'
            '<div class="card-label">' + str(label) + '</div>'
            '<div class="card-value" style="color:' + color + ';">' + icon + ' ' + str(value) + '</div>'
            '<div class="card-guide">변동: ' + str(change) + ' | ' + guide + '</div>'
            '</div>'
        )
    return cards



# ===== 뉴스 카드 생성 =====
def build_news(news_list: list) -> str:
    items = ""
    for item in news_list:
        title    = item.get("title_ko") or item.get("title", "")
        title_orig = item.get("title", "")
        link     = item.get("link", "#")
        source   = item.get("source", "")
        pub_date = item.get("pub_date", "")
        summary  = item.get("summary_ko") or item.get("summary", "")

        is_korean = any(k in source for k in ["연합뉴스", "매일경제", "한국경제"])
        tag_color = "#00c896" if is_korean else "#58a6ff"
        tag_text  = "🇰🇷 한국" if is_korean else "🇺🇸 미국"

        items += (
            '<div class="news-card">'
            '<div class="news-meta">'
            '<span class="tag" style="color:' + tag_color + ';border-color:' + tag_color + ';">' + tag_text + '</span>'
            '<span class="source">' + source + '</span>'
            '<span class="date">' + pub_date + '</span>'
            '</div>'
            '<a href="' + link + '" target="_blank" class="news-title">' + title + '</a>'
            '<div class="news-orig">' + title_orig + '</div>'
            '<div class="news-summary">' + summary + '</div>'
            '</div>'
        )
    return items


# ===== 공통 CSS =====
COMMON_CSS = """
<style>
:root {
  --bg:#0d1117; --surface:#161b22; --border:#30363d;
  --text:#e6edf3; --muted:#7d8590; --accent:#58a6ff;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  background:var(--bg); color:var(--text);
  font-family:'Noto Sans KR',sans-serif;
  min-height:100vh; padding:2rem;
}
.header {
  text-align:center; margin-bottom:2.5rem;
  padding-bottom:1.5rem; border-bottom:1px solid var(--border);
}
.header h1 {
  font-family:'Space Mono',monospace; font-size:1.6rem;
  color:var(--accent); letter-spacing:2px; margin-bottom:0.5rem;
}
.updated { font-size:0.8rem; color:var(--muted); font-family:'Space Mono',monospace; }
.nav {
  display:flex; justify-content:center;
  gap:1rem; margin-bottom:2rem;
}
.nav a {
  color:var(--muted); text-decoration:none; font-size:0.9rem;
  padding:0.4rem 1rem; border:1px solid var(--border);
  border-radius:20px; transition:all 0.2s;
}
.nav a:hover, .nav a.active { color:var(--accent); border-color:var(--accent); }
.footer {
  text-align:center; margin-top:3rem;
  color:var(--muted); font-size:0.75rem; line-height:1.8;
}
</style>
"""

COMMON_HEAD = (
    '<meta charset="UTF-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
    '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700'
    '&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">'
)


# ===== 경제지표 대시보드 =====
def generate_dashboard(indicators: dict, updated_at: str) -> str:
    cards = build_cards(indicators)

    return (
        '<!DOCTYPE html><html lang="ko"><head>' + COMMON_HEAD +
        '<title>📊 경제지표 대시보드</title>' +
        COMMON_CSS +
        """
        <style>
        .grid {
          display:grid;
          grid-template-columns:repeat(auto-fill,minmax(280px,1fr));
          gap:1rem; max-width:1200px; margin:0 auto;
        }
        .card {
          background:var(--surface); border-radius:8px;
          padding:1.2rem 1.4rem; border:1px solid var(--border);
          transition:transform 0.2s;
        }
        .card:hover { transform:translateY(-2px); }
        .card-label {
          font-size:0.8rem; color:var(--muted);
          margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:1px;
        }
        .card-value {
          font-family:'Space Mono',monospace;
          font-size:1.4rem; font-weight:700; margin-bottom:0.4rem;
        }
        .card-guide { font-size:0.75rem; color:var(--muted); line-height:1.5; }
        </style>
        """ +
        '</head><body>' +
        '<div class="header"><h1>📊 ECONOMIC DASHBOARD</h1>'
        '<div class="updated">Last updated: ' + updated_at + ' KST</div></div>' +
        '<div class="nav">'
        '<a href="index.html" class="active">📊 경제지표</a>'
        '<a href="news.html">📰 뉴스</a>'
        '</div>' +
        '<div class="grid">' + cards + '</div>' +
        '<div class="footer">'
        '<p>⚠️ 본 정보는 투자 참고용이며 투자 결정의 책임은 본인에게 있습니다.</p>'
        '<p>데이터 출처: FRED, 한국은행 ECOS, yfinance</p>'
        '</div>'
        '</body></html>'
    )


# ===== 뉴스 페이지 =====
def generate_news(news_list: list, updated_at: str) -> str:
    items = build_news(news_list)

    return (
        '<!DOCTYPE html><html lang="ko"><head>' + COMMON_HEAD +
        '<title>📰 주식 뉴스</title>' +
        COMMON_CSS +
        """
        <style>
        .filter-bar {
          display:flex; justify-content:center;
          gap:0.5rem; margin-bottom:1.5rem;
        }
        .filter-btn {
          background:var(--surface); border:1px solid var(--border);
          color:var(--muted); padding:0.3rem 0.8rem;
          border-radius:20px; cursor:pointer; font-size:0.85rem;
          font-family:'Noto Sans KR',sans-serif; transition:all 0.2s;
        }
        .filter-btn:hover, .filter-btn.active { color:var(--accent); border-color:var(--accent); }
        .news-list {
          max-width:800px; margin:0 auto;
          display:flex; flex-direction:column; gap:1rem;
        }
        .news-card {
          background:var(--surface); border:1px solid var(--border);
          border-radius:8px; padding:1.2rem 1.4rem; transition:transform 0.2s;
        }
        .news-card:hover { transform:translateX(4px); border-color:var(--accent); }
        .news-meta {
          display:flex; align-items:center;
          gap:0.6rem; margin-bottom:0.6rem;
        }
        .tag {
          font-size:0.7rem; border:1px solid;
          padding:0.1rem 0.5rem; border-radius:10px;
        }
        .source { font-size:0.75rem; color:var(--muted); }
        .date {
          font-size:0.7rem; color:var(--muted);
          margin-left:auto; font-family:'Space Mono',monospace;
        }
        .news-title {
          display:block; font-size:1rem; font-weight:500;
          color:var(--text); text-decoration:none;
          margin-bottom:0.3rem; line-height:1.5;
        }
        .news-title:hover { color:var(--accent); }
        .news-orig {
          font-size:0.78rem; color:var(--muted);
          margin-bottom:0.5rem; font-style:italic;
        }
        .news-summary {
          font-size:0.85rem; color:#adbac7; line-height:1.6;
          border-top:1px solid var(--border);
          padding-top:0.5rem; margin-top:0.5rem;
        }
        </style>
        """ +
        '</head><body>' +
        '<div class="header"><h1>📰 MARKET NEWS</h1>'
        '<div class="updated">Last updated: ' + updated_at + ' KST</div></div>' +
        '<div class="nav">'
        '<a href="index.html">📊 경제지표</a>'
        '<a href="news.html" class="active">📰 뉴스</a>'
        '</div>' +
        '<div class="filter-bar">'
        '<button class="filter-btn active" onclick="filterNews(\'all\')">전체</button>'
        '<button class="filter-btn" onclick="filterNews(\'kr\')">🇰🇷 한국</button>'
        '<button class="filter-btn" onclick="filterNews(\'us\')">🇺🇸 미국</button>'
        '</div>' +
        '<div class="news-list" id="newsList">' + items + '</div>' +
        '<div class="footer">'
        '<p>⚠️ 본 정보는 투자 참고용이며 투자 결정의 책임은 본인에게 있습니다.</p>'
        '</div>' +
        '<script>'
        'function filterNews(type) {'
        '  document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));'
        '  event.target.classList.add("active");'
        '  document.querySelectorAll(".news-card").forEach(card => {'
        '    const tag = card.querySelector(".tag").textContent;'
        '    if (type === "all") card.style.display = "";'
        '    else if (type === "kr") card.style.display = tag.includes("한국") ? "" : "none";'
        '    else if (type === "us") card.style.display = tag.includes("미국") ? "" : "none";'
        '  });'
        '}'
        '</script>'
        '</body></html>'
    )


# ===== 메인 생성 함수 (main.py에서 호출) =====
def generate_all(indicators, news_list: list):
    os.makedirs(DOCS_DIR, exist_ok=True)
    updated_at = datetime.now(KST).strftime("%Y-%m-%d %H:%M")

    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(generate_dashboard(indicators, updated_at))
    print("  💾 index.html 생성 완료")

    with open(os.path.join(DOCS_DIR, "news.html"), "w", encoding="utf-8") as f:
        f.write(generate_news(news_list, updated_at))
    print("  💾 news.html 생성 완료")

    print("  🌐 https://jeon1298.github.io/stock-assistant/")
    print("  🌐 https://jeon1298.github.io/stock-assistant/news.html")


# ===== 테스트 실행 (캐시 우선 사용) =====
if __name__ == "__main__":
    import json
    import economic_collector as ec
    import news_collector as nc

    ECONOMIC_FILE = os.path.join(BASE_DIR, "data", "economic_result.json")
    NEWS_FILE = os.path.join(BASE_DIR, "data", "news_result.json")

    print("=" * 50)
    print("🌐 대시보드 생성 테스트")
    print("=" * 50)

    # 경제지표 캐시 우선
    print("\n📊 경제지표 로드 중...")
    if os.path.exists(ECONOMIC_FILE):
        print("  ✅ 캐시에서 로드")
        indicators = ec.fetch_all_indicators()  # 구조 파악용
    else:
        print("  🔄 새로 수집 중...")
        indicators = ec.fetch_all_indicators()

    # 뉴스 캐시 우선
    print("📰 뉴스 로드 중...")
    if os.path.exists(NEWS_FILE):
        print("  ✅ 캐시에서 로드")
        news_list = nc.fetch_news(max_per_feed=3)
    else:
        print("  🔄 새로 수집 중...")
        news_list = nc.fetch_news(max_per_feed=3)

    print("🔨 HTML 생성 중...")
    generate_all(indicators, news_list)
    print("\n✅ 완료!")