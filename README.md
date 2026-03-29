# 🎨 Sanzo Wada — A Dictionary of Color Combinations

An agent skill that brings Sanzo Wada's 348 curated color palettes into your coding workflow. Built on the open [Agent Skills](https://agentskills.io) standard (`SKILL.md`), compatible with Claude Code, OpenAI Codex CLI, and other tools that support the format.

---

## What's inside

**159 named colors** and **348 hand-curated combinations** (120 duos, 120 trios, 108 quads) from Sanzo Wada's classic 1930s reference book, digitized with:

- **L\*a\*b\* perceptual color matching** — find Wada colors closest to any hex value using Delta E, not naive RGB distance
- **WCAG contrast ratios** — every color pair in every combination pre-graded (AAA / AA / AA-large / fail)
- **Colorblind safety flags** — palettes flagged for potential red-green confusion
- **Curated design context** — 30 palettes annotated with mood, best-fit domains (web, fashion, interior, branding, print, data-viz), and usage notes
- **Project scanner** — point it at your codebase, it matches your existing colors to Wada palettes and suggests complements
- **Multi-format export** — CSS custom properties, Tailwind config, SCSS variables, JSON design tokens

---

## Installation

### Claude Code

Claude Code discovers skills from `~/.claude/skills/` (global) or `.claude/skills/` (per-project).

**Global install** (available in all projects):

```bash
# Clone or copy the skill folder
cp -r sanzo-wada-colors ~/.claude/skills/sanzo-wada-colors
```

**Per-project install** (scoped to one repo):

```bash
# From your project root
mkdir -p .claude/skills
cp -r sanzo-wada-colors .claude/skills/sanzo-wada-colors
```

Claude Code picks up new skills automatically — no restart needed. Once installed, Claude will load the skill whenever you ask about colors, palettes, or design. You can also invoke it explicitly:

```
> Use the sanzo-wada-colors skill to find an accessible palette for my dashboard
```

### OpenAI Codex CLI

Codex discovers skills from `~/.codex/skills/`. The SKILL.md format is the same.

```bash
cp -r sanzo-wada-colors ~/.codex/skills/sanzo-wada-colors
```

Restart Codex (or start a new session) after installing. You can mention the skill explicitly with `$sanzo-wada-colors`, or Codex will load it implicitly when your prompt matches the description.

### Other compatible agents

Any tool that supports the [Agent Skills open standard](https://agentskills.io) can use this skill. The pattern is the same: copy the folder into the agent's skills directory. Known compatible agents include Cursor (`.cursor/skills/`), Windsurf, Aider, and others — check your agent's docs for the exact path.

### Claude.ai (web/app)

You can also upload the skill as a `.zip` in **Claude.ai → Customize → Skills**:

```bash
# Create a zip from the skill folder
cd sanzo-wada-colors && zip -r ../sanzo-wada-colors.zip . && cd ..
```

Then go to **Customize → Skills** and upload `sanzo-wada-colors.zip`. Make sure **Code execution and file creation** is enabled in Settings → Capabilities.

---

## Verify it works

After installing, try one of these in your agent:

```
> Suggest a warm color palette for a restaurant website
> Find Wada palettes that match #3B82F6
> I need an accessible color scheme for a data dashboard — show me WCAG AA options
> Scan my project and suggest complementary Wada colors
```

You can also run the helper script directly to explore the data:

```bash
python3 ~/.claude/skills/sanzo-wada-colors/query_colors.py stats
python3 ~/.claude/skills/sanzo-wada-colors/query_colors.py mood autumn
python3 ~/.claude/skills/sanzo-wada-colors/query_colors.py match "#E11D48"
python3 ~/.claude/skills/sanzo-wada-colors/query_colors.py accessible trio
python3 ~/.claude/skills/sanzo-wada-colors/query_colors.py curated web
```

---

## Use cases

### 🖥️ Frontend & web design

You're building a landing page and need a color system. Instead of staring at coolors.co, ask:

```
> Pick a color palette for a wellness SaaS product — something soft and calming,
> and make sure it passes WCAG AA for text contrast. Give me the Tailwind config.
```

The skill returns curated Wada palettes filtered for soft/calm mood and WCAG AA compliance, then exports directly as a Tailwind config you can drop into `tailwind.config.js`.

**What you get:** CSS custom properties, Tailwind color config, SCSS variables, or JSON design tokens — whatever your stack uses. Plus contrast ratios so you know which color pairs are safe for text.

### 👗 Fashion design

You're designing a seasonal collection and want historically-informed color harmonies:

```
> Suggest autumn color combinations from Sanzo Wada for a women's outerwear line.
> Which color should dominate and which should accent?
```

The skill draws from Wada's earthy/warm palettes and explains the 60-30-10 proportion rule — which colors work as the coat (dominant), the scarf or lining (secondary), and the buttons or trim (accent). Wada was himself a costume designer who won an Academy Award, so these combinations have real garment heritage.

### 🏠 Interior design

You're selecting paint colors and furnishing tones for a room:

```
> I'm designing a Scandinavian-style living room. Show me cool, muted Wada palettes
> and map each color to walls, furniture, and textiles.
```

The skill filters for cool/minimal palettes and suggests role assignments: wall color (the lightest), furniture (mid-tone), textile accents (the boldest). It considers that warm artificial light shifts colors toward yellow, so it may recommend slightly cooler choices than they appear on screen.

### 📊 Data visualization

You need chart colors that are distinguishable, accessible, and not ugly:

```
> Give me a 4-color palette for a bar chart that's colorblind-safe and WCAG compliant
```

The skill filters for quad combinations that pass both colorblind simulation and contrast ratio checks, then exports as a ready-to-use array. It flags any palettes where sequential colors might be confused under deuteranopia.

### 🎨 Branding & identity

You have a brand color and need a complete system:

```
> My brand color is #2D3748. Find Wada palettes that include something close to it,
> and suggest a full primary/secondary/accent system with CSS variables.
```

The skill uses LAB perceptual matching to find the nearest Wada color (probably Slate Color or Dark Tyrian Blue), pulls all combinations containing it, and maps each to brand roles — primary, secondary, accent — with contrast ratio validation for logo legibility.

### 🔍 Mid-project color refinement

Your app looks flat and needs an accent color:

```
> Scan my project's CSS files and suggest a Wada accent color that complements
> what I'm already using
```

The skill reads your `*.css`, `*.scss`, `*.tsx`, Tailwind config, and other source files, extracts hex values, matches each to the nearest Wada color, and finds palettes that overlap with your existing scheme. It then recommends the "missing" color from those palettes as your accent.

### 🎲 Exploration & learning

You just want to browse beautiful color combinations:

```
> Show me 5 random Wada trios
> What are the most popular colors Wada used across all his combinations?
> Show me all the curated palettes for print design
```

---

## File structure

```
sanzo-wada-colors/
├── SKILL.md                    # Skill instructions (what the agent reads)
├── README.md                   # This file (for humans)
├── query_colors.py             # CLI helper — all lookup commands
├── build_enhanced.py           # Regenerate enhanced data from base colors
└── data/
    ├── colors.json             # 157 colors (hex, RGB, CMYK, combination refs)
    ├── colors_enhanced.json    # + LAB values, luminance, temperature/lightness/saturation
    └── combinations.json       # 348 palettes with contrast ratios, WCAG grades, curated notes
```

## CLI reference

| Command | Description |
|---|---|
| `palette <id>` | Show combination with contrast data and curated notes |
| `search <term>` | Find colors by name (e.g., `search turquoise`) |
| `match <hex>` | Perceptual match to closest Wada color + its palettes |
| `mood <keyword>` | Filter by mood: warm, cool, earthy, elegant, bold, soft, dramatic, fresh, autumn, spring, summer, winter, minimal, vintage, tropical, luxurious |
| `accessible [duo\|trio\|quad]` | Only WCAG AA compliant palettes |
| `colorblind [duo\|trio\|quad]` | Colorblind-safe + WCAG AA-large palettes |
| `curated [domain]` | Annotated palettes by domain: web, fashion, interior, branding, print, data-viz |
| `for-project <path>` | Scan codebase colors, suggest complements |
| `css <id> [--prefix name]` | CSS custom properties + utility classes |
| `tailwind <id>` | Tailwind config |
| `scss <id>` | SCSS variables + palette map |
| `tokens <id>` | JSON design tokens |
| `random [duo\|trio\|quad]` | Random palette |
| `popular [n]` | Most-used colors |
| `all [duo\|trio\|quad]` | List all palettes |
| `stats` | Dataset summary |
| `preview <ids\|mood\|all>` | Generate interactive HTML preview, open in browser. Accepts combo IDs (`42 125`), mood keywords (`autumn`), or `all` / `curated` / `accessible` |

---

## About Sanzo Wada

**Sanzo Wada** (和田三造, 1883–1967) was a Japanese artist, art instructor, costume designer, and color researcher. He founded the Japan Standard Color Association (now Japan Color Research Institute) in 1927, and his original 6-volume work from the 1930s catalogs 348 color combinations using 159 named colors. He received the 1954 Academy Award for Best Costume Design for *Gate of Hell* and was recognized as a Person of Cultural Merit by the Japanese government in 1958.

The book [*A Dictionary of Color Combinations*](https://en.seigensha.com/books/978-4-86152-247-5/) (Seigensha, 2010) is a modern reprint of his work, and remains a beloved reference for designers worldwide.

## Data sources & credits

- **Interactive web version**: [sanzo-wada.dmbk.io](https://sanzo-wada.dmbk.io) by Dain M. Blodorn Kim ([dblodorn/sanzo-wada](https://github.com/dblodorn/sanzo-wada))
- **Cleaned dataset with ICC-profiled RGB**: [mattdesl/dictionary-of-colour-combinations](https://github.com/mattdesl/dictionary-of-colour-combinations) by Matt DesLauriers
- **R package**: [jmaasch/sanzo](https://github.com/jmaasch/sanzo) on CRAN
- **Publisher**: [Seigensha Art Publishing](https://en.seigensha.com/books/978-4-86152-247-5/)

## License

The skill code (SKILL.md, query_colors.py, build_enhanced.py) is MIT licensed. The color data originates from the open-source projects linked above (MIT). The original book is © Seigensha Art Publishing.
