# Apollo Intelligence Blog — Publishing Process

_Last updated: May 13, 2026_

## Overview

**Publication:** Apollo Intelligence Blog
**Cadence:** 3 articles per week (Tuesday, Thursday, Saturday)
**Platform:** Static HTML on apolloagent.ai (Cloudflare Pages)
**Byline:** Jared Turner, Founder — Apollo Intelligence LLC
**Voice:** Confident, direct, practical — "the smart friend who runs an AI company and tells you the truth"

## Directory Structure

```
website/blog/
  drafts/           ← New drafts land here (auto-generated)
  approved/         ← Jared approved, waiting for publish date
  published/        ← Moved here after going live
  CONTENT_CALENDAR.md
  PUBLISH_QUEUE.json ← Tracks approval status and publish dates
  *.html            ← Live blog posts (root level)
```

## Weekly Generation Schedule

| Day | Time (MT) | Action |
|-----|-----------|--------|
| **Monday** | 9:00 AM | Cron generates Tuesday's draft → Discord notification |
| **Wednesday** | 9:00 AM | Cron generates Thursday's draft → Discord notification |
| **Friday** | 9:00 AM | Cron generates Saturday's draft → Discord notification |

### Publish Timing
- **Jared approves** → Draft moves to `approved/`, PUBLISH_QUEUE.json updated with status "approved"
- **Jared doesn't review by publish date** → Auto-publish check runs at 7:00 AM on publish day:
  1. Checks PUBLISH_QUEUE.json for drafts still in "pending_review"
  2. Runs factual accuracy check on the content
  3. If accurate → publishes without review
  4. If concerns found → sends Discord alert asking Jared to review

### Daily Auto-Publish Check
| Day | Time (MT) | Action |
|-----|-----------|--------|
| **Tuesday** | 7:00 AM | Check for unreviewed drafts → fact-check → publish if accurate |
| **Thursday** | 7:00 AM | Check for unreviewed drafts → fact-check → publish if accurate |
| **Saturday** | 7:00 AM | Check for unreviewed drafts → fact-check → publish if accurate |

### LinkedIn Auto-Post
After each blog post goes live (manually approved or auto-published), it's shared to Jared's LinkedIn profile automatically.
| Day | Time (MT) | Action |
|-----|-----------|--------|
| **Tuesday** | 8:00 AM | Post any newly published Tuesday blog to LinkedIn |
| **Thursday** | 8:00 AM | Post any newly published Thursday blog to LinkedIn |
| **Saturday** | 8:00 AM | Post any newly published Saturday blog to LinkedIn |

The LinkedIn cron checks PUBLISH_QUEUE.json for entries with `status: published` and `linkedInPosted: false`, crafts a post from the article title/summary, and posts via LinkedIn API. If the API fails (e.g., token expired), it alerts Discord and leaves `linkedInPosted: false` for retry.

## Category Mapping

Every blog post belongs to exactly one category. The category determines which filter page(s) the post appears on.

| Category | Filter Page | Slug | Color Scheme | Badge Label |
|----------|-------------|------|--------------|-------------|
| AI News & Analysis | `ai-news.html` | `ai-news` | purple-900 → indigo-700 | AI News & Analysis |
| Business Automation | `business-automation.html` | `business-automation` | amber-800 → orange-600 | Business Automation |
| Role Guides | `role-guides.html` | `role-guides` | slate-800 → blue-900 (legal) or emerald-900 → green-700 (ops) | Role Guide (Legal) / Role Guide (Ops) |
| Case Studies | `case-studies.html` | `case-studies` | rose-900 → orange-700 (ecommerce), red-900 → red-700 (cost), slate-900 → slate-700 (agency) | Case Study |
| Industry Guides | `industry-guides.html` | `industry-guides` | slate-800 → blue-900 | Industry Guide (Legal) |

### Current Post → Category Assignments

| Post Slug | Category |
|-----------|----------|
| `ai-news-march-2026` | ai-news |
| `ai-agents-guide-2026` | ai-news |
| `gpt-5-5-multimodal-business` | ai-news |
| `5-ai-automations-small-business` | business-automation |
| `ai-powered-business-intelligence` | business-automation |
| `how-to-write-ai-prompts-that-actually-work-for-business-tasks` | business-automation |
| `ai-for-operations-managers` | role-guides |
| `ai-for-legal-teams` | role-guides, industry-guides |
| `agency-60-percent-admin-reduction-case-study` | case-studies |
| `the-real-cost-of-not-using-ai-2026` | case-studies |
| `ecommerce-scaled-5m-3-person-team-ai` | case-studies |

> **Note:** Some posts span two categories (e.g., `ai-for-legal-teams` is both a Role Guide and an Industry Guide for legal). Add the card to both category pages in that case.

### Category Card HTML Template

When adding a new post to any category page or the main index, use this card template. Replace the placeholders in curly braces:

```html
<article class="group" data-category="{category-slug}">
  <a href="/blog/{post-slug}" class="block">
    <div class="bg-gradient-to-br {gradient-colors} rounded-2xl h-48 flex items-end p-6 mb-4">
      <span class="text-xs font-bold uppercase tracking-wider text-white bg-white/20 px-3 py-1 rounded-full">{Badge Label}</span>
    </div>
    <h3 class="text-lg font-bold text-slate-900 mb-2 group-hover:text-brand transition">{Post Title}</h3>
    <p class="text-slate-500 text-sm leading-relaxed line-clamp-2 mb-4">{Meta Description or 2-sentence summary}</p>
    <div class="flex items-center gap-3 text-xs text-slate-400">
      <div class="w-7 h-7 bg-slate-200 rounded-full flex items-center justify-center text-slate-500 font-bold text-xs">JT</div>
      <span>Jared Turner</span>
      <span>&middot;</span>
      <span>{Publish Date, e.g. May 12, 2026}</span>
      <span>&middot;</span>
      <span>{X} min read</span>
    </div>
    <div class="mt-3 text-brand text-sm font-semibold group-hover:underline">Read Article &rarr;</div>
  </a>
</article>
```

For category pages that don't use `data-category` filtering, omit the `data-category` attribute from the `<article>` tag.

> **Ordering rule:** All article grids — both `blog/index.html` and every category page — must be ordered **newest → oldest** (top to bottom). Always insert new post cards at the **top** of the `<div id="article-grid">` block, above existing cards.

## Draft Generation Process

Each cron run:

1. **Check PUBLISH_QUEUE.json** — what's already in the pipeline? What's the next calendar slot?
2. **Read CONTENT_CALENDAR.md** — find the next unwritten topic
3. **Search current AI news** for relevant angles to weave in
4. **Read an existing published post** to match HTML template exactly (nav, footer, CSS, schema markup, CTA block)
5. **Write full HTML blog post** (1,200–1,500 words)
6. **Save to** `drafts/<slug>.html`
7. **Update PUBLISH_QUEUE.json** with new entry (status: "pending_review", publish_date, filename)
8. **Send Discord notification** to #projects with:
   - Post title
   - Target publish date
   - Full post content (or key excerpt)
   - "Reply **publish <filename>** to approve, or give feedback to revise"

## Approval Workflow

### Jared Approves
When Jared replies "publish <filename>":
1. Move `drafts/<filename>.html` → root `blog/<filename>.html`
2. Update `PUBLISH_QUEUE.json` status to "approved" (NOT "published" yet)
3. **Do NOT git push immediately.** Instead, schedule the git push for the publish date:
   - Set a cron job to run at 7:00 AM MT on the publish date that does: `git add . && git commit -m "Publish blog: <title>" && git push`
   - Update `PUBLISH_QUEUE.json` status to "published" only after the scheduled push
4. Add the new post URL to `sitemap.xml`
5. Add the new post card to `blog/index.html` (with correct `data-category` attribute — see Category Mapping table). **Insert at the top of the article grid** (newest post first). The grid must always be ordered newest → oldest.
6. Add the new post card to **every relevant category page** (see Category Mapping). **Insert the card so the page remains in newest → oldest order.** If a post spans multiple categories (e.g., role-guides + industry-guides), add it to all applicable pages. Replace any "More articles coming soon" placeholder if present.
7. Submit the new URL to Google Search Console Indexing API: `python3 scripts/gsc_index.py https://apolloagent.ai/blog/<slug>` (if the script exists)
8. Confirm in Discord: "✅ Scheduled for publication on [date]: [title] → apolloagent.ai/blog/<slug> (GSC indexing submitted)"

### Jared Requests Changes
When Jared gives feedback:
1. Revise the draft based on feedback
2. Save updated version to `drafts/<filename>.html`
3. Send revised version to Discord for re-review

### Auto-Publish (No Review)
If a draft is still "pending_review" at 7:00 AM on its publish date:
1. Run factual accuracy check:
   - Are named products/features real and current?
   - Are statistics sourced and not fabricated?
   - Are tool recommendations accurate (features exist, pricing correct)?
   - No misrepresentations or unsupported claims?
2. If passes → publish automatically (follow steps 1–8 from "Jared Approves" section, including adding cards to index + category pages in newest → oldest order)
3. If fails → alert Discord: "⚠️ Blog draft [title] needs review — factual concerns found"

## Content Standards

### Every Article Must Have
- Clear H1 title with target keywords
- Meta description (under 160 chars)
- Schema markup (Article type, author: Jared Turner)
- **One inline article image** (see Image Requirements below)
- Internal links (2–3 to other blog posts or service pages) — **mandatory, not optional**. Every article body must contain at least 2 contextual internal links to other blog posts. Link naturally within paragraphs, not just in the "Related Articles" section.
- CTA at the end: book a free strategy call at apolloagent.ai
- Open Graph tags for social sharing
- Target 1,200–1,500 words
- Written in second person ("you") with concrete examples

### Voice Checklist
- [ ] Reads like a knowledgeable advisor, not a content farm
- [ ] Zero filler — every paragraph earns its place
- [ ] At least one specific example, stat, or tool name per section
- [ ] Actionable takeaway in every section
- [ ] No hype words (revolutionary, game-changing, disruptive) unless quoting someone

### What To Avoid
- ❌ Fabricated statistics or "studies show" without a source
- ❌ Claiming features that don't exist in recommended tools
- ❌ More than 2 affiliate links per article (stay editorial)
- ❌ Generic "AI is transforming everything" openings

## Image Requirements

Every blog post must include **one AI-generated hero image** embedded inline within the article body.

### Generation
- Generate using `image_generate` tool with a prompt matching the article topic and apolloagent.ai brand style (dark navy/slate background, orange accents, editorial illustration or conceptual graphic)
- Aspect ratio: **16:9**
- Style: professional editorial — clean, conceptual, slightly witty where appropriate. No stock photo look.

### Format & Optimization
- Convert the generated PNG to **WebP** using `cwebp -q 85`
- Target output size: under 200KB
- Save to: `website/images/blog/<slug>-hero.webp`
- Never embed a raw PNG in a published post

### Placement
- Place the image **inline in the article body** — not as a full-width banner above the content
- Best position: immediately before the first major `<h2>` section (typically the second or third section of the article)
- Wrap in a `<figure>` tag with a `<figcaption>` describing the image in one sentence
- Use `loading="lazy"` and `decoding="async"` on the `<img>` tag
- Include descriptive `alt` text for accessibility and SEO

### OG Image
- Update the `<meta property="og:image">` tag to point to the published WebP URL: `https://apolloagent.ai/images/blog/<slug>-hero.webp`

### HTML Template
```html
<figure class="my-8">
  <img
    src="/images/blog/<slug>-hero.webp"
    alt="Descriptive alt text for the image"
    width="1536"
    height="1024"
    loading="lazy"
    decoding="async"
    class="w-full rounded-xl shadow-lg"
  />
  <figcaption class="text-center text-sm text-slate-400 mt-3">One-sentence caption that adds context.</figcaption>
</figure>
```

### Publish Checklist Addition
When publishing (manual or auto), the image WebP must be committed alongside the HTML: `git add images/blog/<slug>-hero.webp blog/<slug>.html`

---

## Research Sources
Same as newsletter — see NEWSLETTER_PROCESS.md for Tier 1 and Tier 2 sources.

## Affiliate Links
Same registry as newsletter — see AFFILIATE_LINKS.md. Max 2 affiliate links per article. **Use Make.com (not Zapier)** for automation platform mentions — Make has a direct affiliate link, Zapier requires manual lead entry. Prefer Make.com and Google Workspace (live affiliates).

## File Naming Convention
```
blog/
  drafts/          ← auto-generated HTML drafts
  approved/         ← Jared-approved, awaiting publish date
  published/         ← archive of published posts (moved after deploy)
  CONTENT_CALENDAR.md
  PUBLISH_QUEUE.json ← { "queue": [{ "slug": "...", "title": "...", "status": "pending_review|approved|published|needs_review|skipped", "publishDate": "2026-04-28", "draftPath": "drafts/slug.html", "publishedUrl": "https://...", "linkedInPosted": true|false }] }
  *.html            ← live posts at root level
```

---
_Process maintained by Apollo. Update when cadence, format, or affiliates change._