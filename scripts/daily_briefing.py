import os
import requests
from google import genai
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
NEWS_API_KEY = os.environ["NEWS_API_KEY"]


def get_iran_war_news() -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    resp = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "q": "(Iran) AND (war OR attack OR missile OR strike OR conflict OR nuclear)",
            "from": since,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 10,
            "apiKey": NEWS_API_KEY,
        },
        timeout=10,
    )
    resp.raise_for_status()
    articles = resp.json().get("articles", [])
    return [
        {"title": a["title"], "source": a["source"]["name"], "desc": (a.get("description") or "")[:150]}
        for a in articles
        if a.get("title") and "[Removed]" not in a["title"]
    ][:8]


def get_bitcoin_data() -> dict:
    # 현재 가격 + 24h 변동
    price_resp = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={
            "ids": "bitcoin",
            "vs_currencies": "usd,krw",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true",
        },
        timeout=10,
    )
    price_resp.raise_for_status()
    btc = price_resp.json()["bitcoin"]

    # 24h OHLC (고가/저가)
    ohlc_resp = requests.get(
        "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc",
        params={"vs_currency": "usd", "days": "1"},
        timeout=10,
    )
    ohlc_resp.raise_for_status()
    ohlc = ohlc_resp.json()
    highs = [row[2] for row in ohlc]
    lows = [row[3] for row in ohlc]

    return {
        "usd": btc["usd"],
        "krw": btc["krw"],
        "change_24h": btc["usd_24h_change"],
        "volume_24h": btc["usd_24h_vol"],
        "market_cap": btc["usd_market_cap"],
        "high_24h": max(highs) if highs else 0,
        "low_24h": min(lows) if lows else 0,
    }


_gemini = genai.Client(api_key=GEMINI_API_KEY)


def analyze_with_gemini(btc: dict, articles: list[dict]) -> str:

    news_text = "\n".join(
        f"[{a['source']}] {a['title']} — {a['desc']}" for a in articles
    )

    prompt = f"""아래 정보를 바탕으로 한국어로 간결하게 분석해줘. 총 400자 이내.

[비트코인 24시간 시황]
현재가: ${btc['usd']:,.0f} (₩{btc['krw']:,.0f})
24h 변동: {btc['change_24h']:+.2f}%
24h 고가: ${btc['high_24h']:,.0f} / 저가: ${btc['low_24h']:,.0f}
24h 거래량: ${btc['volume_24h'] / 1e9:.1f}B
시가총액: ${btc['market_cap'] / 1e9:.0f}B

[이란 전쟁 관련 뉴스 (최근 24시간)]
{news_text}

분석 형식 (각 항목은 한 줄):
• 비트코인: 시황 요약 + 단기 방향성
• 이란 전쟁: 핵심 이슈 요약
• 상관관계: 지정학적 리스크가 비트코인에 미치는 영향"""

    return _gemini.models.generate_content(model="gemini-2.0-flash", contents=prompt).text.strip()


def send_telegram(text: str):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=10,
    )


def main():
    btc = get_bitcoin_data()
    articles = get_iran_war_news()
    analysis = analyze_with_gemini(btc, articles)

    emoji = "📈" if btc["change_24h"] > 0 else "📉"
    news_block = "\n".join(f"• {a['title']}" for a in articles[:5])

    message = (
        f"🌅 <b>모닝 브리핑</b>  {datetime.now(timezone(timedelta(hours=9))).strftime('%m/%d %H:%M')} KST\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"{emoji} <b>비트코인 24h 시황</b>\n"
        f"  현재가  ${btc['usd']:,.0f}  |  ₩{btc['krw']:,.0f}\n"
        f"  변동    {btc['change_24h']:+.2f}%\n"
        f"  고가  ${btc['high_24h']:,.0f}  /  저가  ${btc['low_24h']:,.0f}\n"
        f"  거래량  ${btc['volume_24h'] / 1e9:.1f}B\n\n"
        f"🔫 <b>이란 전쟁 뉴스 (24h)</b>\n"
        f"{news_block}\n\n"
        f"🤖 <b>AI 분석</b>\n"
        f"{analysis}"
    )
    send_telegram(message)
    print("✅ 브리핑 전송 완료")


if __name__ == "__main__":
    main()
