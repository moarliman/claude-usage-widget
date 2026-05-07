#!/usr/bin/env python3
import json
import subprocess
import urllib.request


class RateLimited(Exception):
    def __init__(self, retry_after):
        super().__init__(f"rate limited (retry after {retry_after}s)")
        self.retry_after = retry_after


def get_token():
    result = subprocess.run(
        ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
        capture_output=True, text=True, check=True
    )
    creds = json.loads(result.stdout.strip())
    return creds["claudeAiOauth"]["accessToken"]

def fetch_usage(token):
    req = urllib.request.Request(
        "https://api.anthropic.com/api/oauth/usage",
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 429:
            try:
                retry_after = int(e.headers.get("Retry-After", "60"))
            except (TypeError, ValueError):
                retry_after = 60
            raise RateLimited(retry_after) from None
        raise

if __name__ == "__main__":
    token = get_token()
    usage = fetch_usage(token)
    print(json.dumps(usage, indent=2))
