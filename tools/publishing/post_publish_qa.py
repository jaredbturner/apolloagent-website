#!/usr/bin/env python3
"""
Apollo Intelligence — Post-Publish QA Checker
============================================================
Usage:
  # Check a specific post after publishing:
  python3 tools/publishing/post_publish_qa.py https://apolloagent.ai/blog/ai-meeting-automation-guide

  # Check ALL live blog posts:
  python3 tools/publishing/post_publish_qa.py --all

  # Check from local sitemap:
  python3 tools/publishing/post_publish_qa.py --sitemap sitemap.xml

Checks performed per URL:
  1. HTTP 200 response
  2. Canonical URL matches expected (no redirect chain to wrong slug)
  3. <title> and <h1> present and non-empty
  4. Meta description present and ≤160 chars
  5. Open Graph tags: og:title, og:description, og:image
  6. og:image URL returns a real image (Content-Type: image/*)
  7. All <img> src attributes return real images (not HTML soft-404s)
  8. No <a href> links return 4xx/5xx (internal + external, with caching)
  9. Schema markup (application/ld+json) present
 10. No broken internal links (links to /blog/* or / that 404)
 11. Inline hero <figure><img> present (required by BLOG_PROCESS.md for recent posts)
 12. Page load HTTP status logged
"""

import sys
import re
import time
import json
import argparse
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional

BASE_URL = "https://apolloagent.ai"
FETCH_BASE_URL = BASE_URL
CANONICAL_BASE_URL = ""
TIMEOUT = 15
MAX_LINK_WORKERS = 8

# Category/listing pages — exempt from article-level checks (schema, figure)
CATEGORY_PAGES = {
    "ai-news", "business-automation", "case-studies",
    "role-guides", "industry-guides",
}

# Posts published before hero image requirement — exempt from inline image check
# (image requirement added ~May 14, 2026; earlier posts have no figure block)
EXEMPT_FROM_IMAGE_CHECK = {
    "5-ai-automations-small-business",
    "agency-60-percent-admin-reduction-case-study",
    "ai-agents-guide-2026",
    "ai-for-legal-teams",
    "ai-for-operations-managers",
    "ai-news-march-2026",
    "ai-powered-business-intelligence",
    "ecommerce-scaled-5m-3-person-team-ai",
    "gpt-5-5-multimodal-business",
    "how-to-write-ai-prompts-that-actually-work-for-business-tasks",
    "the-real-cost-of-not-using-ai-2026",
}

# Domains/paths to skip for link checking (known-good CDNs, external auth walls, etc.)
SKIP_LINK_DOMAINS = {
    "twitter.com", "x.com", "linkedin.com", "facebook.com",
    "cdn.tailwindcss.com", "fonts.googleapis.com",
}
# URL path prefixes to skip (Cloudflare internals, etc.)
SKIP_LINK_PATHS = (
    "/cdn-cgi/",  # Cloudflare internals (email-protection, scripts, etc.)
    "/go/",       # Affiliate redirect slugs
)


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class PageResult:
    url: str
    checks: list = field(default_factory=list)

    @property
    def passed(self):
        return all(c.passed for c in self.checks)

    @property
    def failures(self):
        return [c for c in self.checks if not c.passed]

    @property
    def warnings(self):
        return [c for c in self.checks if not c.passed and c.name.startswith("WARN")]


def fetch_url(url: str) -> str:
    if FETCH_BASE_URL != BASE_URL and url.startswith(BASE_URL):
        parsed = urllib.parse.urlparse(url)
        return FETCH_BASE_URL.rstrip("/") + parsed.path + (f"?{parsed.query}" if parsed.query else "")
    return url


def fetch(url: str, method: str = "GET", timeout: int = TIMEOUT):
    """Fetch a URL; returns (status_code, content_type, body_bytes)."""
    req = urllib.request.Request(
        fetch_url(url),
        headers={"User-Agent": "ApolloQA/1.0 (+https://apolloagent.ai)"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ct = resp.headers.get("Content-Type", "")
            body = resp.read() if method == "GET" else b""
            return resp.status, ct, body, resp.url
    except urllib.error.HTTPError as e:
        return e.code, "", b"", url
    except Exception as e:
        return 0, "", b"", url


def is_real_image(url: str) -> tuple[bool, str]:
    """Return (is_image, content_type). Checks HEAD first, falls back to GET."""
    status, ct, _, _ = fetch(url, method="HEAD", timeout=10)
    if status == 405:  # HEAD not allowed
        status, ct, _, _ = fetch(url, method="GET", timeout=10)
    if status == 0:
        return False, f"connection error"
    if status >= 400:
        return False, f"HTTP {status}"
    if "image/" not in ct:
        return False, f"Content-Type: {ct!r} (not an image — likely HTML soft-404)"
    return True, ct


def check_link(href: str, base_url: str) -> tuple[str, int, str]:
    """Return (resolved_url, status_code, note)."""
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return href, 200, "skipped"
    if href.startswith("//"):
        href = "https:" + href
    elif href.startswith("/"):
        parsed = urllib.parse.urlparse(base_url)
        href = f"{parsed.scheme}://{parsed.netloc}{href}"
    elif not href.startswith("http"):
        href = urllib.parse.urljoin(base_url, href)

    parsed_href = urllib.parse.urlparse(href)
    domain = parsed_href.netloc
    if any(skip in domain for skip in SKIP_LINK_DOMAINS):
        return href, 200, "skipped (external)"
    if any(parsed_href.path.startswith(prefix) for prefix in SKIP_LINK_PATHS):
        return href, 200, "skipped (internal cdn/system path)"

    status, _, _, _ = fetch(href, method="HEAD", timeout=10)
    if status == 405:
        status, _, _, _ = fetch(href, method="GET", timeout=10)
    return href, status, ""


def qa_page(url: str) -> PageResult:
    result = PageResult(url=url)
    add = result.checks.append

    # ── 1. HTTP 200 ──────────────────────────────────────────────────────────
    status, ct, body, final_url = fetch(url)
    add(Check("HTTP 200", status == 200, f"got {status}"))
    if status != 200:
        return result  # No point continuing on non-200

    html = body.decode("utf-8", errors="replace")

    # ── 2. Canonical / no redirect to wrong slug ──────────────────────────────
    canon_match = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']', html)
    canon_url = canon_match.group(1) if canon_match else ""
    if CANONICAL_BASE_URL:
        parsed_url = urllib.parse.urlparse(url)
        expected_canon = CANONICAL_BASE_URL.rstrip("/") + parsed_url.path.rstrip("/")
    else:
        expected_canon = url.rstrip("/")
    add(Check("Canonical URL", canon_url.rstrip("/") == expected_canon,
              f"canonical={canon_url!r}"))

    # ── 3. <title> ────────────────────────────────────────────────────────────
    title_m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    title = title_m.group(1).strip() if title_m else ""
    add(Check("<title> present", bool(title), f"title={title!r}"))

    # ── 4. <h1> ───────────────────────────────────────────────────────────────
    h1_m = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", html, re.IGNORECASE)
    h1_text = re.sub(r"<[^>]+>", "", h1_m.group(1)).strip() if h1_m else ""
    add(Check("<h1> present", bool(h1_text), f"h1={h1_text[:80]!r}"))

    # ── 5. Meta description ───────────────────────────────────────────────────
    meta_m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', html)
    if not meta_m:
        meta_m = re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']', html)
    meta_desc = meta_m.group(1).strip() if meta_m else ""
    add(Check("Meta description present", bool(meta_desc), f"desc={meta_desc[:80]!r}"))
    if meta_desc:
        add(Check("Meta description ≤160 chars", len(meta_desc) <= 160, f"length={len(meta_desc)}"))

    # ── 6. OG tags ────────────────────────────────────────────────────────────
    for prop in ("og:title", "og:description", "og:image"):
        og_m = re.search(rf'<meta[^>]+property=["\']{{0,1}}{re.escape(prop)}["\']{{0,1}}[^>]+content=["\']([^"\']*)["\']', html)
        val = og_m.group(1).strip() if og_m else ""
        add(Check(f"OG {prop}", bool(val), f"{val[:80]!r}"))

    # ── 7. og:image is a real image ───────────────────────────────────────────
    og_img_m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html)
    if og_img_m:
        og_img_url = og_img_m.group(1)
        if og_img_url.startswith("/"):
            parsed = urllib.parse.urlparse(url)
            og_img_url = f"{parsed.scheme}://{parsed.netloc}{og_img_url}"
        ok, note = is_real_image(og_img_url)
        add(Check("og:image is real image", ok, f"{og_img_url} — {note}"))

    # ── 8. All <img> src return real images ───────────────────────────────────
    img_srcs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
    broken_imgs = []
    for src in img_srcs:
        if src.startswith("data:"):
            continue
        if src.startswith("/"):
            parsed = urllib.parse.urlparse(url)
            src_full = f"{parsed.scheme}://{parsed.netloc}{src}"
        elif src.startswith("http"):
            src_full = src
        else:
            src_full = urllib.parse.urljoin(url, src)
        ok, note = is_real_image(src_full)
        if not ok:
            broken_imgs.append(f"{src} ({note})")
    add(Check("All <img> are real images", len(broken_imgs) == 0,
              "; ".join(broken_imgs) if broken_imgs else "all OK"))

    # ── 9. Schema markup ──────────────────────────────────────────────────────
    slug = url.rstrip("/").split("/")[-1]
    if slug not in CATEGORY_PAGES:
        has_schema = 'application/ld+json' in html
        add(Check("Schema (ld+json) present", has_schema))

    # ── 10. Inline hero <figure><img> ────────────────────────────────────────
    has_figure = bool(re.search(r'<figure[^>]*>[\s\S]*?<img[^>]+src=["\'][^"\']+["\']', html))
    if slug not in EXEMPT_FROM_IMAGE_CHECK and slug not in CATEGORY_PAGES:
        add(Check("Inline hero <figure><img>", has_figure,
                  "missing inline figure block" if not has_figure else "present"))
    # else: older post or category page, silently exempt

    # ── 11. Internal links not broken ────────────────────────────────────────
    all_hrefs = re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', html)
    internal_hrefs = []
    for h in all_hrefs:
        if h.startswith("/") or BASE_URL in h:
            internal_hrefs.append(h)

    broken_links = []
    with ThreadPoolExecutor(max_workers=MAX_LINK_WORKERS) as ex:
        futures = {ex.submit(check_link, h, url): h for h in set(internal_hrefs)}
        for fut in as_completed(futures):
            resolved, code, note = fut.result()
            if note == "skipped" or note.startswith("skipped"):
                continue
            if code >= 400 or code == 0:
                broken_links.append(f"{resolved} → {code}")

    add(Check("No broken internal links", len(broken_links) == 0,
              "; ".join(broken_links[:5]) if broken_links else "all OK"))

    return result


def format_result(r: PageResult) -> str:
    slug = r.url.rstrip("/").split("/")[-1]
    icon = "✅" if r.passed else "❌"
    lines = [f"{icon} {slug}"]
    for c in r.checks:
        if not c.passed:
            lines.append(f"   ✗ {c.name}: {c.detail}")
    if r.passed:
        lines.append(f"   All {len(r.checks)} checks passed")
    return "\n".join(lines)


def get_all_blog_urls(sitemap_path: Optional[str] = None) -> list[str]:
    """Return all /blog/<slug> URLs from sitemap or by scraping the blog index."""
    if sitemap_path:
        try:
            tree = ET.parse(sitemap_path)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            urls = [loc.text.strip() for loc in tree.findall(".//sm:loc", ns)
                    if "/blog/" in loc.text and loc.text.count("/") >= 4
                    and not loc.text.rstrip("/").endswith("/blog")]
            return sorted(set(urls))
        except Exception as e:
            print(f"⚠️  Could not parse sitemap: {e}")

    # Fallback: scrape blog index
    _, _, body, _ = fetch(f"{BASE_URL}/blog/")
    html = body.decode("utf-8", errors="replace")
    hrefs = re.findall(r'href=["\'](/blog/[a-z0-9-]+/?)["\']', html)
    urls = sorted({f"{BASE_URL}{h.rstrip('/')}" for h in hrefs
                   if h not in ("/blog/", "/blog")})
    return urls


def main():
    parser = argparse.ArgumentParser(description="Apollo Intelligence post-publish QA checker")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Check all live blog posts")
    group.add_argument("--sitemap", metavar="FILE", help="Check all URLs from sitemap.xml")
    parser.add_argument("urls", nargs="*", help="Specific URLs to check")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument("--fetch-base-url", default=BASE_URL, help="Base URL to fetch for apolloagent.ai URLs during local simulation.")
    parser.add_argument("--canonical-base-url", default="", help="Expected canonical base URL; defaults to each checked URL.")
    args = parser.parse_args()
    global FETCH_BASE_URL, CANONICAL_BASE_URL
    FETCH_BASE_URL = args.fetch_base_url.rstrip("/")
    CANONICAL_BASE_URL = args.canonical_base_url.rstrip("/")

    if args.all or args.sitemap:
        sitemap = args.sitemap if args.sitemap else None
        urls = get_all_blog_urls(sitemap_path=sitemap)
        print(f"Found {len(urls)} blog posts to check...\n")
    elif args.urls:
        urls = args.urls
    else:
        parser.print_help()
        sys.exit(1)

    results = []
    total_pass = 0
    total_fail = 0

    for url in urls:
        print(f"Checking {url} ...", end=" ", flush=True)
        r = qa_page(url)
        results.append(r)
        if r.passed:
            total_pass += 1
            print("✅")
        else:
            total_fail += 1
            print(f"❌ ({len(r.failures)} failures)")
        time.sleep(0.3)  # Be polite

    print("\n" + "=" * 60)
    print(f"QA REPORT — {time.strftime('%Y-%m-%d %H:%M MT')}")
    print("=" * 60)
    for r in results:
        print(format_result(r))

    print("\n" + "=" * 60)
    print(f"SUMMARY: {total_pass} passed, {total_fail} failed out of {len(results)} posts")

    if args.json:
        report = {
            "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "summary": {"passed": total_pass, "failed": total_fail, "total": len(results)},
            "results": [
                {
                    "url": r.url,
                    "passed": r.passed,
                    "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail}
                                for c in r.checks],
                }
                for r in results
            ],
        }
        with open("qa_report.json", "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nJSON report saved to qa_report.json")

    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
