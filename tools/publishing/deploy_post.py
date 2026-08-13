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
CATEGORY_URLS = {
    "ai-news": f"{BASE_URL}/blog/ai-news",
    "business-automation": f"{BASE_URL}/blog/business-automation",
    "role-guides": f"{BASE_URL}/blog/role-guides",
    "case-studies": f"{BASE_URL}/blog/case-studies",
    "industry-guides": f"{BASE_URL}/blog/industry-guides",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed:\n{proc.stderr or proc.stdout}")
    return proc


def project_root(root: Path) -> Path:
    return root.parent


def load_env(project: Path) -> dict[str, str]:
    env_path = project / ".env"
    if not env_path.exists():
        return {}
    values: dict[str, str] = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def env_value(project: Path, *names: str) -> str:
    file_env = load_env(project)
    for name in names:
        value = os.environ.get(name) or file_env.get(name)
        if value:
            return value
    return ""


def notify(message: str, project: Path) -> None:
    webhook = env_value(project, "BLOG_NOTIFY_WEBHOOK_URL", "DISCORD_WEBHOOK_URL")
    if not webhook:
        return
    data = json.dumps({"content": message}).encode("utf-8")
    req = urllib.request.Request(webhook, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as exc:  # best-effort notification must not hide original failure
        print(f"WARNING: notification failed: {exc}", file=sys.stderr)


def fail(message: str, project: Path) -> None:
    notify(f"ERROR: Apollo blog deploy failed: {message}", project)
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def warn_if_dirty(root: Path) -> None:
    status = run(["git", "status", "--porcelain"], cwd=root).stdout.strip()
    if status:
        print("WARNING: working tree has uncommitted local changes; deploying committed HEAD only.")
        for line in status.splitlines():
            print(f"  {line}")


def current_branch(root: Path, project: Path) -> str:
    branch = run(["git", "branch", "--show-current"], cwd=root).stdout.strip()
    if not branch:
        fail("Could not determine current git branch.", project)
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


def canonical_ok(url: str) -> bool:
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "ApolloDeploy/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            if not (200 <= resp.status < 300):
                return False
            body = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return False
    canonical = f'<link rel="canonical" href="{url.rstrip("/")}"'
    return canonical in body


def wait_for_live(url: str, timeout_seconds: int, project: Path) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if canonical_ok(url):
            return
        time.sleep(10)
    fail(f"Timed out waiting for live canonical URL: {url}", project)


def run_qa(root: Path, project: Path, url: str, base_url: str) -> None:
    script = root / "tools/publishing/post_publish_qa.py"
    cmd = ["python3", str(script), url]
    if base_url.rstrip("/") != BASE_URL:
        cmd.extend(["--fetch-base-url", base_url.rstrip("/"), "--canonical-base-url", BASE_URL])
    proc = run(cmd, cwd=root, check=False)
    print(proc.stdout)
    if proc.returncode != 0:
        fail(f"Post-publish QA failed for {url}.\n{proc.stderr}", project)


def post_categories(root: Path, slug: str) -> list[str]:
    queue_path = root / "blog/PUBLISH_QUEUE.json"
    if not queue_path.exists():
        return []
    queue = json.loads(queue_path.read_text())
    for entry in queue.get("queue", []):
        if entry.get("slug") != slug:
            continue
        categories = entry.get("categories") or []
        category = entry.get("category")
        if category and category not in categories:
            categories.insert(0, category)
        return [item for item in categories if item in CATEGORY_URLS]
    return []


def updated_urls(root: Path, slug: str) -> list[str]:
    urls = [
        f"{BASE_URL}/blog/{slug}",
        f"{BASE_URL}/images/blog/{slug}-hero.webp",
        f"{BASE_URL}/",
        f"{BASE_URL}/blog/",
    ]
    urls.extend(CATEGORY_URLS[category] for category in post_categories(root, slug))
    return list(dict.fromkeys(urls))


def purge_cloudflare_cache(project: Path, urls: list[str]) -> bool:
    zone_id = env_value(project, "CF_ZONE_ID")
    api_token = env_value(project, "CF_API_TOKEN")
    if not zone_id or not api_token:
        print("Cloudflare cache purge skipped: CF_ZONE_ID and CF_API_TOKEN are not set.")
        return False
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache",
        data=json.dumps({"files": urls}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read())
    if not body.get("success"):
        raise RuntimeError(f"Cloudflare cache purge failed: {body.get('errors', body)}")
    print(f"Cloudflare cache purged for {len(urls)} URL(s).")
    return True


def submit_to_gsc(project: Path, urls: list[str]) -> bool:
    script = project / "scripts/gsc_index.py"
    if not script.exists():
        print("GSC submission skipped: scripts/gsc_index.py not found.")
        return False
    proc = subprocess.run([sys.executable, str(script), *urls], cwd=project, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout)
    if proc.returncode != 0:
        raise RuntimeError(f"GSC submission failed:\n{proc.stderr or proc.stdout}")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Push and verify a prepared Apollo blog post deployment.")
    parser.add_argument("slug", help="Post slug to verify after push.")
    parser.add_argument("--base-url", default=BASE_URL, help="Base URL to verify. Defaults to production.")
    parser.add_argument("--remote", default="origin", help="Git remote to push to.")
    parser.add_argument("--branch", help="Branch to push. Defaults to current branch.")
    parser.add_argument("--skip-push", action="store_true", help="Do not push; only wait/verify the live URL.")
    parser.add_argument("--skip-cache-purge", action="store_true", help="Do not purge Cloudflare cache after QA.")
    parser.add_argument("--skip-gsc", action="store_true", help="Do not submit updated URLs to Google Search Console.")
    parser.add_argument("--timeout", type=int, default=240, help="Seconds to wait for Cloudflare Pages deployment.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    project = project_root(root)
    branch = args.branch or current_branch(root, project)
    base_url = args.base_url.rstrip("/")
    url = f"{base_url}/blog/{args.slug}"
    try:
        warn_if_dirty(root)
        if not args.skip_push:
            print(f"Pushing {branch} to {args.remote}...")
            run(["git", "push", args.remote, branch], cwd=root)
        print(f"Waiting for live URL: {url}")
        wait_for_live(url, args.timeout, project)
        run_qa(root, project, url, base_url)
        urls = updated_urls(root, args.slug)
        if args.skip_cache_purge:
            print("Cloudflare cache purge skipped by --skip-cache-purge.")
            cache_purged = False
        else:
            cache_purged = purge_cloudflare_cache(project, urls)
        if args.skip_gsc:
            print("GSC submission skipped by --skip-gsc.")
            gsc_submitted = False
        else:
            gsc_submitted = submit_to_gsc(project, [item for item in urls if not item.endswith("-hero.webp")])
        completed = ["deployed", "verified"]
        if cache_purged:
            completed.append("cache purged")
        if gsc_submitted:
            completed.append("indexed")
        message = f"Apollo blog {', '.join(completed)}: {url}"
        print(message)
        notify(message, project)
        return 0
    except SystemExit:
        raise
    except Exception as exc:
        fail(str(exc), project)


if __name__ == "__main__":
    raise SystemExit(main())
