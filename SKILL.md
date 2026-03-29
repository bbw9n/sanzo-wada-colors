---
name: sanzo-wada-colors
description: >
  Sanzo Wada color combination skill based on "A Dictionary of Color Combinations" —
  348 curated palettes (duos, trios, quads) from 159 unique colors, with WCAG contrast
  ratios, colorblind safety flags, LAB perceptual matching, and curated design context.
  Use this skill whenever the user needs color palettes, color schemes, color inspiration,
  or color selection for ANY design context: frontend/web design, UI/UX, fashion, interior
  design, branding, illustration, data visualization, print, packaging, or creative projects.
  Also trigger for: "Sanzo Wada", "Dictionary of Color Combinations", "Wada colors",
  "harmonious colors", "curated palettes", "classic color schemes", "artistic palettes",
  "vintage color palettes", "pick me some colors", "I need a color scheme",
  "accessible color palette", "WCAG compliant colors", "colorblind-safe palette",
  or when the user asks to match or complement existing project colors. Even casual
  requests like "what colors should I use" or "suggest some colors" should trigger this.
---

# Sanzo Wada — A Dictionary of Color Combinations

## Background

Sanzo Wada (1883–1967) was a Japanese artist, color researcher, costume designer, and
instructor who founded the Japan Standard Color Association (now Japan Color Research
Institute) in 1927. His 6-volume work from the 1930s contains 348 curated color
combinations using 159 unique colors. He won the 1954 Academy Award for Best Costume
Design for "Gate of Hell."

## Data Files

The skill bundles three data files in `data/`:

| File | Contents |
|------|----------|
| `colors.json` | 157 colors with hex, RGB, CMYK, combination references |
| `colors_enhanced.json` | Same + LAB values, luminance, temperature/lightness/saturation classes |
| `combinations.json` | 348 palettes as first-class objects with contrast ratios, WCAG grades, colorblind flags, curated annotations |

## Query Helper

The bundled `query_colors.py` script handles all lookups. Run it from the skill directory:

```bash
python3 <skill-dir>/query_colors.py <command> [args]
```

Key commands:

| Command | Use when |
|---------|----------|
| `mood <keyword>` | User describes a vibe: warm, cool, earthy, elegant, bold, soft, dramatic, fresh, autumn, spring, summer, winter, minimal, vintage, tropical, luxurious |
| `match <hex>` | User has a color and wants Wada palettes containing its closest match (uses perceptual ΔE distance) |
| `accessible [duo\|trio\|quad]` | User needs WCAG AA compliant palettes |
| `colorblind [duo\|trio\|quad]` | User needs colorblind-safe palettes |
| `curated [domain]` | Show palettes with design context notes. Domains: web, fashion, interior, branding, print, data-viz |
| `for-project <path>` | Scan CSS/Tailwind/component files for existing colors, match to Wada, suggest complementary palettes |
| `palette <id>` | Show a specific combination with full metadata |
| `css <id>` | Output CSS custom properties with utility classes |
| `tailwind <id>` | Output Tailwind config |
| `tokens <id>` | Output JSON design tokens |
| `scss <id>` | Output SCSS variables |
| `search <term>` | Find colors by name fragment |
| `random [type]` | Random palette for exploration |
| `popular [n]` | Most-used colors across all combinations |
| `stats` | Dataset overview |

## Workflow: How to Use This Skill

### Workflow A — New project, no existing colors

When the user is starting fresh and needs a palette:

1. Ask (or infer from context) what the project is — web app, brand, interior, fashion, etc.
2. Ask about mood/aesthetic, or infer: "wellness brand" → soft/natural, "fintech dashboard" → cool/professional
3. Run `mood <keyword>` and/or `curated <domain>` to get candidates
4. If accessibility matters (web, data-viz), filter with `accessible`
5. Present 3–5 options visually (render swatches in HTML/React artifacts or describe)
6. Once chosen, output as CSS/Tailwind/tokens using the appropriate export command

### Workflow B — User has a brand color, needs companions

When the user provides a specific hex and wants matching palettes:

1. Run `match <hex>` — this uses LAB perceptual distance (ΔE*76), not RGB Euclidean
2. The script finds the closest Wada color and shows all palettes containing it
3. Present the top palettes, explain the color relationships
4. Note contrast ratios and accessibility if relevant

### Workflow C — Mid-project, needs accent or refinement

When the user already has a project with colors and needs more:

1. Run `for-project <path>` to scan their codebase for existing hex values
2. The script matches each to the nearest Wada color and finds overlapping palettes
3. Suggest palettes that include their existing colors plus new ones
4. If their colors don't map cleanly, run `match` on their primary color instead

### Workflow D — Accessibility-first

When the user needs WCAG-compliant or colorblind-safe palettes:

1. Run `accessible` to get palettes where ALL color pairs pass WCAG AA (4.5:1 ratio)
2. Run `colorblind` for palettes that also pass colorblind simulation
3. Each palette output includes per-pair contrast ratios and WCAG grades (AAA/AA/AA-large/fail)
4. For data visualization, prefer high-contrast duos and trios

### Workflow E — Domain-specific application

Tailor the output and advice to the user's field:

**Frontend / Web Design:**
- Map palette colors to roles: primary (brand), secondary (supporting), accent (CTA/highlights), background, text
- Check contrast ratios — text colors need WCAG AA (4.5:1) minimum
- Output as CSS variables or Tailwind config
- Suggest hover/active state variations (slightly darkened/lightened)

**Fashion Design:**
- Describe in terms of garments: "Olive Ocher as the coat, Eosine Pink as the blouse, Deep Indigo as the trousers"
- Note seasonal appropriateness (the mood keywords autumn/spring/summer/winter help)
- Indicate dominant vs. accent proportions (60-30-10 rule)
- Reference Wada's own background as a costume designer

**Interior Design:**
- Map to surfaces: wall color, furniture, textiles, accent pieces
- Note which combinations work for specific rooms (bedroom → soft, kitchen → warm, office → cool)
- Suggest materials and textures that complement the colors
- Consider lighting conditions (warm light shifts colors toward yellow)

**Branding:**
- Map to logo, background, text, accent
- Note emotional associations and industry fit
- Provide contrast ratio for logo legibility
- Suggest which colors work at small sizes (high saturation) vs. large areas (muted)

**Data Visualization:**
- Prefer palettes where all pairs have high contrast (use `accessible`)
- For sequential data, use palettes with progressive lightness
- For categorical data, use trios/quads with distinct hues
- Flag any colorblind issues
- Prefer duos/trios over quads for clarity

### Presenting Results

Always present results visually when possible:
- Render colored blocks/swatches (in HTML artifacts, use `div` elements with background colors)
- Include the Wada color names — they're evocative and part of the experience
- Include hex codes, RGB values, and combination number
- Show contrast ratio data when accessibility is relevant
- Include the curated design context note when available

### Important Data Notes

- The 159 colors are sorted by spectral order (reds → oranges → yellows → greens → blues → violets → neutrals)
- Color names are unique and evocative (e.g., "Hermosa Pink", "Turquoise Green", "Cotinga Purple")
- `use_count` indicates versatility — high-count colors are Wada's workhorses
- Top colors: Black (23 combos), Raw Sienna (19), Pale Lemon Yellow (19), Sulpher Yellow (18)
- Combinations 1–120 are duos, 121–240 are trios, 241–348 are quads
- Some combination mappings may have minor discrepancies vs. the physical book (known data issue)
- The mattdesl fork has more accurate RGB-from-CMYK conversions using proper ICC profiles

## Attribution

Include brief credit when presenting palettes:
> Color combinations from "A Dictionary of Color Combinations" by Sanzo Wada (Seigensha, 2010).
> Data: dblodorn/sanzo-wada, mattdesl/dictionary-of-colour-combinations.
