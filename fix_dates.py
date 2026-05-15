#!/usr/bin/env python3
"""
Sync all dates across the site to match canonical publish dates.
Canonical source: PUBLISH_QUEUE.json publishDate (if present), else article HTML byline.
Only fixes dates adjacent to their slug href — never touches unrelated prose dates.
"""
import json, re, os, glob
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))

# ── Canonical date map ────────────────────────────────────────────────────────

with open(os.path.join(BASE, 'blog/PUBLISH_QUEUE.json')) as f:
    queue = json.load(f)

queue_dates = {}
for p in queue['queue']:
    try:
        d = datetime.strptime(p['publishDate'], '%Y-%m-%d')
        queue_dates[p['slug']] = d.strftime('%b %-d, %Y')
    except:
        pass

DATE_PAT = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+,\s+202\d'

def get_article_byline_date(slug):
    """Get the first date from the article's hero/byline section (not related cards)."""
    path = os.path.join(BASE, f'blog/{slug}.html')
    if not os.path.exists(path):
        return None
    with open(path) as f:
        html = f.read()
    m = re.search(DATE_PAT, html)
    return m.group(0) if m else None

CANONICAL = {}
ARTICLE_SLUGS = [
    'ai-news-march-2026', 'ai-agents-guide-2026', 'ai-powered-business-intelligence',
    '5-ai-automations-small-business', 'agency-60-percent-admin-reduction-case-study',
    'ai-for-operations-managers', 'the-real-cost-of-not-using-ai-2026',
    'gpt-5-5-multimodal-business', 'how-to-write-ai-prompts-that-actually-work-for-business-tasks',
    'ai-for-legal-teams', 'ecommerce-scaled-5m-3-person-team-ai', 'ai-hype-detector',
]
for slug in ARTICLE_SLUGS:
    if slug in queue_dates:
        CANONICAL[slug] = queue_dates[slug]
    else:
        d = get_article_byline_date(slug)
        if d:
            CANONICAL[slug] = d

print("Canonical dates:")
for s, d in CANONICAL.items():
    print(f"  {s}: {d}")


# ── Fix dates in listing/card files ──────────────────────────────────────────
# Strategy: for each slug, find blocks that reference /blog/{slug} and fix
# any date within the next 600 chars of the href occurrence.

def fix_card_dates_in_file(filepath, label):
    with open(filepath) as f:
        html = f.read()
    original = html
    total_fixed = 0

    for slug, correct_date in CANONICAL.items():
        # Match from href="/blog/{slug}" through the next 600 chars, replace dates within
        def fix_block(m):
            block = m.group(0)
            fixed_block = re.sub(DATE_PAT, correct_date, block)
            if fixed_block != block:
                nonlocal total_fixed
                old_dates = re.findall(DATE_PAT, block)
                for od in set(old_dates):
                    if od != correct_date:
                        print(f"  ✓ {label}: /blog/{slug}: '{od}' → '{correct_date}'")
                        total_fixed += 1
            return fixed_block

        pattern = rf'href="/blog/{re.escape(slug)}"[^"{{}}]*?(?=[^<]*<div[^>]*>){{0,3}}.{{0,600}}?(?={DATE_PAT})'
        # Simpler: match href to closing </article> or </a> then fix dates
        # Use a window: href through next 500 chars
        html = re.sub(
            rf'(href="/blog/{re.escape(slug)}"(?:.{{1,500}}?)(?={DATE_PAT}))',
            fix_block,
            html,
            flags=re.DOTALL
        )

    if html != original:
        with open(filepath, 'w') as f:
            f.write(html)
    elif total_fixed == 0:
        print(f"  ✅ {label}: all dates correct")

    return total_fixed


# ── Fix article byline/metadata (schema + hero span) only ────────────────────
# In article files, fix: schema datePublished/dateModified, hero <span> date,
# author row <span> date — but NOT dates in related article cards (those have hrefs).

def fix_article_own_dates(slug, correct_date):
    path = os.path.join(BASE, f'blog/{slug}.html')
    if not os.path.exists(path):
        return
    with open(path) as f:
        html = f.read()
    original = html
    fixed_count = 0

    # 1. Fix JSON-LD datePublished / dateModified
    def fix_jsonld_date(m):
        nonlocal fixed_count
        iso = datetime.strptime(correct_date, '%b %d, %Y').strftime('%Y-%m-%d') \
              if len(correct_date.split()[1].rstrip(',')) > 1 \
              else datetime.strptime(correct_date, '%b %-d, %Y').strftime('%Y-%m-%d')
        old_val = m.group(1)
        if old_val != iso:
            fixed_count += 1
            print(f"  ✓ blog/{slug}.html schema: '{old_val}' → '{iso}'")
        return f'"datePublished": "{iso}"'
    # Parse correct ISO date
    try:
        iso_date = datetime.strptime(correct_date, '%b %d, %Y').strftime('%Y-%m-%d')
    except ValueError:
        iso_date = datetime.strptime(correct_date, '%b %-d, %Y').strftime('%Y-%m-%d') \
                   if False else None
        # Universal parse
        for fmt in ('%b %d, %Y', '%b %-d, %Y'):
            try:
                iso_date = datetime.strptime(correct_date, fmt).strftime('%Y-%m-%d')
                break
            except:
                pass

    if iso_date:
        old_html = html
        html = re.sub(r'"datePublished":\s*"[^"]+"', f'"datePublished": "{iso_date}"', html)
        html = re.sub(r'"dateModified":\s*"[^"]+"', f'"dateModified": "{iso_date}"', html)
        if html != old_html:
            fixed_count += 1
            print(f"  ✓ blog/{slug}.html schema dates → {iso_date}")

    # 2. Fix <span>Month Day, Year</span> patterns in the HERO section (before article body)
    # Hero is everything before class="article-body" or id="article-body" or <!-- ARTICLE
    hero_end = html.find('class="article-body"')
    if hero_end == -1:
        hero_end = html.find('<!-- ARTICLE')
    if hero_end == -1:
        hero_end = len(html) // 3  # rough heuristic: first third of file

    hero = html[:hero_end]
    body = html[hero_end:]

    old_hero = hero
    # Replace full written date: "April 28, 2026" style
    written = datetime.strptime(correct_date, '%b %-d, %Y' if True else '%b %d, %Y')
    for fmt in ('%b %-d, %Y', '%b %d, %Y'):
        try:
            written = datetime.strptime(correct_date, fmt)
            break
        except:
            pass
    long_date = written.strftime('%B %-d, %Y')  # "April 28, 2026"

    # Fix short dates (May 10, 2026) and long dates (May 10, 2026) in hero
    hero = re.sub(DATE_PAT, correct_date, hero)
    hero = re.sub(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+,\s+202\d', long_date, hero)

    if hero != old_hero:
        fixed_count += 1
        print(f"  ✓ blog/{slug}.html hero date → {correct_date}")

    html = hero + body

    if html != original:
        with open(path, 'w') as f:
            f.write(html)
    elif fixed_count == 0:
        print(f"  ✅ blog/{slug}.html: dates correct")


# ── Run fixes ─────────────────────────────────────────────────────────────────

print("\nHomepage:")
fix_card_dates_in_file(os.path.join(BASE, 'index.html'), 'index.html')

print("\nblog/index.html:")
fix_card_dates_in_file(os.path.join(BASE, 'blog/index.html'), 'blog/index.html')

print("\nCategory pages:")
for page in ['ai-news', 'business-automation', 'case-studies', 'role-guides', 'industry-guides']:
    path = os.path.join(BASE, f'blog/{page}.html')
    if os.path.exists(path):
        fix_card_dates_in_file(path, f'blog/{page}.html')

print("\nArticle own dates (hero + schema only):")
for slug in ARTICLE_SLUGS:
    if slug in CANONICAL:
        fix_article_own_dates(slug, CANONICAL[slug])

print("\n✅ Date sync complete.")
