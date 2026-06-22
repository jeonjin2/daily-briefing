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

자동 등록:

```bash
CRON_JOB_ORG_API_KEY=... python scripts/create_cron_job.py
```

`GITHUB_DISPATCH_TOKEN`을 따로 지정하지 않으면 현재 `gh auth token`을 사용합니다. 더 안전하게 하려면 GitHub에서 이 repo 전용 fine-grained token을 만들고 `GITHUB_DISPATCH_TOKEN`으로 넘깁니다. 필요한 권한은 이 repo의 Actions write 권한입니다.

수동 등록:

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
