/**
 * Apollo Intelligence — AI Readiness Assessment
 * Configuration File
 *
 * ─────────────────────────────────────────────────────────────────
 * BEFORE GOING LIVE, replace every placeholder marked with ⚠️
 * ─────────────────────────────────────────────────────────────────
 */

const ASSESSMENT_CONFIG = {

  // ─── Calendly ──────────────────────────────────────────────────
  calendlyUrl: 'https://calendly.com/hello-apolloagent/30min',

  // ─── ActiveCampaign ────────────────────────────────────────────
  activeCampaign: {
    // ⚠️  Your ActiveCampaign account URL (no trailing slash)
    // Format: https://YOURACCOUNTNAME.api-us1.com
    apiUrl: 'https://apolloagent.api-us1.com',

    // ⚠️  Your ActiveCampaign API Key
    // Found at: Settings → Developer → API Access
    apiKey: '22da711bdf147117e2b192c63578681078c5c808f4abe2244e30fe889f9b1920c57caf40',

    // ⚠️  The list ID to add contacts to
    // Found at: Lists → hover a list → note the ID in the URL
    listId: '3',

    // ⚠️  ActiveCampaign Custom Field IDs
    // Create these under: Settings → Custom Fields → New Custom Field
    // Then fill in the numeric IDs here
    customFields: {
      aiReadinessScore:        '2',   // Text field — overall score 0–100
      dataInfraScore:          '3',   // Text field — category %
      processAutomationScore:  '4',   // Text field — category %
      customerExperienceScore: '5',   // Text field — category %
      contentMarketingScore:   '6',   // Text field — category %
      strategyLeadershipScore: '7',   // Text field — category %
      scoreLabel:              '8',   // Text field — "Emerging", "Developing", etc.
      topRecommendation1:      '9',   // Text field
      topRecommendation2:      '10',  // Text field
      topRecommendation3:      '11',  // Text field
      companyName:             '12',  // Text field
    },

    // ⚠️  Tag names to apply to the contact
    // These should already exist in ActiveCampaign (auto-created on first use)
    tags: {
      base:   ['ai-readiness-assessment', 'lead'],
      low:    'score-low',     // score 0–39
      medium: 'score-medium',  // score 40–69
      high:   'score-high',    // score 70–100
    },

    // Automation ID to trigger after contact is created/updated
    automationId: 1, // "Submits a form" → Send Email automation
  },

  // ─── Site ──────────────────────────────────────────────────────
  site: {
    name:     'Apollo Intelligence',
    url:      'https://apolloagent.ai',
    logoUrl:  '/logo.webp',
    logoAlt:  'Apollo Intelligence',
    email:    'hello@apolloagent.ai',
  },

  // ─── CORS proxy ───────────────────────────────────────────────
  // Cloudflare Worker proxy for ActiveCampaign API calls (deployed)
  proxyUrl: 'https://apollo-ac-proxy.jared-turner-f80.workers.dev'

};

// Make available globally
window.ASSESSMENT_CONFIG = ASSESSMENT_CONFIG;
