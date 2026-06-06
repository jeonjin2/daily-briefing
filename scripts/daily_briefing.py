import os
import requests
import feedparser
import google.generativeai as genai

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = "7824088625"
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]


def get_bitcoin_data():
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin&vs_currencies=usd,krw"
        "&include_24hr_change=true&include_market_cap=true"
    )
    data = requests.get(url, timeout=10).json()["bitcoin"]
    return data


def get_mideast_news():
    feeds = [
        "http://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
    ]
    headlines = []
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")[:200]
            headlines.append(f"- {title}: {summary}")
        if len(headlines) >= 8:
            break
    return "\n".join(headlines[:8])


def analyze_with_gemini(btc: dict, news: str) -> str:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""다음 정보를 바탕으로 한국어로 간결하게 분석해줘. 총 300자 이내.

[비트코인 시황]
가격: ${btc['usd']:,.0f} (₩{btc['krw']:,.0f})
24h 변동: {btc['usd_24h_change']:+.2f}%
시가총액: ${btc['usd_market_cap'] / 1e9:.0f}B

[중동 뉴스 헤드라인]
{news}

분석 형식:
• 비트코인: 한 줄 요약 + 방향성
• 중동: 핵심 이슈 한 줄
• 종합 코멘트: 한 줄"""

    response = model.generate_content(prompt)
    return response.text.strip()


def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }, timeout=10)


def main():
    btc = get_bitcoin_data()
    news = get_mideast_news()
    analysis = analyze_with_gemini(btc, news)

    change_emoji = "📈" if btc["usd_24h_change"] > 0 else "📉"
    message = (
        f"🌅 <b>모닝 브리핑</b>\n\n"
        f"{change_emoji} <b>비트코인</b>\n"
        f"  ${btc['usd']:,.0f}  |  ₩{btc['krw']:,.0f}\n"
        f"  24h: {btc['usd_24h_change']:+.2f}%\n\n"
        f"🌍 <b>중동 주요 뉴스</b>\n"
        f"{news[:400]}\n\n"
        f"🤖 <b>AI 분석</b>\n{analysis}"
    )
    send_telegram(message)


if __name__ == "__main__":
    main()
