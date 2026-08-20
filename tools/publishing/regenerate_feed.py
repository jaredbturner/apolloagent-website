#!/usr/bin/env python3
"""
Regenerate blog/feed.xml from the live article HTML files.

Use this when RSS needs to be reconciled against the actual blog inventory
instead of relying on the incremental publish insertion path.
"""

from __future__ import annotations

import email.utils
import html
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path


BASE_URL = "https://apolloagent.ai"
EXCLUDED_BLOG_FILES = {
    "index.html",
    "ai-news.html",
    "business-automation.html",
    "role-guides.html",
    "case-studies.html",
    "industry-guides.html",
}


@dataclass(frozen=True)
class FeedItem:
    slug: str
    title: str
    description: str
    url: str
    publish_date: date


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return html.unescape(value)


def attr(source: str, tag_pattern: str, attr_name: str) -> str:
    tag = re.search(tag_pattern, source, flags=re.I | re.S)
    if not tag:
        return ""
    match = re.search(rf'{attr_name}\s*=\s*(["\'])(.*?)\1', tag.group(0), flags=re.I | re.S)
    return clean_text(match.group(2)) if match else ""


def meta_content(source: str, name: str) -> str:
    escaped = re.escape(name)
    return attr(source, rf'<meta[^>]+(?:name|property)=["\']{escaped}["\'][^>]*>', "content")


def canonical_url(source: str, slug: str) -> str:
    canonical = attr(source, r'<link[^>]+rel=["\']canonical["\'][^>]*>', "href")
    return canonical or f"{BASE_URL}/blog/{slug}"


def title_from_html(source: str) -> str:
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", source, flags=re.I | re.S)
    if h1:
        return clean_text(h1.group(1))
    title = re.search(r"<title[^>]*>(.*?)</title>", source, flags=re.I | re.S)
    if title:
        return re.sub(r"\s+[—-]\s+Apollo Intelligence$", "", clean_text(title.group(1))).strip()
    return ""


def date_from_html(source: str) -> date | None:
    patterns = [
        r'"datePublished"\s*:\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})"',
        r'"dateModified"\s*:\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})"',
        r'<time[^>]+datetime=["\']([0-9]{4}-[0-9]{2}-[0-9]{2})',
    ]
    for pattern in patterns:
        match = re.search(pattern, source, flags=re.I)
        if match:
            return date.fromisoformat(match.group(1))
    return None


def rss_date(value: date) -> str:
    dt = datetime.combine(value, time(hour=12), tzinfo=timezone.utc)
    return email.utils.format_datetime(dt, usegmt=True)


def load_queue_dates(root: Path) -> dict[str, date]:
    queue_path = root / "blog/PUBLISH_QUEUE.json"
    if not queue_path.exists():
        return {}
    data = json.loads(read_text(queue_path))
    dates = {}
    for item in data.get("queue", []):
        slug = item.get("slug")
        publish_date = item.get("publishDate")
        if slug and publish_date:
            dates[slug] = date.fromisoformat(publish_date)
    return dates


def collect_items(root: Path) -> list[FeedItem]:
    queue_dates = load_queue_dates(root)
    items = []
    for path in sorted((root / "blog").glob("*.html")):
        if path.name in EXCLUDED_BLOG_FILES:
            continue
        slug = path.stem
        source = read_text(path)
        title = title_from_html(source)
        description = meta_content(source, "description") or meta_content(source, "og:description")
        publish_date = queue_dates.get(slug) or date_from_html(source)
        if not title or not description or not publish_date:
            missing = []
            if not title:
                missing.append("title")
            if not description:
                missing.append("description")
            if not publish_date:
                missing.append("publish date")
            raise SystemExit(f"ERROR: {path.relative_to(root)} missing {', '.join(missing)}")
        items.append(
            FeedItem(
                slug=slug,
                title=title,
                description=description,
                url=canonical_url(source, slug),
                publish_date=publish_date,
            )
        )
    return sorted(items, key=lambda item: (item.publish_date, item.slug), reverse=True)


def render_feed(items: list[FeedItem]) -> str:
    if not items:
        raise SystemExit("ERROR: no feed items found")
    last_build = rss_date(items[0].publish_date)
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "  <channel>",
        "    <title>Apollo Intelligence Blog</title>",
        "    <link>https://apolloagent.ai/blog/</link>",
        "    <description>Practical AI insights for business leaders. No hype, just signal.</description>",
        "    <language>en-us</language>",
        "    <managingEditor>hello@apolloagent.ai (Apollo Intelligence)</managingEditor>",
        "    <webMaster>hello@apolloagent.ai (Apollo Intelligence)</webMaster>",
        f"    <lastBuildDate>{last_build}</lastBuildDate>",
        '    <atom:link href="https://apolloagent.ai/blog/feed.xml" rel="self" type="application/rss+xml" />',
        "",
    ]
    for item in items:
        title = html.escape(item.title, quote=False)
        description = html.escape(item.description, quote=False)
        url = html.escape(item.url, quote=True)
        parts.extend(
            [
                "    <item>",
                f"      <title>{title}</title>",
                f"      <link>{url}</link>",
                f"      <description>{description}</description>",
                f"      <pubDate>{rss_date(item.publish_date)}</pubDate>",
                f"      <guid>{url}</guid>",
                "    </item>",
                "",
            ]
        )
    parts.extend(["  </channel>", "</rss>", ""])
    return "\n".join(parts)


def main() -> None:
    root = repo_root()
    items = collect_items(root)
    feed_path = root / "blog/feed.xml"
    feed_path.write_text(render_feed(items), encoding="utf-8")
    print(f"Regenerated {feed_path.relative_to(root)} with {len(items)} items.")


if __name__ == "__main__":
    main()
