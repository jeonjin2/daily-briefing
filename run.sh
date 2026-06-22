#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck source=/dev/null
  source .env
  set +a
fi

: "${TELEGRAM_BOT_TOKEN:?Set TELEGRAM_BOT_TOKEN in .env}"
: "${TELEGRAM_CHAT_ID:?Set TELEGRAM_CHAT_ID in .env}"

TIMEZONE="${TIMEZONE:-Asia/Seoul}"
DIGEST_DAYS="${DIGEST_DAYS:-3}"
CODEX_BIN="${CODEX_BIN:-codex}"
CODEX_MODEL="${CODEX_MODEL:-}"

mkdir -p out logs

STAMP="$(TZ="$TIMEZONE" date '+%Y-%m-%d_%H-%M-%S')"
RAW_NEWS="out/news-$STAMP.json"
SUMMARY="out/summary-$STAMP.md"

python3 scripts/fetch_news.py --days "$DIGEST_DAYS" --output "$RAW_NEWS"

PROMPT="$(cat <<'PROMPT'
너는 매일 아침 보내는 AI 뉴스 브리핑 작성자다.

입력 JSON은 Google News RSS에서 수집한 최근 기사 후보들이다. 기사 후보는 중복되거나 품질이 낮을 수 있으므로, 제목/출처/일시/링크를 근거로 중요도를 판단해라.

출력은 한국어 Telegram 메시지로 바로 보낼 수 있게 작성한다.

요구사항:
- 전체 길이는 되도록 2500자 이내.
- "Grok/xAI"와 "Manus AI" 관련 최신 이슈를 합쳐서 중요한 것 2개 정도만 고른다.
- 각 이슈는 왜 중요한지 한 문장으로 설명한다.
- 링크는 각 이슈마다 1개만 붙인다.
- 이어서 "LLM/코딩 모델 꿀팁 5개"를 작성한다.
- 꿀팁은 남들이 잘 모르는 실전 사용 팁 위주로 작성한다.
- 뻔한 팁(프롬프트를 명확히 써라, 예시를 줘라, 단계별로 생각해라)은 피한다.
- 입력 기사에서 확인되지 않은 최신 사실은 단정하지 않는다.
- 끝에 "오늘의 실행 포인트" 1줄을 붙인다.

형식:
오늘의 AI 브리핑 (YYYY-MM-DD)

1. 최신 이슈
- ...
- ...

2. LLM/코딩 모델 꿀팁 5개
1) ...
2) ...
3) ...
4) ...
5) ...

오늘의 실행 포인트: ...
PROMPT
)"

CODEX_ARGS=(exec --skip-git-repo-check --sandbox read-only --cd "$SCRIPT_DIR")
if [[ -n "$CODEX_MODEL" ]]; then
  CODEX_ARGS+=(--model "$CODEX_MODEL")
fi

"$CODEX_BIN" "${CODEX_ARGS[@]}" "$PROMPT" < "$RAW_NEWS" > "$SUMMARY"

python3 scripts/send_telegram.py "$SUMMARY"

printf 'Wrote %s and %s\n' "$RAW_NEWS" "$SUMMARY"
