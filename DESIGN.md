# WhatIfWeBelieved — Elegant Editorial

> Design system for a global faith & theology ministry. Refined, warm, editorial elegance.

## Visual Theme & Atmosphere

A quiet, sophisticated editorial experience. Think aged parchment meets modern typography — warm, inviting, and dignified. The palette avoids cold corporate blues in favor of burnished gold and deep ink. The mood is contemplative: a reader should feel they are entering a library, not a dashboard.

## Color Palette & Roles

| Token | Hex | Role |
|---|---|---|
| `--bg-primary` | `#faf8f5` | Warm cream page background |
| `--bg-secondary` | `#ffffff` | Card and surface backgrounds |
| `--bg-surface` | `#ffffff` | Elevated surfaces (nav, cards) |
| `--bg-surface-hover` | `#f5f0eb` | Surface hover state |
| `--accent` | `#8b6914` | Primary accent — burnished gold |
| `--accent-light` | `#b8941e` | Accent hover / secondary accent |
| `--accent-dark` | `#6b4f10` | Accent pressed / deep gold |
| `--accent-muted` | `rgba(139,105,20,0.08)` | Accent background tint |
| `--accent-subtle` | `rgba(139,105,20,0.04)` | Very light accent wash |
| `--text-primary` | `#1a1a1a` | Primary text — near-black ink |
| `--text-secondary` | `#4a4540` | Body text — warm dark gray |
| `--text-tertiary` | `#7a7570` | Meta, dates, subtle text |
| `--text-inverse` | `#faf8f5` | Text on dark/accent backgrounds |
| `--border-subtle` | `#ebe6e0` | Light dividers |
| `--border-default` | `#d4cec6` | Standard borders |
| `--border-strong` | `#a8a098` | Emphasized borders |

## Typography Rules

| Use | Font | Weight | Size |
|---|---|---|---|
| Display / Hero | EB Garamond | 500 | 4.2rem |
| Section headings | EB Garamond | 600 | 2rem |
| Card titles | EB Garamond | 600 | 1.1rem |
| Body copy | EB Garamond | 400 | 1.05rem, line-height 1.85 |
| UI labels / Nav | Poppins | 400 | 0.8rem, letter-spacing 0.2px |
| Eyebrow tags | Poppins | 500 | 0.7rem, uppercase, letter-spacing 0.8px |
| Meta / dates | Poppins | 300 | 0.68rem, letter-spacing 0.3px |

Line-height for body: 1.85. Letter-spacing for headings: -0.3px (tight). Serif for all reading content; sans-serif for UI chrome only.

## Component Stylings

- **Buttons (primary):** `background: var(--accent)`, `color: var(--text-inverse)`, `border-radius: 6px`, subtle hover lift (`translateY(-1px)`)
- **Buttons (outline):** transparent bg, `border: 1px solid var(--border-default)`, accent color on hover
- **Cards:** white surface, 1px `var(--border-subtle)` border, 10px radius, no shadow (clean editorial)
- **Tags / Badges:** `var(--accent-muted)` bg, `var(--accent)` text, pill shape (100px radius)
- **Nav:** white surface, `var(--border-subtle)` border, 16px radius, sticky with 12px top offset
- **Section dividers:** 1px `var(--border-subtle)` bottom border on section headers

## Layout Principles

- Max-width: 1120px, centered
- Vertical rhythm: 96px section padding, 40px subsection gaps
- Grid: 3-column for cards/voices/videos, 4-column stats bar
- Generous whitespace — editorial breathing room, never cramped
- Hero: full-width with generous 80px vertical padding

## Depth & Elevation

Minimal elevation. The editorial tone relies on whitespace and border contrast, not shadows. Hover states use subtle background shifts (`--bg-surface-hover`) rather than shadow lifts. The hero video wrapper gets a gentle animated glow using `rgba(139,105,20,0.08)` instead of blue.

## Do's and Don'ts

### Do
- Use warm cream (`#faf8f5`) as the default page background
- Let typography carry the hierarchy — weight and size, not color bombardment
- Keep accent color reserved for interactive elements and emphasis
- Use EB Garamond for all reading content
- Maintain generous padding and line-height

### Don't
- Don't use cold blues or corporate grays as primary accents
- Don't add drop shadows to cards — use border contrast instead
- Don't use more than two typefaces
- Don't use pure black (`#000`) for body text — use `#1a1a1a`
- Don't apply accent color to large background fills

## Responsive Behavior

- Below 900px: hero stacks vertically, single-column grids, nav links collapse
- Below 480px: hero title shrinks to 2.1rem, stats stack, footer single-column
- Touch targets: minimum 44px for interactive elements on mobile

## Agent Prompt Guide

When generating UI for this project:
- Always read this DESIGN.md as the brand contract
- Use the warm cream + burnished gold palette — never cold blues
- Typography is EB Garamond (serif) for content, Poppins (sans) for UI chrome
- Cards are border-defined, not shadow-defined
- Keep the editorial, contemplative tone — this is a faith ministry, not a SaaS dashboard
- Accent usage: buttons, links, tags, hero emphasis italic text
