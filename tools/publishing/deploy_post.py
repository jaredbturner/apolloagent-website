#!/usr/bin/env python3
"""
Push a prepared Apollo blog publish commit and verify the live deployment.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE_URL = "https://apolloagent.ai"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed:\n{proc.stderr or proc.stdout}")
    return proc


def notify(message: str) -> None:
    webhook = os.environ.get("BLOG_NOTIFY_WEBHOOK_URL")
    if not webhook:
        return
    data = json.dumps({"content": message}).encode("utf-8")
    req = urllib.request.Request(webhook, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as exc:  # best-effort notification must not hide original failure
        print(f"WARNING: notification failed: {exc}", file=sys.stderr)


def fail(message: str) -> None:
    notify(f"❌ Apollo blog deploy failed: {message}")
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def ensure_clean(root: Path) -> None:
    status = run(["git", "status", "--porcelain"], cwd=root).stdout.strip()
    if status:
        fail("Working tree is dirty. Commit or stash changes before deploy.")


def current_branch(root: Path) -> str:
    branch = run(["git", "branch", "--show-current"], cwd=root).stdout.strip()
    if not branch:
        fail("Could not determine current git branch.")
    return branch


def url_ok(url: str) -> bool:
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "ApolloDeploy/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 300
    except urllib.error.HTTPError as exc:
        return 200 <= exc.code < 300
    except Exception:
        return False


def wait_for_live(url: str, timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if url_ok(url):
            return
        time.sleep(10)
    fail(f"Timed out waiting for live URL: {url}")


def run_qa(root: Path, url: str) -> None:
    script = root / "tools/publishing/post_publish_qa.py"
    proc = run(["python3", str(script), url], cwd=root, check=False)
    print(proc.stdout)
    if proc.returncode != 0:
        fail(f"Post-publish QA failed for {url}.\n{proc.stderr}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Push and verify a prepared Apollo blog post deployment.")
    parser.add_argument("slug", help="Post slug to verify after push.")
    parser.add_argument("--remote", default="origin", help="Git remote to push to.")
    parser.add_argument("--branch", help="Branch to push. Defaults to current branch.")
    parser.add_argument("--skip-push", action="store_true", help="Do not push; only wait/verify the live URL.")
    parser.add_argument("--timeout", type=int, default=240, help="Seconds to wait for Cloudflare Pages deployment.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    branch = args.branch or current_branch(root)
    url = f"{BASE_URL}/blog/{args.slug}"
    try:
        ensure_clean(root)
        if not args.skip_push:
            print(f"Pushing {branch} to {args.remote}...")
            run(["git", "push", args.remote, branch], cwd=root)
        print(f"Waiting for live URL: {url}")
        wait_for_live(url, args.timeout)
        run_qa(root, url)
        message = f"✅ Apollo blog deployed and verified: {url}"
        print(message)
        notify(message)
        return 0
    except SystemExit:
        raise
    except Exception as exc:
        fail(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
