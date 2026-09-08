"""Rewrites the Recent Activity section in README.md from GitHub's public events API."""
import json
import os
import re
import urllib.request
from datetime import datetime, timezone

USER = os.environ["GH_USER"]
TOKEN = os.environ.get("GH_TOKEN")
README_PATH = "README.md"

EVENT_LABELS = {
    "PushEvent": lambda p, repo: f"Pushed to `{repo}`",
    "PullRequestEvent": lambda p, repo: f"{p['action'].capitalize()} a pull request in `{repo}`",
    "IssuesEvent": lambda p, repo: f"{p['action'].capitalize()} an issue in `{repo}`",
    "CreateEvent": lambda p, repo: f"Created {p.get('ref_type', 'a ref')} in `{repo}`",
    "WatchEvent": lambda p, repo: f"Starred `{repo}`",
    "ForkEvent": lambda p, repo: f"Forked `{repo}`",
}


def fetch_events():
    req = urllib.request.Request(f"https://api.github.com/users/{USER}/events/public?per_page=30")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", USER)
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def build_lines(events):
    lines = []
    for e in events:
        fmt = EVENT_LABELS.get(e.get("type"))
        if not fmt:
            continue
        try:
            lines.append(f"- {fmt(e['payload'], e['repo']['name'])}")
        except (KeyError, TypeError):
            continue
        if len(lines) == 5:
            break
    if not lines:
        lines = ["- No recent public activity"]
    return lines


def main():
    events = fetch_events()
    lines = build_lines(events)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    block = "\n".join(lines) + f"\n\n_Last synced: {timestamp}_"

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        r"(<!--START_SECTION:activity-->)(.*?)(<!--END_SECTION:activity-->)",
        re.DOTALL,
    )
    if not pattern.search(content):
        raise SystemExit("Activity markers not found in README.md")

    new_content = pattern.sub(lambda m: f"{m.group(1)}\n{block}\n{m.group(3)}", content)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


if __name__ == "__main__":
    main()
