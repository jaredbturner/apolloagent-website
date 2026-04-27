# Apollo Intelligence Blog — Publishing Process

_Last updated: April 27, 2026_

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
2. Update `PUBLISH_QUEUE.json` status to "published"
3. Update blog index page and RSS feed
4. Git commit and push to trigger Cloudflare Pages deploy
5. Confirm in Discord: "✅ Published: [title] → apolloagent.ai/blog/<slug>"

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
2. If passes → publish automatically, notify Discord
3. If fails → alert Discord: "⚠️ Blog draft [title] needs review — factual concerns found"

## Content Standards

### Every Article Must Have
- Clear H1 title with target keywords
- Meta description (under 160 chars)
- Schema markup (Article type, author: Jared Turner)
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