#!/usr/bin/env python3
import argparse
import os
import sys
import time
import urllib.parse
import urllib.request


MAX_TELEGRAM_TEXT = 3900


def chunks(text: str, size: int):
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            newline = text.rfind("\n", start, end)
            if newline > start + 1000:
                end = newline
        yield text[start:end].strip()
        start = end


def send_message(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8", errors="replace")
        if response.status >= 400:
            raise RuntimeError(body)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("summary_file")
    args = parser.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")

    with open(args.summary_file, "r", encoding="utf-8") as handle:
        text = handle.read().strip()

    if not text:
        raise SystemExit("Summary is empty")

    if os.environ.get("TELEGRAM_DRY_RUN") == "1":
        print(text)
        return 0

    parts = list(chunks(text, MAX_TELEGRAM_TEXT))
    for index, part in enumerate(parts):
        prefix = f"({index + 1}/{len(parts)})\n" if len(parts) > 1 else ""
        send_message(token, chat_id, prefix + part)
        time.sleep(0.4)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Telegram send failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
