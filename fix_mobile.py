#!/usr/bin/env python3
"""
Apply all mobile/responsive fixes to apolloagent.ai static HTML files.
"""
import re
import os
import glob

SITE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Shared snippets ─────────────────────────────────────────────────────────

SKIP_LINK = '  <!-- SKIP TO CONTENT -->\n  <a href="#main-content" class="sr-only focus:not-sr-only" style="position:absolute;left:-9999px;top:auto;width:1px;height:1px;overflow:hidden;" onFocus="this.style.cssText=\'position:static;width:auto;height:auto;overflow:visible;padding:8px 16px;background:#3b52d4;color:#fff;z-index:9999;border-radius:4px;\'" onBlur="this.style.cssText=\'position:absolute;left:-9999px;top:auto;width:1px;height:1px;overflow:hidden;\'">Skip to main content</a>\n\n'

# Blog articles nav (links back to /#section)
BLOG_NAV_NEW = '''  <!-- NAV -->
  <nav class="sticky top-0 z-50 bg-white border-b border-slate-100">
    <div class="max-w-6xl mx-auto px-6 h-14 md:h-20 flex items-center justify-between">
      <a href="/" class="flex items-center">
        <picture>
          <source
            type="image/webp"
            srcset="/logo-mobile.webp 656w, /logo-tablet.webp 940w, /logo.webp 1181w"
            sizes="(max-width: 640px) 328px, 470px" />
          <img src="/logo.png" alt="Apollo Intelligence" class="h-12 md:h-16 w-auto" width="470" height="160" />
        </picture>
      </a>
      <!-- DESKTOP NAV -->
      <div class="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
        <a href="/#services" class="hover:text-slate-900 transition py-2">Services</a>
        <a href="/#how-it-works" class="hover:text-slate-900 transition py-2">How It Works</a>
        <a href="/#pricing" class="hover:text-slate-900 transition py-2">Pricing</a>
        <a href="/blog/" class="text-slate-900 font-semibold transition py-2">Blog</a>
        <a href="/#faq" class="hover:text-slate-900 transition py-2">FAQ</a>
      </div>
      <!-- HAMBURGER MENU BUTTON -->
      <button id="mobile-menu-btn" class="md:hidden flex flex-col gap-1.5 w-10 h-10 items-center justify-center" aria-label="Toggle mobile menu" aria-expanded="false">
        <span class="w-6 h-0.5 bg-slate-900 transition duration-300" id="menu-line-1"></span>
        <span class="w-6 h-0.5 bg-slate-900 transition duration-300" id="menu-line-2"></span>
        <span class="w-6 h-0.5 bg-slate-900 transition duration-300" id="menu-line-3"></span>
      </button>
      <a href="https://calendly.com/hello-apolloagent/30min" target="_blank" rel="noopener" class="hidden sm:block bg-brand text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-brand-dark transition">Book a Call</a>
    </div>
  </nav>

  <!-- MOBILE MENU -->
  <div id="mobile-menu" style="display:none;position:fixed;inset:0;top:56px;z-index:40;background:#fff;overflow-y:auto;" class="md:hidden">
    <div class="px-6 py-8 space-y-4">
      <a href="/#services" class="block text-lg font-medium text-slate-900 hover:text-brand transition py-3 px-2">Services</a>
      <a href="/#how-it-works" class="block text-lg font-medium text-slate-900 hover:text-brand transition py-3 px-2">How It Works</a>
      <a href="/#pricing" class="block text-lg font-medium text-slate-900 hover:text-brand transition py-3 px-2">Pricing</a>
      <a href="/blog/" class="block text-lg font-medium text-slate-900 hover:text-brand transition py-3 px-2">Blog</a>
      <a href="/#faq" class="block text-lg font-medium text-slate-900 hover:text-brand transition py-3 px-2">FAQ</a>
      <div class="border-t border-slate-100 pt-4 mt-4">
        <a href="https://calendly.com/hello-apolloagent/30min" target="_blank" rel="noopener" class="block bg-brand text-white text-center font-semibold py-3 rounded-lg hover:bg-brand-dark transition">Book a Call</a>
      </div>
    </div>
  </div>'''

# Blog index / non-article pages nav (links to /blog/ as active, back to /#section)
BLOG_INDEX_NAV_NEW = '''  <!-- NAV -->
  <nav class="sticky top-0 z-50 bg-white border-b border-slate-100">
    <div class="max-w-6xl mx-auto px-6 h-14 md:h-20 flex items-center justify-between">
      <a href="/" class="flex items-center">
        <picture>
          <source
            type="image/webp"
            srcset="/logo-mobile.webp 656w, /logo-tablet.webp 940w, /logo.webp 1181w"
            sizes="(max-width: 640px) 328px, 470px" />
          <img src="/logo.png" alt="Apollo Intelligence" class="h-12 md:h-16 w-auto" width="470" height="160" />
        </picture>
      </a>
      <!-- DESKTOP NAV -->
      <div class="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
        <a href="/#services" class="hover:text-slate-900 transition py-2">Services</a>
        <a href="/#how-it-works" class="hover:text-slate-900 transition py-2">How It Works</a>
        <a href="/#pricing" class="hover:text-slate-900 transition py-2">Pricing</a>
        <a href="/blog/" class="text-slate-900 font-semibold transition py-2">Blog</a>
        <a href="/#faq" class="hover:text-slate-900 transition py-2">FAQ</a>
      </div>
      <!-- HAMBURGER MENU BUTTON -->
      <button id="mobile-menu-btn" class="md:hidden flex flex-col gap-1.5 w-10 h-10 items-center justify-center" aria-label="Toggle mobile menu" aria-expanded="false">
        <span class="w-6 h-0.5 bg-slate-900 transition duration-300" id="menu-line-1"></span>
        <span class="w-6 h-0.5 bg-slate-900 transition duration-300" id="menu-line-2"></span>
        <span class="w-6 h-0.5 bg-slate-900 transition duration-300" id="menu-line-3"></span>
      </button>
      <a href="https://calendly.com/hello-apolloagent/30min" target="_blank" rel="noopener" class="hidden sm:block bg-brand text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-brand-dark transition">Book a Call</a>
    </div>
  </nav>

  <!-- MOBILE MENU -->
  <div id="mobile-menu" style="display:none;position:fixed;inset:0;top:56px;z-index:40;background:#fff;overflow-y:auto;" class="md:hidden">
    <div class="px-6 py-8 space-y-4">
      <a href="/#services" class="block text-lg font-medium text-slate-900 hover:text-brand transition py-3 px-2">Services</a>
      <a href="/#how-it-works" class="block text-lg font-medium text-slate-900 hover:text-brand transition py-3 px-2">How It Works</a>
      <a href="/#pricing" class="block text-lg font-medium text-slate-900 hover:text-brand transition py-3 px-2">Pricing</a>
      <a href="/blog/" class="block text-lg font-medium text-slate-900 hover:text-brand transition py-3 px-2">Blog</a>
      <a href="/#faq" class="block text-lg font-medium text-slate-900 hover:text-brand transition py-3 px-2">FAQ</a>
      <div class="border-t border-slate-100 pt-4 mt-4">
        <a href="https://calendly.com/hello-apolloagent/30min" target="_blank" rel="noopener" class="block bg-brand text-white text-center font-semibold py-3 rounded-lg hover:bg-brand-dark transition">Book a Call</a>
      </div>
    </div>
  </div>'''

MOBILE_MENU_JS = '''
  <script>
  // ── Mobile menu toggle ──────────────────────────────────────────────────────
  (function() {
    var btn = document.getElementById('mobile-menu-btn');
    var menu = document.getElementById('mobile-menu');
    var l1 = document.getElementById('menu-line-1');
    var l2 = document.getElementById('menu-line-2');
    var l3 = document.getElementById('menu-line-3');
    if (!btn || !menu) return;
    function openMenu() {
      menu.style.display = 'block';
      btn.setAttribute('aria-expanded', 'true');
      l1.style.transform = 'rotate(45deg) translateY(8px)';
      l2.style.opacity = '0';
      l3.style.transform = 'rotate(-45deg) translateY(-8px)';
      document.body.style.overflow = 'hidden';
    }
    function closeMenu() {
      menu.style.display = 'none';
      btn.setAttribute('aria-expanded', 'false');
      l1.style.transform = 'none';
      l2.style.opacity = '1';
      l3.style.transform = 'none';
      document.body.style.overflow = '';
    }
    btn.addEventListener('click', function() {
      menu.style.display === 'block' ? closeMenu() : openMenu();
    });
    menu.querySelectorAll('a').forEach(function(a) {
      a.addEventListener('click', closeMenu);
    });
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') closeMenu();
    });
  })();
  // ───────────────────────────────────────────────────────────────────────────
  </script>
'''

# ─── Transformation helpers ───────────────────────────────────────────────────

def add_preconnects(html):
    """Add preconnect hints for GTM and Beehiiv if not already present."""
    if 'preconnect" href="https://www.googletagmanager.com"' in html:
        return html
    target = '<link rel="preconnect" href="https://fonts.googleapis.com" />'
    insert = (
        '<link rel="preconnect" href="https://www.googletagmanager.com" />\n'
        '  <link rel="preconnect" href="https://subscribe-forms.beehiiv.com" />\n'
        '  '
    )
    return html.replace(target, insert + target, 1)

def add_skip_link(html):
    """Add skip-to-main-content link before the NAV if not present."""
    if 'Skip to main content' in html:
        return html
    return html.replace('  <!-- NAV -->', SKIP_LINK + '  <!-- NAV -->', 1)

def add_main_id(html):
    """Ensure <main> has id="main-content" for skip link target."""
    return re.sub(r'<main>', '<main id="main-content">', html)

def fix_homepage_nav(html):
    """Already patched in-place; just ensure mobile menu JS is present."""
    return html

def fix_blog_nav(html, is_article=True):
    """Replace the blog page nav with the mobile-friendly version."""
    # Match the nav block (from <!-- NAV --> to </nav>)
    # We'll match the entire old nav + inject new nav + mobile menu
    pattern = r'  <!-- NAV -->\s*<nav[^>]*>.*?</nav>'
    replacement = BLOG_NAV_NEW if is_article else BLOG_INDEX_NAV_NEW
    return re.sub(pattern, replacement, html, count=1, flags=re.DOTALL)

def fix_article_hero_h1(html):
    """Scale down the article hero H1 for mobile."""
    # text-4xl md:text-5xl → text-2xl sm:text-3xl md:text-4xl lg:text-5xl
    html = re.sub(
        r'class="text-4xl md:text-5xl font-extrabold text-white leading-tight',
        'class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-extrabold text-white leading-tight',
        html
    )
    return html

def fix_author_avatar(html):
    """Make article body author avatar responsive."""
    # Author row avatar: w-12 h-12 → w-10 h-10 md:w-12 md:h-12
    html = html.replace(
        'class="w-12 h-12 bg-slate-200 rounded-full flex items-center justify-center text-slate-500 font-bold"',
        'class="w-10 h-10 md:w-12 md:h-12 bg-slate-200 rounded-full flex items-center justify-center text-slate-500 font-bold shrink-0"'
    )
    # Related articles CTA avatar: w-16 h-16 → w-12 h-12 md:w-16 md:h-16
    html = html.replace(
        'class="w-16 h-16 bg-slate-200 rounded-full flex items-center justify-center text-slate-500 font-bold text-lg shrink-0"',
        'class="w-12 h-12 md:w-16 md:h-16 bg-slate-200 rounded-full flex items-center justify-center text-slate-500 font-bold text-lg shrink-0"'
    )
    return html

def fix_cta_section_h2(html):
    """Scale bottom CTA H2 for mobile (text-4xl → responsive)."""
    html = re.sub(
        r'<h2 class="text-4xl font-bold text-white mb-4">',
        '<h2 class="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-4">',
        html
    )
    return html

def inject_mobile_menu_js(html):
    """Inject mobile menu JS - before </body> if present, else at end of file."""
    if 'Mobile menu toggle' in html:
        return html
    if '</body>' in html:
        return html.replace('</body>', MOBILE_MENU_JS + '</body>', 1)
    # Files that don't have </body> (e.g. truncated blog articles) - append at end
    return html.rstrip() + '\n' + MOBILE_MENU_JS

def fix_blog_card_grid(html):
    """Change blog card grid from md:grid-cols-3 to md:grid-cols-2 lg:grid-cols-3."""
    html = re.sub(
        r'class="grid md:grid-cols-3 gap-8"',
        'class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"',
        html
    )
    return html

def fix_modal_padding(html):
    """Ensure contact modal inner div has safe mobile padding."""
    # The modal already has width:calc(100% - 2rem) which is fine; add padding tweak
    html = html.replace(
        'padding:2rem;position:relative;max-width:520px;width:calc(100% - 2rem)',
        'padding:1.5rem;position:relative;max-width:520px;width:calc(100% - 1.5rem)'
    )
    return html

# ─── Apply to homepage ────────────────────────────────────────────────────────

def process_homepage(path):
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    html = add_preconnects(html)
    html = add_skip_link(html)
    html = add_main_id(html)
    html = fix_blog_card_grid(html)
    html = fix_modal_padding(html)
    html = inject_mobile_menu_js(html)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'  ✓ {os.path.relpath(path)}')

# ─── Apply to blog article pages ─────────────────────────────────────────────

def process_blog_article(path):
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    html = add_preconnects(html)
    html = add_skip_link(html)
    html = add_main_id(html)
    html = fix_blog_nav(html, is_article=True)
    html = fix_article_hero_h1(html)
    html = fix_author_avatar(html)
    html = fix_cta_section_h2(html)
    html = fix_blog_card_grid(html)
    html = inject_mobile_menu_js(html)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'  ✓ {os.path.relpath(path)}')

# ─── Apply to blog listing/category pages ────────────────────────────────────

def process_blog_listing(path):
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    html = add_preconnects(html)
    html = add_skip_link(html)
    html = add_main_id(html)
    html = fix_blog_nav(html, is_article=False)
    html = fix_blog_card_grid(html)
    html = inject_mobile_menu_js(html)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'  ✓ {os.path.relpath(path)}')

# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('\n🔧 Applying mobile/responsive fixes...\n')

    # Homepage
    print('Homepage:')
    process_homepage(os.path.join(SITE_DIR, 'index.html'))

    # Blog article pages (all .html files that aren't category/index/listing pages)
    LISTING_PAGES = {'index.html', 'ai-news.html', 'business-automation.html',
                     'case-studies.html', 'industry-guides.html', 'role-guides.html'}
    print('\nBlog articles:')
    for path in sorted(glob.glob(os.path.join(SITE_DIR, 'blog', '*.html'))):
        fname = os.path.basename(path)
        if fname in LISTING_PAGES:
            continue
        process_blog_article(path)

    # Blog listing / category pages
    print('\nBlog listing/category pages:')
    for fname in LISTING_PAGES:
        path = os.path.join(SITE_DIR, 'blog', fname)
        if os.path.exists(path):
            process_blog_listing(path)

    print('\n✅ All fixes applied.\n')
