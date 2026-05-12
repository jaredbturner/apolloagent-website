# Apollo Intelligence — AI Readiness Results Email Template

> **Usage:** Import this as an email template in ActiveCampaign.
> Replace `%MERGE_TAG%` placeholders with your actual ActiveCampaign personalization tags.
> Trigger this email via an Automation that fires when the contact is created with the tag `ai-readiness-assessment`.

---

## Email Settings

| Field | Value |
|---|---|
| **From Name** | Apollo Intelligence |
| **From Email** | hello@apolloagent.ai |
| **Reply-To** | hello@apolloagent.ai |
| **Subject Line** | Your AI Readiness Score: {{SCORE_LABEL}} ({{AI_READINESS_SCORE}}/100) |
| **Preview Text** | Here's what your score means — and your top 3 AI opportunities, {{FIRSTNAME}}. |

---

## HTML Email Body

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Your AI Readiness Score — Apollo Intelligence</title>
  <style>
    body { margin: 0; padding: 0; background: #f8fafc; font-family: 'Inter', Arial, sans-serif; }
    .wrapper { max-width: 620px; margin: 0 auto; padding: 32px 16px; }
    .card { background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 2px 16px rgba(0,0,0,0.07); }
    .header { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 40px 40px 32px; text-align: center; }
    .logo-text { color: #ffffff; font-size: 20px; font-weight: 800; letter-spacing: -0.3px; }
    .logo-dot { color: #6b7ff0; }
    .header h1 { color: #ffffff; font-size: 26px; font-weight: 800; margin: 24px 0 8px; line-height: 1.3; }
    .header p { color: #94a3b8; font-size: 15px; margin: 0; }
    .score-badge { display: inline-block; margin: 20px 0 0; }
    .score-number { font-size: 72px; font-weight: 800; color: #ffffff; line-height: 1; display: block; }
    .score-label { display: inline-block; padding: 6px 18px; border-radius: 100px; font-size: 13px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; margin-top: 8px; }
    .label-emerging  { background: rgba(239,68,68,0.2);  color: #fca5a5; }
    .label-developing { background: rgba(245,158,11,0.2); color: #fcd34d; }
    .label-advancing  { background: rgba(245,158,11,0.2); color: #fcd34d; }
    .label-aiready    { background: rgba(34,197,94,0.2);  color: #86efac; }
    .body { padding: 36px 40px; }
    .greeting { font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 12px; }
    .summary { font-size: 15px; color: #475569; line-height: 1.7; margin-bottom: 32px; }
    .section-title { font-size: 13px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #6b7ff0; margin-bottom: 16px; }
    .cat-row { margin-bottom: 14px; }
    .cat-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
    .cat-name { font-size: 14px; font-weight: 600; color: #1e293b; }
    .cat-score { font-size: 13px; font-weight: 700; padding: 2px 8px; border-radius: 100px; }
    .score-red    { background: #fee2e2; color: #dc2626; }
    .score-yellow { background: #fef3c7; color: #d97706; }
    .score-green  { background: #dcfce7; color: #16a34a; }
    .bar-bg { height: 8px; background: #f1f5f9; border-radius: 100px; overflow: hidden; }
    .bar-fill { height: 8px; border-radius: 100px; }
    .bar-red    { background: #ef4444; }
    .bar-yellow { background: #f59e0b; }
    .bar-green  { background: #22c55e; }
    .divider { border: none; border-top: 1px solid #e2e8f0; margin: 32px 0; }
    .rec-item { display: flex; gap: 16px; margin-bottom: 24px; }
    .rec-num { width: 32px; height: 32px; background: #eff1fe; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 800; color: #3b52d4; flex-shrink: 0; }
    .rec-title { font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 4px; }
    .rec-desc { font-size: 14px; color: #64748b; line-height: 1.6; }
    .cta-section { background: linear-gradient(135deg, #2d3fb8 0%, #4338ca 100%); border-radius: 12px; padding: 32px; text-align: center; margin-top: 32px; }
    .cta-section h2 { color: #ffffff; font-size: 20px; font-weight: 800; margin-bottom: 10px; }
    .cta-section p { color: rgba(255,255,255,0.8); font-size: 14px; line-height: 1.65; margin-bottom: 22px; }
    .cta-btn { display: inline-block; background: #ffffff; color: #2d3fb8; font-size: 15px; font-weight: 700; padding: 14px 28px; border-radius: 10px; text-decoration: none; }
    .cta-trust { color: rgba(255,255,255,0.6); font-size: 12px; margin-top: 12px; }
    .footer { padding: 24px 40px; text-align: center; border-top: 1px solid #f1f5f9; }
    .footer p { font-size: 12px; color: #94a3b8; line-height: 1.7; margin: 0; }
    .footer a { color: #6b7ff0; text-decoration: none; }
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="card">

      <!-- Header / Score -->
      <div class="header">
        <div class="logo-text">Apollo<span class="logo-dot"> Intelligence</span></div>
        <h1>Your AI Readiness Report</h1>
        <p>Personalized results for %FIRSTNAME%</p>
        <div class="score-badge">
          <span class="score-number">%AI_READINESS_SCORE%</span>
          <!-- Swap class based on score label: label-emerging / label-developing / label-advancing / label-aiready -->
          <span class="score-label label-%SCORE_LABEL_SLUG%">%SCORE_LABEL%</span>
        </div>
      </div>

      <!-- Body -->
      <div class="body">
        <p class="greeting">Hi %FIRSTNAME%,</p>
        <p class="summary">
          Thanks for completing the Apollo Intelligence AI Readiness Assessment.
          Based on your answers, here's a complete picture of where your business
          stands — and exactly where the biggest opportunities are.
        </p>

        <!-- Category Breakdown -->
        <p class="section-title">Category Breakdown</p>

        <div class="cat-row">
          <div class="cat-header">
            <span class="cat-name">🗄️ Data &amp; Infrastructure</span>
            <!-- Swap score class: score-red / score-yellow / score-green -->
            <span class="cat-score score-%DATA_COLOR%">%DATA_INFRA_SCORE%%</span>
          </div>
          <div class="bar-bg"><div class="bar-fill bar-%DATA_COLOR%" style="width:%DATA_INFRA_SCORE%%"></div></div>
        </div>

        <div class="cat-row">
          <div class="cat-header">
            <span class="cat-name">⚙️ Process Automation</span>
            <span class="cat-score score-%AUTO_COLOR%">%PROCESS_AUTOMATION_SCORE%%</span>
          </div>
          <div class="bar-bg"><div class="bar-fill bar-%AUTO_COLOR%" style="width:%PROCESS_AUTOMATION_SCORE%%"></div></div>
        </div>

        <div class="cat-row">
          <div class="cat-header">
            <span class="cat-name">💬 Customer Experience</span>
            <span class="cat-score score-%CX_COLOR%">%CUSTOMER_EXPERIENCE_SCORE%%</span>
          </div>
          <div class="bar-bg"><div class="bar-fill bar-%CX_COLOR%" style="width:%CUSTOMER_EXPERIENCE_SCORE%%"></div></div>
        </div>

        <div class="cat-row">
          <div class="cat-header">
            <span class="cat-name">✍️ Content &amp; Marketing</span>
            <span class="cat-score score-%CONTENT_COLOR%">%CONTENT_MARKETING_SCORE%%</span>
          </div>
          <div class="bar-bg"><div class="bar-fill bar-%CONTENT_COLOR%" style="width:%CONTENT_MARKETING_SCORE%%"></div></div>
        </div>

        <div class="cat-row">
          <div class="cat-header">
            <span class="cat-name">🧭 Strategy &amp; Leadership</span>
            <span class="cat-score score-%STRATEGY_COLOR%">%STRATEGY_LEADERSHIP_SCORE%%</span>
          </div>
          <div class="bar-bg"><div class="bar-fill bar-%STRATEGY_COLOR%" style="width:%STRATEGY_LEADERSHIP_SCORE%%"></div></div>
        </div>

        <hr class="divider" />

        <!-- Recommendations -->
        <p class="section-title">🚀 Your Top 3 AI Opportunities</p>
        <p style="font-size:14px;color:#64748b;margin-bottom:20px;">
          Based on your weakest categories, these are the highest-ROI AI moves for your business right now.
        </p>

        <div class="rec-item">
          <div class="rec-num">1</div>
          <div>
            <div class="rec-title">%TOP_RECOMMENDATION_1%</div>
            <div class="rec-desc">This is your #1 priority. Addressing this gap will have the most immediate impact on your team's efficiency and your ability to scale with AI.</div>
          </div>
        </div>

        <div class="rec-item">
          <div class="rec-num">2</div>
          <div>
            <div class="rec-title">%TOP_RECOMMENDATION_2%</div>
            <div class="rec-desc">Once your #1 is in place, this becomes your next highest-leverage move — typically delivering results within 30-60 days of implementation.</div>
          </div>
        </div>

        <div class="rec-item">
          <div class="rec-num">3</div>
          <div>
            <div class="rec-title">%TOP_RECOMMENDATION_3%</div>
            <div class="rec-desc">Rounding out your AI roadmap, this opportunity will help you build a compounding advantage over competitors who haven't made this move yet.</div>
          </div>
        </div>

        <!-- CTA -->
        <div class="cta-section">
          <h2>Ready to turn this into a real plan?</h2>
          <p>
            In a free 30-minute strategy call, we'll walk through your results together,
            build out a concrete AI roadmap for your business, and show you exactly
            what we'd build — with real timelines and ROI estimates.
          </p>
          <a href="https://calendly.com/hello-apolloagent/30min" class="cta-btn">
            Get Your Custom AI Roadmap →
          </a>
          <p class="cta-trust">Free · 30 minutes · No commitment</p>
        </div>

      </div>

      <!-- Footer -->
      <div class="footer">
        <p>
          © 2026 Apollo Intelligence LLC · <a href="https://apolloagent.ai">apolloagent.ai</a><br />
          You're receiving this because you completed the AI Readiness Assessment.<br />
          <a href="%UNSUBSCRIBE_URL%">Unsubscribe</a> · <a href="https://apolloagent.ai/privacy-policy.html">Privacy Policy</a>
        </p>
      </div>

    </div>
  </div>
</body>
</html>
```

---

## Merge Fields Reference

| Merge Tag | Source | Description |
|---|---|---|
| `%FIRSTNAME%` | Contact first name | Personalization |
| `%AI_READINESS_SCORE%` | Custom field: `ai_readiness_score` | Overall score (0–100) |
| `%SCORE_LABEL%` | Custom field: `score_label` | "Emerging", "Developing", "Advancing", or "AI-Ready" |
| `%SCORE_LABEL_SLUG%` | Derived from score label | Lowercase slug for CSS class |
| `%DATA_INFRA_SCORE%` | Custom field: `data_infra_score` | 0–100 |
| `%PROCESS_AUTOMATION_SCORE%` | Custom field: `process_automation_score` | 0–100 |
| `%CUSTOMER_EXPERIENCE_SCORE%` | Custom field: `customer_experience_score` | 0–100 |
| `%CONTENT_MARKETING_SCORE%` | Custom field: `content_marketing_score` | 0–100 |
| `%STRATEGY_LEADERSHIP_SCORE%` | Custom field: `strategy_leadership_score` | 0–100 |
| `%TOP_RECOMMENDATION_1%` | Custom field: `top_recommendation_1` | Top recommendation title |
| `%TOP_RECOMMENDATION_2%` | Custom field: `top_recommendation_2` | #2 recommendation title |
| `%TOP_RECOMMENDATION_3%` | Custom field: `top_recommendation_3` | #3 recommendation title |
| `%DATA_COLOR%` | Derived in automation | "red", "yellow", or "green" based on score |
| `%AUTO_COLOR%` | Derived in automation | Same pattern |
| `%CX_COLOR%` | Derived in automation | Same pattern |
| `%CONTENT_COLOR%` | Derived in automation | Same pattern |
| `%STRATEGY_COLOR%` | Derived in automation | Same pattern |
| `%UNSUBSCRIBE_URL%` | ActiveCampaign built-in | Auto-filled by AC |

> **Note on color fields:** ActiveCampaign's conditional content blocks can set these based on score ranges. Alternatively, simplify by using a single neutral gray bar color in the email and only using color on the web results page.

---

## Plain Text Version

```
Your AI Readiness Score: %SCORE_LABEL% (%AI_READINESS_SCORE%/100)

Hi %FIRSTNAME%,

Thanks for taking the Apollo Intelligence AI Readiness Assessment.
Here's your full breakdown:

CATEGORY SCORES
─────────────────────────────────
Data & Infrastructure:   %DATA_INFRA_SCORE%%
Process Automation:      %PROCESS_AUTOMATION_SCORE%%
Customer Experience:     %CUSTOMER_EXPERIENCE_SCORE%%
Content & Marketing:     %CONTENT_MARKETING_SCORE%%
Strategy & Leadership:   %STRATEGY_LEADERSHIP_SCORE%%

YOUR TOP 3 AI OPPORTUNITIES
─────────────────────────────────
1. %TOP_RECOMMENDATION_1%
2. %TOP_RECOMMENDATION_2%
3. %TOP_RECOMMENDATION_3%

─────────────────────────────────
READY TO BUILD YOUR AI ROADMAP?

Book a free 30-minute strategy call and we'll walk through your results, 
build out a concrete plan, and show you exactly what we'd implement:

https://calendly.com/hello-apolloagent/30min

Free · 30 minutes · No commitment required.

─────────────────────────────────
© 2026 Apollo Intelligence LLC
https://apolloagent.ai
Unsubscribe: %UNSUBSCRIBE_URL%
```
