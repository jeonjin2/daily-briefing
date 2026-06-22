# Daily Briefing

cron-job.org가 매일 05:59 KST에 GitHub Actions `workflow_dispatch`를 호출하고, Actions가 Codex로 AI 뉴스 브리핑을 만들어 Telegram으로 보냅니다.

## 브리핑 내용

- Grok/xAI와 Manus AI 관련 최신 이슈 2개 정도
- LLM이나 코딩 모델 사용 시 실전 꿀팁 5개
- 한국어 Telegram 메시지

## GitHub Secrets

이 repo의 Actions secrets:

- `CODEX_AUTH_JSON`: 로컬 `/Users/james/.codex/auth.json` 내용
- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `TELEGRAM_CHAT_ID`: 받을 채팅 ID

## cron-job.org

Method:

```text
POST
```

URL:

```text
https://api.github.com/repos/jeonjin2/daily-briefing/actions/workflows/daily-briefing.yml/dispatches
```

Headers:

```text
Accept: application/vnd.github+json
Authorization: Bearer GITHUB_PAT
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json
```

Body:

```json
{
  "ref": "main",
  "inputs": {
    "dry_run": "false"
  }
}
```

`GITHUB_PAT`는 fine-grained token으로 만들고, 이 repo에 Actions write 권한을 줍니다.
