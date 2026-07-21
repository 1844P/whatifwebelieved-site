# Wallpaper Evaluation & Application Thread — WhatIfWeBelieved

**Date:** July 20, 2026
**Site:** `http://127.0.0.1:8080/` (served from `C:\Users\catha\Desktop\whatifwebelieved-site\`)
**Goal:** Evaluate and apply the best Unsplash wallpaper for the WhatIfWeBelieved site.

---

## 1. Site Evaluation

### Purpose
**WhatIfWeBelieved** is a global faith & theology media ministry. It features:
- Featured teachings (YouTube video embeds)
- Articles (theological analysis, scripture study)
- Video library
- Global testimonials from 40+ countries
- A free book download ("Affirming Faith Through Thought")
- Community subscription

### Design Language
| Element | Value |
|---|---|
| Primary background | `#faf8f5` (warm cream) |
| Accent color | `#8b6914` (burnished gold) |
| Text primary | `#1a1a1a` (deep ink) |
| Serif font | EB Garamond |
| Sans font | Poppins |
| Existing textures | SVG paper grain, linen weave, diagonal pinstripes (CSS-only, 1–4% opacity) |

### Existing Wallpaper Research
The site already had a `WALLPAPER_RESEARCH.md` documenting 12 CSS-only texture recommendations (SVG feTurbulence noise, radial gradients, crosshatch patterns). All pure CSS/SVG, zero image downloads.

---

## 2. Wallpaper Selection from Unsplash

### Evaluation Criteria
For a faith & theology ministry, the ideal wallpaper should:
1. **Evoke divine presence** — light, creation, transcendence
2. **Complement the gold/cream palette** — warm tones, not cold
3. **Not distract from text** — works as a background, not a focal point
4. **Create contemplative mood** — encourage visitors to linger

### Candidates Evaluated

| # | Unsplash Photo | Description | Fit |
|---|---|---|---|
| 1 | `photo-1507400492013-162706c8c05e` | **Dramatic sky with divine light rays breaking through clouds** | **Selected** — Best thematic fit. Light rays = divine presence. Warm amber tones match gold palette. |
| 2 | `photo-1518837695005-2083093ee35b` | Sun rays breaking through dramatic clouds | Strong runner-up. Downloaded as backup (`hero-wallpaper-2.jpg`). |
| 3 | `photo-T_dAmNJdoMA` | Golden sun rays penetrate misty forest canopy | Nature-focused, less "divine" than clouds |
| 4 | `photo-wwBlw-VIVjQ` | Golden sunset with sun rays breaking through clouds | Similar to #1 but more sunset-oriented |

### Selected Wallpaper
**Image:** `images/hero-wallpaper.jpg` (203 KB)
**Source:** Unsplash `photo-1507400492013-162706c8c05e`
**Why:** Dramatic sky with golden light rays breaking through clouds directly evokes divine presence, revelation, and creation — the core themes of a faith theology ministry. The warm amber/gold tones naturally complement the existing `#8b6914` palette.

### Backup Wallpaper
**Image:** `images/hero-wallpaper-2.jpg` (234 KB)
**Source:** Unsplash `photo-1518837695005-2083093ee35b`

---

## 3. Application

### Changes Made to `index.html`

#### Hero Background Image
```css
.hero {
    /* ...existing styles... */
    background: url('images/hero-wallpaper.jpg') center/cover no-repeat;
}
```

#### Warm Cream Overlay (`::before`)
Ensures text readability on the left (text area) while letting the wallpaper show through on the right (video area).
```css
.hero::before {
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(
        135deg,
        rgba(250,248,245,0.82) 0%,    /* 82% opaque — text area */
        rgba(250,248,245,0.60) 35%,
        rgba(250,248,245,0.35) 65%,
        rgba(250,248,245,0.12) 100%   /* 12% opaque — video area */
    );
    z-index: 0;
    pointer-events: none;
}
```

#### Golden Glow (`::after`)
Adds warmth matching the site's gold accent color.
```css
.hero::after {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse 70% 50% at 70% 40%, rgba(139,105,20,0.06), transparent 60%);
    z-index: 0;
    pointer-events: none;
}
```

#### Particles Z-Index Adjustment
Particles canvas moved from `z-index: 0` to `z-index: 1` to sit above the overlay.
```css
#hero-particles {
    position: absolute; inset: 0; z-index: 1; pointer-events: none;
}
```

### Final Stacking Order
| Layer | Element | z-index |
|---|---|---|
| 1 (bottom) | `.hero` background-image (wallpaper) | — (element bg) |
| 2 | `.hero::before` (cream gradient overlay) | 0 |
| 3 | `.hero::after` (golden radial glow) | 0 |
| 4 | `#hero-particles` (canvas particles) | 1 |
| 5 (top) | `.hero-content` (text, buttons, video) | 2 |
| 5 (top) | `.hero-visual-wrapper` (YouTube embed) | 2 |
| 5 (top) | `.scroll-indicator` | 2 |

### No Responsive Changes Needed
The `background: center/cover no-repeat` automatically scales for mobile. The gradient overlay also scales proportionally. Existing responsive rules at `@media (max-width: 900px)` and `@media (max-width: 480px)` handle layout changes without conflicts.

---

## 4. File Inventory

| File | Status | Notes |
|---|---|---|
| `images/hero-wallpaper.jpg` | **New** | Primary wallpaper (203 KB) |
| `images/hero-wallpaper-2.jpg` | **New** | Backup wallpaper (234 KB) |
| `index.html` | **Modified** | Hero CSS updated with wallpaper + overlays |
| `WALLPAPER_RESEARCH.md` | Existing | CSS texture research (unchanged) |
| `WALLPAPER_THREAD.md` | **New** | This document |

---

## 5. How to Swap Wallpapers

To use the backup wallpaper instead:
```css
.hero {
    background: url('images/hero-wallpaper-2.jpg') center/cover no-repeat;
}
```

To use any new Unsplash image:
1. Save to `images/` folder
2. Update the `background` URL in `.hero`
3. Adjust overlay opacity if needed
