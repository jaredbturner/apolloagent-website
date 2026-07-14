#!/usr/bin/env python3
"""
Create a local publish commit for an Apollo Intelligence blog draft.

This script prepares the repository for deployment but does not push. Use
deploy_post.py for the production push/verification step.
"""

from __future__ import annotations

import argparse
import email.utils
import html
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


BASE_URL = "https://apolloagent.ai"
VALID_CATEGORIES = {
    "ai-news": {
        "label": "AI News & Analysis",
        "gradient": "from-violet-900 to-indigo-700",
        "span_class": "text-brand-light bg-brand/20",
        "page": "blog/ai-news.html",
    },
    "business-automation": {
        "label": "Business Automation",
        "gradient": "from-brand-dark to-indigo-500",
        "span_class": "text-white bg-white/20",
        "page": "blog/business-automation.html",
    },
    "role-guides": {
        "label": "Role Guide",
        "gradient": "from-emerald-900 to-green-700",
        "span_class": "text-white bg-white/20",
        "page": "blog/role-guides.html",
    },
    "case-studies": {
        "label": "Case Study",
        "gradient": "from-slate-900 via-blue-900 to-slate-800",
        "span_class": "text-white bg-white/20",
        "page": "blog/case-studies.html",
    },
    "industry-guides": {
        "label": "Industry Guide",
        "gradient": "from-slate-800 to-blue-900",
        "span_class": "text-white bg-white/20",
        "page": "blog/industry-guides.html",
    },
}


@dataclass
class Post:
    slug: str
    title: str
    description: str
    publish_date: date
    draft_rel: Path
    live_rel: Path
    url: str
    categories: list[str]
    read_minutes: int


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=check)


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def load_queue(root: Path) -> dict:
    return json.loads(read_text(root / "blog/PUBLISH_QUEUE.json"))


def save_queue(root: Path, queue: dict) -> None:
    write_text(root / "blog/PUBLISH_QUEUE.json", json.dumps(queue, indent=2) + "\n")


def normalize_slug(value: str) -> str:
    name = Path(value).name
    if name.endswith(".html"):
        name = name[:-5]
    return name.strip()


def find_queue_entry(queue: dict, slug: str) -> dict:
    matches = [entry for entry in queue.get("queue", []) if entry.get("slug") == slug]
    if not matches:
        fail(f"No PUBLISH_QUEUE.json entry found for slug '{slug}'.")
    if len(matches) > 1:
        fail(f"Multiple PUBLISH_QUEUE.json entries found for slug '{slug}'.")
    return matches[0]


def meta_content(source: str, name: str) -> str:
    patterns = [
        rf'<meta\s+name="{re.escape(name)}"\s+content="([^"]*)"',
        rf'<meta\s+property="{re.escape(name)}"\s+content="([^"]*)"',
    ]
    for pattern in patterns:
        match = re.search(pattern, source, flags=re.I)
        if match:
            return html.unescape(match.group(1)).strip()
    return ""


def title_from_html(source: str) -> str:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", source, flags=re.I | re.S)
    if match:
        return html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()
    match = re.search(r"<title[^>]*>(.*?)</title>", source, flags=re.I | re.S)
    if match:
        title = html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()
        return re.sub(r"\s+—\s+Apollo Intelligence$", "", title).strip()
    return ""


def word_count_minutes(source: str) -> int:
    article_match = re.search(r'<article[^>]*class="[^"]*article-body[^"]*"[^>]*>(.*?)</article>', source, flags=re.I | re.S)
    body = article_match.group(1) if article_match else source
    text = re.sub(r"<script.*?</script>", " ", body, flags=re.I | re.S)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    words = re.findall(r"[A-Za-z0-9']+", html.unescape(text))
    return max(4, round(len(words) / 225))


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        fail(f"Invalid publishDate '{value}'. Expected YYYY-MM-DD.")


def display_date(value: date, short: bool = True) -> str:
    fmt = "%b %-d, %Y" if short else "%B %-d, %Y"
    return value.strftime(fmt)


def rss_date(value: date) -> str:
    dt = datetime.combine(value, time(hour=12), tzinfo=timezone.utc)
    return email.utils.format_datetime(dt, usegmt=True)


def infer_categories(slug: str, title: str, explicit: str | None) -> list[str]:
    if explicit:
        categories = [item.strip() for item in explicit.split(",") if item.strip()]
    else:
        haystack = f"{slug} {title}".lower()
        if "case-study" in haystack or "case study" in haystack:
            categories = ["case-studies"]
        elif any(term in haystack for term in ["legal", "law-firm", "law firm"]):
            categories = ["role-guides", "industry-guides"]
        elif any(term in haystack for term in ["hr", "finance", "sales", "operations", "project-management", "project management"]):
            categories = ["role-guides"]
        elif any(term in haystack for term in ["claude", "gpt", "gemini", "model", "context", "token", "ai-news", "landscape"]):
            categories = ["ai-news"]
        elif any(term in haystack for term in ["automation", "workflow", "support", "meeting", "lead", "workspace", "productivity", "vibe-coding"]):
            categories = ["business-automation"]
        else:
            categories = ["business-automation"]
    invalid = [item for item in categories if item not in VALID_CATEGORIES]
    if invalid:
        fail(f"Invalid category/categories: {', '.join(invalid)}. Valid: {', '.join(VALID_CATEGORIES)}")
    return list(dict.fromkeys(categories))


def build_post(root: Path, slug: str, category_arg: str | None) -> Post:
    queue = load_queue(root)
    entry = find_queue_entry(queue, slug)
    status = entry.get("status")
    if status not in {"pending_review", "approved"}:
        fail(f"Queue entry status is '{status}', expected pending_review or approved.")
    draft_rel = Path("blog") / entry.get("draftPath", f"drafts/{slug}.html")
    draft_path = root / draft_rel
    if not draft_path.exists():
        fail(f"Draft not found: {draft_rel}")
    source = read_text(draft_path)
    title = entry.get("title") or title_from_html(source)
    if not title:
        fail("Could not determine post title from queue or HTML.")
    description = meta_content(source, "description") or meta_content(source, "og:description")
    if not description:
        fail("Draft is missing a meta description.")
    publish_date = parse_date(entry.get("publishDate", ""))
    live_rel = Path("blog") / f"{slug}.html"
    categories = infer_categories(slug, title, category_arg or entry.get("category") or ",".join(entry.get("categories", []) or []))
    return Post(
        slug=slug,
        title=title,
        description=description,
        publish_date=publish_date,
        draft_rel=draft_rel,
        live_rel=live_rel,
        url=f"{BASE_URL}/blog/{slug}",
        categories=categories,
        read_minutes=word_count_minutes(source),
    )


def remove_existing_card(content: str, slug: str) -> str:
    pattern = re.compile(
        rf"\n?        <article class=\"group\"[^>]*>\s*<a href=\"/blog/{re.escape(slug)}(?:\.html)?\".*?</article>",
        flags=re.S,
    )
    return pattern.sub("", content)


def grid_insert(content: str, card: str) -> str:
    marker = re.search(r'(<div class="grid[^"]*" id="article-grid">\n)', content)
    if not marker:
        fail("Could not find article grid in HTML file.")
    return content[: marker.end()] + card + content[marker.end() :]


def category_info(category: str) -> dict:
    return VALID_CATEGORIES[category]


def build_card(post: Post, category: str, homepage: bool = False) -> str:
    info = category_info(category)
    href = f"/blog/{post.slug}" if homepage else f"/blog/{post.slug}.html"
    article_attr = 'class="group"' if homepage else f'class="group" data-category="{category}"'
    height = "h-44" if homepage else "h-48"
    meta = (
        f'''            <div class="flex items-center gap-2 text-xs text-slate-400">
              <span class="text-slate-500">{display_date(post.publish_date)}</span>
              <span>&middot;</span>
              <span class="text-slate-500">{post.read_minutes} min read</span>
            </div>'''
        if homepage
        else f'''            <div class="flex items-center gap-3 text-xs text-slate-400">
              <div class="w-7 h-7 bg-slate-200 rounded-full flex items-center justify-center text-slate-500 font-bold text-xs">JT</div>
              <span>Jared Turner</span>
              <span>&middot;</span>
              <span>{display_date(post.publish_date)}</span>
              <span>&middot;</span>
              <span>{post.read_minutes} min read</span>
            </div>
            <div class="mt-3 text-brand text-sm font-semibold group-hover:underline">Read Article &rarr;</div>'''
    )
    return f'''        <article {article_attr}>
          <a href="{href}" class="block">
            <div class="bg-gradient-to-br {info["gradient"]} rounded-2xl {height} flex items-end p-6 mb-4">
              <span class="text-xs font-bold uppercase tracking-wider {info["span_class"]} px-3 py-1 rounded-full">{info["label"]}</span>
            </div>
            <h3 class="text-lg font-bold text-slate-900 mb-2 group-hover:text-brand transition">{html.escape(post.title)}</h3>
            <p class="text-slate-500 text-sm leading-relaxed {'mb-3' if homepage else 'line-clamp-2 mb-4'}">{html.escape(post.description)}</p>
{meta}
          </a>
        </article>
'''


def update_grid_file(path: Path, post: Post, category: str) -> None:
    content = read_text(path)
    content = remove_existing_card(content, post.slug)
    content = grid_insert(content, build_card(post, category))
    write_text(path, content)


def published_posts_from_queue(root: Path) -> list[Post]:
    posts: list[Post] = []
    for entry in load_queue(root).get("queue", []):
        if entry.get("status") != "published":
            continue
        slug = entry.get("slug")
        if not slug:
            continue
        live_path = root / "blog" / f"{slug}.html"
        if not live_path.exists():
            continue
        source = read_text(live_path)
        title = entry.get("title") or title_from_html(source)
        description = meta_content(source, "description") or meta_content(source, "og:description")
        publish_date = parse_date(entry.get("publishDate", "1970-01-01"))
        category = infer_categories(slug, title, entry.get("category") or ",".join(entry.get("categories", []) or []))[0]
        posts.append(Post(slug, title, description, publish_date, Path(), Path("blog") / f"{slug}.html", f"{BASE_URL}/blog/{slug}", [category], word_count_minutes(source)))
    return sorted(posts, key=lambda item: item.publish_date, reverse=True)


def update_homepage(root: Path) -> None:
    path = root / "index.html"
    content = read_text(path)
    posts = published_posts_from_queue(root)[:3]
    cards = "".join(build_card(post, post.categories[0], homepage=True) for post in posts)
    pattern = re.compile(
        r'(<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">\n)(.*?)(\n      </div>\n      <div class="text-center mt-10">)',
        flags=re.S,
    )
    next_content, count = pattern.subn(rf"\1{cards}      \3", content, count=1)
    if count != 1:
        fail("Could not replace homepage From the Blog grid.")
    write_text(path, next_content)


def update_queue(root: Path, post: Post) -> None:
    queue = load_queue(root)
    entry = find_queue_entry(queue, post.slug)
    entry["status"] = "published"
    entry["publishedUrl"] = post.url
    entry["linkedInPosted"] = bool(entry.get("linkedInPosted", False))
    entry["category"] = post.categories[0]
    if len(post.categories) > 1:
        entry["categories"] = post.categories
    save_queue(root, queue)


def update_sitemap(root: Path, post: Post) -> None:
    path = root / "sitemap.xml"
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    tree = ET.parse(path)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    root_el = tree.getroot()
    loc_to_url = {url.findtext("sm:loc", namespaces=ns): url for url in root_el.findall("sm:url", ns)}
    targets = {
        f"{BASE_URL}/": "0.9",
        f"{BASE_URL}/blog/": "0.8",
        post.url: "0.8",
    }
    for category in post.categories:
        page = category_info(category)["page"]
        category_url = f"{BASE_URL}/{page[:-5]}"
        targets[category_url] = "0.8"
    for loc, priority in targets.items():
        url = loc_to_url.get(loc)
        if url is None:
            url = ET.SubElement(root_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}url")
            ET.SubElement(url, "{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text = loc
            ET.SubElement(url, "{http://www.sitemaps.org/schemas/sitemap/0.9}changefreq").text = "monthly"
            ET.SubElement(url, "{http://www.sitemaps.org/schemas/sitemap/0.9}priority").text = priority
        lastmod = url.find("sm:lastmod", ns)
        if lastmod is None:
            lastmod = ET.SubElement(url, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
        lastmod.text = post.publish_date.isoformat()
    tree.write(path, encoding="unicode", xml_declaration=True)
    content = read_text(path).replace(" />", "/>")
    write_text(path, content)


def update_feed(root: Path, post: Post) -> None:
    path = root / "blog/feed.xml"
    content = read_text(path)
    content = re.sub(r"<lastBuildDate>.*?</lastBuildDate>", f"<lastBuildDate>{rss_date(post.publish_date)}</lastBuildDate>", content, count=1)
    content = re.sub(
        rf"\n    <item>\s*<title>{re.escape(html.escape(post.title))}</title>.*?</item>\n",
        "\n",
        content,
        flags=re.S,
    )
    item = f'''
    <item>
      <title>{html.escape(post.title)}</title>
      <link>{post.url}</link>
      <description>{html.escape(post.description)}</description>
      <pubDate>{rss_date(post.publish_date)}</pubDate>
      <guid>{post.url}</guid>
    </item>
'''
    marker = "\n    <item>"
    index = content.find(marker)
    if index == -1:
        fail("Could not find first RSS item.")
    content = content[:index] + item + content[index:]
    write_text(path, content)


def move_draft(root: Path, post: Post, overwrite: bool) -> None:
    src = root / post.draft_rel
    dst = root / post.live_rel
    if dst.exists() and not overwrite:
        fail(f"Live post already exists: {post.live_rel}. Use --overwrite to replace it.")
    shutil.move(str(src), str(dst))


def ensure_hero_image(root: Path, post: Post) -> Path:
    image = root / "images/blog" / f"{post.slug}-hero.webp"
    if not image.exists():
        fail(
            "Hero image missing: "
            f"{image.relative_to(root)}. Generate and commit the WebP hero before publishing."
        )
    return image


def git_changed_files(root: Path) -> list[str]:
    result = run(["git", "status", "--porcelain"], cwd=root)
    return [line[3:] for line in result.stdout.splitlines() if line]


def commit_changes(root: Path, post: Post) -> None:
    files = [
        "index.html",
        "blog/index.html",
        "blog/PUBLISH_QUEUE.json",
        "blog/feed.xml",
        "sitemap.xml",
        str(post.live_rel),
        str(post.draft_rel),
    ]
    files.extend(category_info(category)["page"] for category in post.categories)
    image = root / "images/blog" / f"{post.slug}-hero.webp"
    if image.exists():
        files.append(str(image.relative_to(root)))
    run(["git", "add", "--", *sorted(set(files))], cwd=root)
    run(["git", "commit", "-m", f"Publish blog: {post.title}"], cwd=root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a local publish commit for an Apollo blog draft.")
    parser.add_argument("slug", help="Post slug or draft filename.")
    parser.add_argument("--category", help="Category slug, or comma-separated category slugs for multi-category posts.")
    parser.add_argument("--commit", action="store_true", help="Create the local git commit after updating files.")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing live blog HTML file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    slug = normalize_slug(args.slug)
    post = build_post(root, slug, args.category)
    print(f"Publishing draft locally: {post.slug}")
    print(f"Category/categories: {', '.join(post.categories)}")
    hero_image = ensure_hero_image(root, post)
    print(f"Hero image: {hero_image.relative_to(root)}")
    move_draft(root, post, args.overwrite)
    update_queue(root, post)
    update_grid_file(root / "blog/index.html", post, post.categories[0])
    for category in post.categories:
        update_grid_file(root / category_info(category)["page"], post, category)
    update_homepage(root)
    update_sitemap(root, post)
    update_feed(root, post)
    changed = git_changed_files(root)
    print("Updated files:")
    for item in changed:
        print(f"  - {item}")
    if args.commit:
        commit_changes(root, post)
        print("Local publish commit created.")
    else:
        print("No commit created. Re-run with --commit after reviewing changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
