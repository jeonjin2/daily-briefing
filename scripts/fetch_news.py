#!/usr/bin/env python3
import argparse
import email.utils
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone


QUERIES = [
    {
        "topic": "Grok/xAI",
        "query": '("Grok" OR "xAI") AI when:{days}d',
    },
    {
        "topic": "Manus AI",
        "query": '("Manus AI" OR "Manus agent") when:{days}d',
    },
]


def fetch_url(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "daily-ai-news-digest/1.0",
            "Accept": "application/rss+xml, application/xml, text/xml",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def text_of(parent: ET.Element, name: str) -> str:
    child = parent.find(name)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def parse_pub_date(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        return value


def fetch_topic(topic: str, query: str, days: int, limit: int) -> dict:
    expanded_query = query.format(days=days)
    params = urllib.parse.urlencode(
        {
            "q": expanded_query,
            "hl": "ko",
            "gl": "KR",
            "ceid": "KR:ko",
        }
    )
    url = f"https://news.google.com/rss/search?{params}"
    payload = fetch_url(url)
    root = ET.fromstring(payload)
    channel = root.find("channel")
    items = []
    if channel is not None:
        for item in channel.findall("item")[:limit]:
            source = item.find("source")
            items.append(
                {
                    "topic": topic,
                    "title": text_of(item, "title"),
                    "link": text_of(item, "link"),
                    "published_at": parse_pub_date(text_of(item, "pubDate")),
                    "source": source.text.strip() if source is not None and source.text else "",
                }
            )
    return {
        "topic": topic,
        "query": expanded_query,
        "url": url,
        "items": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--limit-per-topic", type=int, default=8)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "Google News RSS",
        "topics": [],
    }

    for spec in QUERIES:
        try:
            result["topics"].append(
                fetch_topic(spec["topic"], spec["query"], args.days, args.limit_per_topic)
            )
        except Exception as exc:
            result["topics"].append(
                {
                    "topic": spec["topic"],
                    "query": spec["query"].format(days=args.days),
                    "error": str(exc),
                    "items": [],
                }
            )

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    errors = [topic for topic in result["topics"] if topic.get("error")]
    if errors:
        print(
            "Warning: some news topics failed: "
            + ", ".join(topic["topic"] for topic in errors),
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
