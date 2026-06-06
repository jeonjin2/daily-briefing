import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
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
        {"title": a["title"], "source": a["source"]["name"]}
        for a in articles
        if a.get("title") and "[Removed]" not in a["title"]
    ][:8]


def get_bitcoin_data() -> dict:
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


def send_telegram(text: str):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=10,
    )


def main():
    btc = get_bitcoin_data()
    articles = get_iran_war_news()

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
        f"{news_block}"
    )
    send_telegram(message)
    print("✅ 브리핑 전송 완료")


if __name__ == "__main__":
    main()
