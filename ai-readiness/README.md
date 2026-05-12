# AI Readiness Assessment
**Apollo Intelligence · apolloagent.ai/ai-readiness/**

A fully self-contained, single-page assessment that scores businesses on AI readiness across 5 categories, gates results behind an email capture, and syncs leads into ActiveCampaign.

---

## File Structure

```
ai-readiness/
├── index.html                  # Full SPA — landing + assessment + gate + results
├── config.js                   # All integration settings (fill in before going live)
├── results-email-template.md   # ActiveCampaign email template with merge fields
└── README.md                   # This file
```

---

## How It Works

1. **Landing page** — Compelling hero, 3 stats, 5 category previews, social proof
2. **Assessment** — 13 questions across 5 categories, one at a time with animated progress
3. **Email gate** — Name + email + company (required to unlock results)
4. **Results** — Animated score gauge, category bars (red/yellow/green), top 3 recommendations, Calendly CTA
5. **ActiveCampaign** — Contact created/updated with score fields + tags + automation trigger (fire-and-forget, doesn't block results)

---

## Setup: ActiveCampaign Integration

### Step 1 — Get your credentials

1. Log in to ActiveCampaign
2. Go to **Settings → Developer** → copy your **API URL** and **API Key**
3. Go to **Lists** → find or create your leads list → note the **List ID**

### Step 2 — Create Custom Fields

In ActiveCampaign: **Settings → Custom Fields → New Field**

Create the following fields (all type: **Number** unless noted):

| Field Name | Type | Notes |
|---|---|---|
| AI Readiness Score | Number | Overall score 0–100 |
| Data Infrastructure Score | Number | Category % |
| Process Automation Score | Number | Category % |
| Customer Experience Score | Number | Category % |
| Content Marketing Score | Number | Category % |
| Strategy Leadership Score | Number | Category % |
| Score Label | Text | "Emerging", "Developing", etc. |
| Top Recommendation 1 | Text | Title of #1 rec |
| Top Recommendation 2 | Text | Title of #2 rec |
| Top Recommendation 3 | Text | Title of #3 rec |
| Company Name | Text | From gate form |

After creating each field, click it to see the **Field ID** (numeric, in the URL or field details).

### Step 3 — Fill in config.js

Open `config.js` and replace every `YOUR_*` / `FIELD_ID_*` placeholder:

```js
activeCampaign: {
  apiUrl: 'https://YOURACCOUNTNAME.api-us1.com',   // ← your AC URL
  apiKey: 'abc123...',                               // ← your API key
  listId: '1',                                       // ← your list ID
  customFields: {
    aiReadinessScore: '42',                          // ← numeric field IDs
    // ... etc
  },
  automationId: 7,  // ← ID of the automation to trigger (or null)
}
```

### Step 4 — Set up a CORS proxy (recommended)

ActiveCampaign's API doesn't allow direct browser requests due to CORS restrictions. The cleanest solution is a small Cloudflare Worker proxy.

#### Option A: Cloudflare Worker (recommended)

1. Create a new Worker at [dash.cloudflare.com](https://dash.cloudflare.com)
2. Paste this Worker code:

```js
export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': 'https://apolloagent.ai',
          'Access-Control-Allow-Methods': 'POST',
          'Access-Control-Allow-Headers': 'Content-Type',
        },
      });
    }

    const body   = await request.json();
    const AC_URL = env.AC_API_URL;   // Set as Worker secret
    const AC_KEY = env.AC_API_KEY;   // Set as Worker secret

    // Create or update contact
    const contactRes = await fetch(AC_URL + '/api/3/contacts', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'Api-Token': AC_KEY },
      body:    JSON.stringify({ contact: body.contact }),
    });
    const contactData = await contactRes.json();
    const contactId   = contactData?.contact?.id || contactData?.contacts?.[0]?.id;

    if (!contactId) {
      return new Response(JSON.stringify({ error: 'Contact creation failed', detail: contactData }), {
        status: 400,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      });
    }

    // Add to list
    if (body.listId) {
      await fetch(AC_URL + '/api/3/contactLists', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'Api-Token': AC_KEY },
        body:    JSON.stringify({ contactList: { list: body.listId, contact: contactId, status: 1 } }),
      });
    }

    // Apply tags
    if (body.tags && body.tags.length > 0) {
      const tagStr = body.tags.join(',');
      await fetch(AC_URL + '/api/3/contacts/' + contactId + '/tags', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'Api-Token': AC_KEY },
        body:    JSON.stringify({ contactTag: { contact: contactId, tag: tagStr } }),
      });
    }

    // Trigger automation
    if (body.automationId) {
      await fetch(AC_URL + '/api/3/contactAutomations', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'Api-Token': AC_KEY },
        body:    JSON.stringify({ contactAutomation: { contact: contactId, automation: body.automationId } }),
      });
    }

    return new Response(JSON.stringify({ success: true, contactId }), {
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': 'https://apolloagent.ai' },
    });
  },
};
```

3. Add Secrets in Worker Settings:
   - `AC_API_URL` = your AC API URL
   - `AC_API_KEY` = your AC API key

4. Deploy and note your Worker URL (e.g., `https://apollo-ac-proxy.YOUR_SUBDOMAIN.workers.dev`)

5. Update `config.js`:
   ```js
   proxyUrl: 'https://apollo-ac-proxy.YOUR_SUBDOMAIN.workers.dev',
   ```

#### Option B: Skip CORS proxy (simplest for now)

Leave `proxyUrl: null` and the assessment will attempt a direct API call. This will fail in most modern browsers due to CORS, **but** the results page will still show — the AC sync just won't happen silently. You can monitor failures in the browser console and set up the proxy later.

---

## Setup: ActiveCampaign Automation (Email Delivery)

1. Go to **Automations → New Automation**
2. Trigger: **Contact is added to a list** → select your leads list
3. Add condition: Tag contains `ai-readiness-assessment`
4. Action: **Send Email** → import the template from `results-email-template.md`
5. Map merge fields to your custom fields (see the merge fields table in that file)
6. Note the Automation ID (from the URL) and add it to `config.js` as `automationId`

---

## Deployment: Cloudflare Pages

The assessment is a static file — no build step required.

### Option A: Deploy as part of the main site

Since `ai-readiness/` is a subfolder of the main `website/` directory, it will automatically be deployed when you push the main site to Cloudflare Pages.

### Option B: Manual upload

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → Pages
2. Select your `apolloagent.ai` project → Deployments
3. Or just commit and push — Cloudflare Pages auto-deploys on git push

### Ensure the route works

Make sure your `_redirects` or routing config serves `ai-readiness/index.html` at `/ai-readiness/`. No changes should be needed if the subfolder structure is correct.

---

## Assessment Scoring

**Questions:** 13 total across 5 categories
**Scoring:** Each answer is worth 1–5 points based on AI maturity level

| Score Range | Tier Label | Description |
|---|---|---|
| 0–39 | Emerging | Early stage — biggest opportunity |
| 40–59 | Developing | Foundation in place, clear gaps |
| 60–79 | Advancing | Strong base, optimization needed |
| 80–100 | AI-Ready | Sophisticated — compound advantage |

**Category weights (questions per category):**
- Data & Infrastructure: 3 questions (max 15 pts)
- Process Automation: 3 questions (max 15 pts)
- Customer Experience: 3 questions (max 15 pts)
- Content & Marketing: 2 questions (max 10 pts)
- Strategy & Leadership: 2 questions (max 10 pts)
- **Total max raw: 65 points → normalized to 0–100**

---

## Customization

### Changing questions
Edit the `QUESTIONS` array in `index.html`. Each question needs:
- `id` — unique string
- `cat` — one of: `data`, `automation`, `cx`, `content`, `strategy`
- `catLabel`, `catIcon` — display text + emoji
- `text` — question text
- `options` — array of `{ text, score }` (score 1–5)

### Changing recommendations
Edit the `RECOMMENDATIONS` object in `index.html`. Add/change entries under each category key.

### Changing score tier thresholds
Edit the `getTier()` function — adjust the `score <= X` breakpoints.

### Changing the Calendly link
Update `config.js` → `calendlyUrl`. Also update the hardcoded links in the HTML (search for `calendly.com`).

---

## SEO Notes

- Page title: `Free AI Readiness Assessment | Apollo Intelligence`
- Meta description: Included and optimized
- OG / Twitter card: Configured
- Schema.org: `WebApplication` and `BreadcrumbList` markup included
- Canonical URL: `https://apolloagent.ai/ai-readiness/`

---

## Browser Support

Works in all modern browsers (Chrome, Firefox, Safari, Edge). No build tools, no dependencies, no framework. Pure HTML + CSS + vanilla JS.

---

## Questions?

Contact: hello@apolloagent.ai
