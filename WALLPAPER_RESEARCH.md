# Wallpaper & Texture Research — WhatIfWeBelieved
## Elegant Section-by-Section Background Recommendations

**Goal:** Seamless, elegant textures that cause visitors to linger — warm, editorial, contemplative.
**Palette reference:** Burnished gold (#8b6914), warm cream (#faf8f5), deep ink (#1a1a1a)

---

## Design Principles

1. **Subtlety is everything** — textures should be felt, not seen. Opacity 3-8% maximum.
2. **Zero image downloads** — all patterns use pure CSS/SVG for instant load times.
3. **Section differentiation** — each section gets a unique texture to create visual rhythm.
4. **Warm analog feel** — noise, linen, parchment textures over cold geometric grids.
5. **WCAG compliant** — textures never interfere with text contrast ratios.

---

## Section-by-Section Recommendations

### 1. BODY / PAGE BACKGROUND
**Texture:** Warm paper grain (SVG feTurbulence noise)
**Why:** Creates an aged parchment feel without actual parchment images. Adds warmth and depth to the cream background.

```css
body::before {
    content: '';
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    opacity: 0.03;
    background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E");
}
```

**Source:** Inspired by shadcn.io's "Hero Centered Noise Texture" pattern.
**Effect:** Subtle film-grain warmth. Makes the flat cream feel like real paper.

---

### 2. HERO SECTION
**Texture:** Radial golden glow + diagonal scripture watermark
**Why:** The hero is the first impression. A warm radial glow draws the eye to center, while a faded diagonal scripture text adds theological depth.

```css
.hero::before {
    content: '';
    position: absolute;
    inset: 0;
    z-index: 0;
    background:
        /* Warm golden radial glow from top */
        radial-gradient(ellipse 80% 50% at 50% 0%, rgba(139,105,20,0.04), transparent 60%),
        /* Diagonal scripture watermark */
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='600' height='300'%3E%3Ctext x='300' y='150' text-anchor='middle' dominant-baseline='central' font-family='Georgia,serif' font-size='18' fill='rgba(139,105,20,0.025)' transform='rotate(-25 300 150)'%3EIn the beginning was the Word%3C/text%3E%3C/svg%3E") repeat;
    pointer-events: none;
}
```

**Effect:** Warm golden ambient light from above + faded diagonal text creates a contemplative, library-like atmosphere.

---

### 3. NAVIGATION BAR
**Texture:** Micro linen weave (CSS repeating gradient)
**Why:** The nav is sticky and always visible. A barely-visible linen texture adds tactile quality without distraction.

```css
nav {
    background:
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='4' height='4'%3E%3Crect width='4' height='4' fill='%23ffffff'/%3E%3Crect width='1' height='1' x='0' y='0' fill='rgba(139,105,20,0.02)'/%3E%3Crect width='1' height='1' x='2' y='2' fill='rgba(139,105,20,0.02)'/%3E%3C/svg%3E") repeat,
        var(--bg-surface);
}
```

**Effect:** Imperceptible micro-check pattern that adds texture depth to the white nav bar.

---

### 4. STATS BAR
**Texture:** Subtle diagonal lines (CSS repeating gradient)
**Why:** Stats deserve visual weight. Thin diagonal lines add gravitas without heaviness.

```css
.stats-bar {
    background:
        repeating-linear-gradient(
            -45deg,
            transparent,
            transparent 10px,
            rgba(139,105,20,0.015) 10px,
            rgba(139,105,20,0.015) 11px
        ),
        var(--bg-surface);
}
```

**Effect:** Hairline diagonal pinstripes — like engraved stationery.

---

### 5. VOICES / TESTIMONIALS SECTION
**Texture:** Soft radial spotlight per card (CSS radial gradient)
**Why:** Testimonials are personal. A warm spotlight effect on each card creates intimacy.

```css
.voice-card {
    background:
        radial-gradient(ellipse 120% 80% at 50% 0%, rgba(139,105,20,0.02), transparent 70%),
        var(--bg-surface);
}
```

**Effect:** Each card has a gentle warm glow from the top, like candlelight on a page.

---

### 6. ARTICLES / FEATURED SECTION
**Texture:** Crosshatch pattern (CSS repeating gradient)
**Why:** Articles are scholarly. A crosshatch pattern evokes engraved book plates and academic tradition.

```css
.articles-grid {
    background:
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='8'%3E%3Cpath d='M0 0L8 8M8 0L0 8' stroke='rgba(139,105,20,0.02)' stroke-width='0.5'/%3E%3C/svg%3E") repeat,
        var(--bg-surface);
}

.article-card {
    background: var(--bg-surface);
}

.article-card:hover {
    background: var(--bg-surface-hover);
}
```

**Effect:** Faded crosshatch behind the grid — like old library bookcloth.

---

### 7. THEOLOGY FEATURED CARD
**Texture:** Parchment gradient + subtle diagonal stripes
**Why:** The theology card is the hero article. It should feel like a manuscript page.

```css
.article-card.theology-card {
    background:
        repeating-linear-gradient(
            45deg,
            transparent,
            transparent 20px,
            rgba(139,105,20,0.01) 20px,
            rgba(139,105,20,0.01) 21px
        ),
        linear-gradient(170deg, #fdfcf9 0%, #f8f4ed 40%, #f0ebe0 100%);
}
```

**Effect:** Warm parchment gradient with barely-visible diagonal ruling — like aged manuscript paper.

---

### 8. BOOK SECTION
**Texture:** Gold dust noise (SVG feTurbulence)
**Why:** The book is a premium offering. Gold dust noise adds luxury without being gaudy.

```css
.book-section {
    background:
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='g'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23g)' opacity='0.03'/%3E%3C/svg%3E"),
        linear-gradient(180deg, var(--bg-surface) 0%, #faf6f0 100%);
}
```

**Effect:** Warm parchment with gold-tinted noise — feels like holding a gilded book.

---

### 9. VIDEOS SECTION
**Texture:** Dark linen weave (CSS repeating gradient)
**Why:** Video sections benefit from darker tones. A dark linen adds cinematic texture.

```css
.videos-section {
    background:
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='4' height='4'%3E%3Crect width='4' height='4' fill='%23faf8f5'/%3E%3Crect width='1' height='1' x='0' y='0' fill='rgba(0,0,0,0.01)'/%3E%3Crect width='1' height='1' x='2' y='2' fill='rgba(0,0,0,0.01)'/%3E%3C/svg%3E") repeat;
}
```

**Effect:** Subtle woven texture that adds depth to the video grid background.

---

### 10. CTA (CALL TO ACTION) SECTION
**Texture:** Radial golden glow + paper grain
**Why:** CTAs need warmth and urgency. A golden glow draws the eye, paper grain adds substance.

```css
.cta-section {
    background:
        radial-gradient(ellipse 60% 80% at 50% 50%, rgba(139,105,20,0.04), transparent 70%),
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.02'/%3E%3C/svg%3E"),
        var(--bg-surface);
}
```

**Effect:** Warm ambient glow with paper texture — inviting and warm.

---

### 11. FOOTER
**Texture:** Deep warm gradient + micro noise
**Why:** The footer should feel grounded. A warm dark gradient with subtle noise adds closure.

```css
footer {
    background:
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.015'/%3E%3C/svg%3E"),
        linear-gradient(180deg, var(--bg-primary) 0%, #f0ebe3 100%);
}
```

**Effect:** Warm gradient descent with paper grain — a gentle close to the reading experience.

---

### 12. ARTICLE READER (LIGHTBOX)
**Texture:** Clean parchment gradient
**Why:** Long-form reading needs zero distraction. A gentle warm gradient reduces eye strain.

```css
.article-lightbox {
    background: linear-gradient(180deg, var(--bg-primary) 0%, #f8f4ed 100%);
}

.article-reader {
    max-width: 720px;
    margin: 0 auto;
    padding: 56px 32px 80px;
    background: transparent;
}
```

**Effect:** Warm cream-to-parchment gradient — like reading on aged paper.

---

## Summary: Texture Map by Section

| Section | Texture Type | Opacity | Effect |
|---|---|---|---|
| Body | SVG noise grain | 3% | Paper warmth |
| Hero | Radial gold + scripture watermark | 4% / 2.5% | Contemplative glow |
| Nav | Micro linen weave | 2% | Tactile quality |
| Stats | Diagonal pinstripes | 1.5% | Engraved stationery |
| Voices | Radial spotlight per card | 2% | Candlelight intimacy |
| Articles | Crosshatch pattern | 2% | Academic bookcloth |
| Theology card | Parchment gradient + diagonal | 1% | Manuscript page |
| Book | Gold dust noise | 3% | Gilded luxury |
| Videos | Dark linen weave | 1% | Cinematic depth |
| CTA | Radial gold + paper grain | 4% / 2% | Warm invitation |
| Footer | Warm gradient + micro noise | 1.5% | Grounded closure |
| Article reader | Parchment gradient | — | Reading comfort |

---

## Technical Notes

- **All patterns are pure CSS/SVG** — zero HTTP requests, instant load, infinitely scalable.
- **Colors use the warm gold palette** (`rgba(139,105,20,...)`) — consistent with the DESIGN.md.
- **Opacity is kept below 5%** — textures add depth without competing with content.
- **SVG feTurbulence** creates organic, non-repeating noise that never looks "stock."
- **CSS repeating gradients** create geometric patterns with zero image files.
- **All patterns are responsive** — they scale with the viewport automatically.

---

## Sources

- [SVG Backgrounds](https://www.svgbackgrounds.com/) — Free customizable SVG patterns
- [Texturize](https://texturize.app/) — Free seamless textures (parchment, linen, gold dust)
- [MagicPattern CSS Backgrounds](https://www.magicpattern.design/tools/css-backgrounds) — 50+ pure CSS patterns
- [shadcn.io Blocks](https://www.shadcn.io/blocks) — Noise texture and crosshatch hero patterns
- [DesignForge — Noise Gradients](https://www.designforge.dev/techniques/noise-gradient-backgrounds) — SVG turbulence technique
- [Medialoot](https://medialoot.com/blog/32-seamless-background-patterns/) — Curated subtle patterns
- [Envato — Golden Harmony](https://elements.envato.com/golden-harmony-elegant-gold-neutral-AKV9GZB) — Gold texture inspiration
