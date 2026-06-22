#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import urllib.request


CRON_API = "https://api.cron-job.org/jobs"
WORKFLOW_URL = (
    "https://api.github.com/repos/jeonjin2/daily-briefing/"
    "actions/workflows/daily-briefing.yml/dispatches"
)


def github_token() -> str:
    token = os.environ.get("GITHUB_DISPATCH_TOKEN")
    if token:
        return token
    return subprocess.check_output(["gh", "auth", "token"], text=True).strip()


def main() -> int:
    cron_token = os.environ.get("CRON_JOB_ORG_API_KEY")
    if not cron_token:
        raise SystemExit("Set CRON_JOB_ORG_API_KEY")

    payload = {
        "job": {
            "enabled": True,
            "title": "Daily AI Briefing",
            "url": WORKFLOW_URL,
            "saveResponses": True,
            "requestMethod": 1,
            "requestTimeout": 60,
            "redirectSuccess": False,
            "schedule": {
                "timezone": "Asia/Seoul",
                "expiresAt": 0,
                "hours": [5],
                "minutes": [59],
                "mdays": [-1],
                "months": [-1],
                "wdays": [-1],
            },
            "extendedData": {
                "headers": {
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {github_token()}",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "Content-Type": "application/json",
                },
                "body": json.dumps(
                    {
                        "ref": "main",
                        "inputs": {
                            "dry_run": "false",
                        },
                    },
                    separators=(",", ":"),
                ),
            },
        }
    }

    request = urllib.request.Request(
        CRON_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {cron_token}",
            "Content-Type": "application/json",
        },
        method="PUT",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            print(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(exc.read().decode("utf-8", errors="replace"), file=sys.stderr)
        raise

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
