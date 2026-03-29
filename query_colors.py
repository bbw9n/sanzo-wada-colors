#!/usr/bin/env python3
"""
Sanzo Wada Color Combinations — Enhanced Query Helper
=====================================================

Usage:
  python3 query_colors.py palette <combo_id>                # Show combination with contrast data
  python3 query_colors.py search <term>                     # Search colors by name
  python3 query_colors.py match <hex> [--top N]             # Find closest Wada color (LAB perceptual)
  python3 query_colors.py random [duo|trio|quad]            # Random combination
  python3 query_colors.py mood <keyword>                    # Suggest palettes by mood/season
  python3 query_colors.py popular [N]                       # Most-used colors
  python3 query_colors.py accessible [duo|trio|quad]        # WCAG AA compliant palettes only
  python3 query_colors.py colorblind [duo|trio|quad]        # Colorblind-safe palettes
  python3 query_colors.py curated [domain]                  # Curated palettes (web|fashion|interior|branding|print|data-viz)
  python3 query_colors.py for-project <path>                # Scan project files, suggest complementary palettes
  python3 query_colors.py css <combo_id> [--prefix NAME]    # Output CSS custom properties
  python3 query_colors.py tailwind <combo_id>               # Output Tailwind config
  python3 query_colors.py tokens <combo_id>                 # Output JSON design tokens
  python3 query_colors.py scss <combo_id>                   # Output SCSS variables
  python3 query_colors.py all [duo|trio|quad]               # List all palettes
  python3 query_colors.py stats                             # Dataset statistics
  python3 query_colors.py preview <combo_ids|mood|all>      # Open visual HTML preview in browser
"""

import json
import sys
import os
import math
import random
import re
import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COLORS_FILE = os.path.join(SCRIPT_DIR, "data", "colors_enhanced.json")
COMBOS_FILE = os.path.join(SCRIPT_DIR, "data", "combinations.json")
COLORS_BASIC = os.path.join(SCRIPT_DIR, "data", "colors.json")


def load_data():
    if os.path.exists(COLORS_FILE):
        with open(COLORS_FILE) as f:
            colors = json.load(f)["colors"]
    else:
        with open(COLORS_BASIC) as f:
            colors = json.load(f)["colors"]

    if os.path.exists(COMBOS_FILE):
        with open(COMBOS_FILE) as f:
            combos = {c["id"]: c for c in json.load(f)["combinations"]}
    else:
        combos = {}
        for c in colors:
            for cid in c["combinations"]:
                if cid not in combos:
                    combos[cid] = {"id": cid, "colors": [], "hex_codes": []}
                combos[cid]["colors"].append(
                    {"index": c["index"], "name": c["name"], "hex": c["hex"]}
                )
                combos[cid]["hex_codes"].append(c["hex"])
    return colors, combos


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb_to_lab(r, g, b):
    rl, gl, bl = srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b)
    x = 0.4124564 * rl + 0.3575761 * gl + 0.1804375 * bl
    y = 0.2126729 * rl + 0.7151522 * gl + 0.0721750 * bl
    z = 0.0193339 * rl + 0.1191920 * gl + 0.9503041 * bl
    xd = 1.0478112 * x + 0.0228866 * y - 0.0501270 * z
    yd = 0.0295424 * x + 0.9904844 * y - 0.0170491 * z
    zd = -0.0092345 * x + 0.0150436 * y + 0.7521316 * z
    XN, YN, ZN = 0.96422, 1.0, 0.82521

    def f(t):
        return t ** (1 / 3) if t > (6 / 29) ** 3 else t / (3 * (6 / 29) ** 2) + 4 / 29

    fx, fy, fz = f(xd / XN), f(yd / YN), f(zd / ZN)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e(lab1, lab2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))


def hex_to_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    return [int(h[i : i + 2], 16) for i in (0, 2, 4)]


def swatch(hx):
    r, g, b = hex_to_rgb(hx)
    return f"\033[48;2;{r};{g};{b}m    \033[0m"


def format_color(c, lab=False):
    s = f"  {swatch(c['hex'])} [{c['index']:>3}] {c['name']:<30} {c['hex']}  RGB({c['rgb_array'][0]:>3},{c['rgb_array'][1]:>3},{c['rgb_array'][2]:>3})"
    if lab and "lab" in c:
        L, a, b = c["lab"]
        s += f"  LAB({L:>6.1f},{a:>6.1f},{b:>6.1f})"
    return s


def format_palette(combo, colors_db):
    cid = combo["id"]
    ctype = combo.get("type", "duo" if cid <= 120 else "trio" if cid <= 240 else "quad")
    lines = [
        f"\n{'=' * 70}",
        f"  Combination #{cid}  |  {ctype}  |  {len(combo['colors'])} colors",
        f"{'=' * 70}",
    ]
    for cc in combo["colors"]:
        full = next((c for c in colors_db if c["index"] == cc["index"]), None)
        lines.append(
            format_color(full)
            if full
            else f"  [{cc['index']:>3}] {cc['name']:<30} {cc['hex']}"
        )
    lines.append(f"\n  Hex: {' '.join(cc['hex'] for cc in combo['colors'])}")
    if "contrast" in combo and combo["contrast"].get("pairs"):
        ct = combo["contrast"]
        lines.append(f"\n  Contrast:")
        icons = {"AAA": "✅", "AA": "✅", "AA-large": "⚠️ ", "fail": "❌"}
        for p in ct["pairs"]:
            lines.append(
                f"    {icons.get(p['grade'], '')} {p['colors'][0]} ↔ {p['colors'][1]}: {p['ratio']}:1 ({p['grade']})"
            )
        if ct.get("all_wcag_aa"):
            lines.append(f"  ✅ All pairs WCAG AA")
        elif ct.get("all_wcag_aa_large"):
            lines.append(f"  ⚠️  WCAG AA large text only")
    if combo.get("palette_temperature"):
        lines.append(f"  Temperature: {combo['palette_temperature']}")
    if combo.get("colorblind_safe") == False:
        lines.append(f"  ⚠️  Possible colorblind issues")
    if "curated" in combo:
        cur = combo["curated"]
        lines.append(f"\n  💡 {cur['context']}")
        lines.append(
            f"     Mood: {', '.join(cur['mood'])}  |  Best for: {', '.join(cur['domains'])}"
        )
    return "\n".join(lines)


# === Commands ===


def cmd_palette(args, colors, combos):
    cid = int(args[0])
    print(
        format_palette(combos[cid], colors)
        if cid in combos
        else f"Combination #{cid} not found (1-348)"
    )


def cmd_search(args, colors, combos):
    term = " ".join(args).lower()
    matches = [c for c in colors if term in c["name"].lower()]
    if not matches:
        print(f"No colors matching '{term}'")
        return
    print(f"\n{len(matches)} color(s) matching '{term}':\n")
    for c in matches:
        print(format_color(c, lab=True))
        print(
            f"         {c.get('temperature', '?')} | {c.get('lightness_class', '?')} | {c.get('saturation_class', '?')} | {c['use_count']} combos: {c['combinations']}"
        )


def cmd_match(args, colors, combos):
    target_hex = args[0]
    top_n = int(args[args.index("--top") + 1]) if "--top" in args else 5
    target_lab = rgb_to_lab(*hex_to_rgb(target_hex))
    dists = sorted(
        [
            (delta_e(target_lab, c.get("lab", list(rgb_to_lab(*c["rgb_array"])))), c)
            for c in colors
        ],
        key=lambda x: x[0],
    )
    print(f"\nClosest Wada colors to {target_hex} (perceptual ΔE*76):\n")
    for d, c in dists[:top_n]:
        print(f"  {format_color(c)}  (ΔE = {d:.1f})")
    best = dists[0][1]
    print(f"\nPalettes containing '{best['name']}':")
    for cid in best["combinations"][:5]:
        if cid in combos:
            print(format_palette(combos[cid], colors))
    if len(best["combinations"]) > 5:
        print(f"\n  ... and {len(best['combinations']) - 5} more")


def cmd_random(args, colors, combos):
    ctype = args[0] if args else None
    pool = {
        k: v
        for k, v in combos.items()
        if not ctype
        or v.get("type") == ctype
        or (ctype == "duo" and 1 <= k <= 120)
        or (ctype == "trio" and 121 <= k <= 240)
        or (ctype == "quad" and 241 <= k <= 348)
    }
    cid = random.choice(list(pool.keys()))
    print(format_palette(pool[cid], colors))


MOOD_MAP = {
    "warm": [
        "red",
        "orange",
        "yellow",
        "cinnamon",
        "sienna",
        "coral",
        "rufous",
        "golden",
        "peach",
    ],
    "cool": [
        "blue",
        "green",
        "turquoise",
        "teal",
        "cerulian",
        "glaucous",
        "nile",
        "cobalt",
        "olympic",
    ],
    "earthy": [
        "brown",
        "olive",
        "sienna",
        "umber",
        "khaki",
        "sepia",
        "ochre",
        "raw",
        "sudan",
        "citrine",
        "maple",
        "ecru",
    ],
    "elegant": [
        "purple",
        "violet",
        "carmine",
        "lake",
        "vandyke",
        "pansy",
        "rose",
        "lilac",
        "mauve",
    ],
    "soft": [
        "pink",
        "lavender",
        "pale",
        "light",
        "buff",
        "cream",
        "cameo",
        "fawn",
        "seashell",
    ],
    "bold": [
        "spectrum",
        "scarlet",
        "red",
        "orange",
        "peach",
        "jasper",
        "grenadine",
        "coral",
    ],
    "natural": [
        "green",
        "olive",
        "citrine",
        "rainette",
        "pistachio",
        "andover",
        "artemesia",
        "lincoln",
        "oil",
    ],
    "dramatic": [
        "black",
        "deep",
        "dark",
        "vandyke",
        "burnt",
        "indigo",
        "slate",
        "pansy",
    ],
    "fresh": [
        "green",
        "turquoise",
        "nile",
        "calamine",
        "venice",
        "cobalt",
        "mint",
        "lemon",
        "benzol",
    ],
    "autumn": [
        "sienna",
        "orange",
        "rufous",
        "brown",
        "ocher",
        "rust",
        "ochre",
        "brick",
        "hay",
        "burnt",
    ],
    "spring": [
        "green",
        "yellow",
        "pink",
        "lemon",
        "turquoise",
        "fresh",
        "cobalt",
        "pistachio",
    ],
    "summer": [
        "blue",
        "turquoise",
        "sea",
        "cerulian",
        "olympic",
        "calamine",
        "nile",
        "coral",
    ],
    "winter": [
        "blue",
        "violet",
        "slate",
        "gray",
        "indigo",
        "deep",
        "dark",
        "tyrian",
        "plumbeous",
    ],
    "minimal": ["white", "black", "gray", "neutral", "slate", "mineral", "warm gray"],
    "vintage": [
        "buff",
        "ecru",
        "ocher",
        "sienna",
        "fawn",
        "isabella",
        "drab",
        "cameo",
        "maple",
    ],
    "tropical": [
        "coral",
        "turquoise",
        "orange",
        "green",
        "pink",
        "lemon",
        "sea",
        "grenadine",
    ],
    "luxurious": [
        "violet",
        "purple",
        "indigo",
        "carmine",
        "golden",
        "deep",
        "pansy",
        "cotinga",
    ],
}


def cmd_mood(args, colors, combos):
    kw = " ".join(args).lower()
    terms = MOOD_MAP.get(kw)
    if not terms:
        matching = set()
        for c in colors:
            if kw in c["name"].lower():
                matching.update(c["combinations"])
        if not matching:
            print(f"No palettes for '{kw}'. Try: {', '.join(sorted(MOOD_MAP.keys()))}")
            return
    else:
        matching = set()
        for c in colors:
            if any(t in c["name"].lower() for t in terms):
                matching.update(c["combinations"])
    curated = [cid for cid in matching if cid in combos and "curated" in combos[cid]]
    rest = [cid for cid in matching if cid not in curated]
    sample = curated[:3] + random.sample(
        rest, min(max(0, 5 - len(curated[:3])), len(rest))
    )
    print(f"\n{len(matching)} palettes match '{kw}'. Showing {len(sample)}:\n")
    for cid in sorted(sample):
        if cid in combos:
            print(format_palette(combos[cid], colors))


def cmd_popular(args, colors, combos):
    n = int(args[0]) if args else 10
    for c in sorted(colors, key=lambda c: c["use_count"], reverse=True)[:n]:
        print(
            f"  {format_color(c)}  ({c['use_count']} combos, {c.get('temperature', '?')})"
        )


def cmd_accessible(args, colors, combos):
    ctype = args[0] if args else None
    pool = [
        c
        for c in combos.values()
        if c.get("contrast", {}).get("all_wcag_aa")
        and c.get("color_count", 0) >= 2
        and (not ctype or c.get("type") == ctype)
    ]
    print(f"\n{len(pool)} WCAG AA palettes{f' ({ctype})' if ctype else ''}:\n")
    for c in random.sample(pool, min(5, len(pool))) if len(pool) > 5 else pool:
        print(format_palette(c, colors))


def cmd_colorblind(args, colors, combos):
    ctype = args[0] if args else None
    pool = [
        c
        for c in combos.values()
        if c.get("colorblind_safe", True)
        and c.get("contrast", {}).get("all_wcag_aa_large")
        and (not ctype or c.get("type") == ctype)
    ]
    print(
        f"\n{len(pool)} colorblind-safe + WCAG AA-large palettes{f' ({ctype})' if ctype else ''}:\n"
    )
    for c in random.sample(pool, min(5, len(pool))) if len(pool) > 5 else pool:
        print(format_palette(c, colors))


def cmd_curated(args, colors, combos):
    domain = args[0] if args else None
    pool = [
        c
        for c in sorted(combos.values(), key=lambda x: x["id"])
        if "curated" in c and (not domain or domain in c["curated"].get("domains", []))
    ]
    print(f"\n{len(pool)} curated palettes{f' for {domain}' if domain else ''}:\n")
    for c in pool:
        print(format_palette(c, colors))


def cmd_for_project(args, colors, combos):
    path = args[0] if args else "."
    found = set()
    for ext in [
        "*.css",
        "*.scss",
        "*.tsx",
        "*.jsx",
        "*.ts",
        "*.js",
        "*.html",
        "*.vue",
        "*.svelte",
        "*.json",
        "tailwind.config.*",
    ]:
        for fp in glob.glob(os.path.join(path, "**", ext), recursive=True):
            if "node_modules" in fp or ".git" in fp:
                continue
            try:
                with open(fp, "r", errors="ignore") as f:
                    for m in re.findall(r"#([0-9a-fA-F]{6})\b", f.read()):
                        found.add(f"#{m.lower()}")
            except:
                pass
    found -= {"#000000", "#ffffff", "#333333", "#666666", "#999999", "#cccccc"}
    if not found:
        print(f"No custom colors found in {path}")
        return
    print(f"\nFound {len(found)} colors. Matching to Wada:\n")
    matched = set()
    for hx in sorted(found)[:12]:
        lab = rgb_to_lab(*hex_to_rgb(hx))
        dists = sorted(
            [
                (delta_e(lab, c.get("lab", list(rgb_to_lab(*c["rgb_array"])))), c)
                for c in colors
            ],
            key=lambda x: x[0],
        )
        best_d, best_c = dists[0]
        if best_d < 35:
            print(
                f"  {swatch(hx)} {hx} → {best_c['name']} ({best_c['hex']}) ΔE={best_d:.1f}"
            )
            matched.update(best_c["combinations"])
    if matched:
        scores = {}
        for cid in matched:
            scores[cid] = scores.get(cid, 0) + 1
        print(f"\nSuggested palettes:")
        for cid, _ in sorted(scores.items(), key=lambda x: -x[1])[:5]:
            if cid in combos:
                print(format_palette(combos[cid], colors))


def cmd_css(args, colors, combos):
    cid = int(args[0])
    prefix = args[args.index("--prefix") + 1] if "--prefix" in args else "wada"
    if cid not in combos:
        print(f"Not found")
        return
    combo = combos[cid]
    roles = ["primary", "secondary", "accent", "highlight"]
    print(f"/* Sanzo Wada — Combination #{cid} ({combo.get('type', '?')}) */")
    if "curated" in combo:
        print(f"/* {combo['curated']['context']} */")
    print(":root {")
    for i, cc in enumerate(combo["colors"]):
        r = roles[i] if i < len(roles) else f"color-{i + 1}"
        print(f"  --{prefix}-{r}: {cc['hex']};  /* {cc['name']} */")
    print("}\n")
    for i, cc in enumerate(combo["colors"]):
        r = roles[i] if i < len(roles) else f"color-{i + 1}"
        print(f".bg-{prefix}-{r} {{ background-color: var(--{prefix}-{r}); }}")
        print(f".text-{prefix}-{r} {{ color: var(--{prefix}-{r}); }}")


def cmd_tailwind(args, colors, combos):
    cid = int(args[0])
    if cid not in combos:
        print(f"Not found")
        return
    combo = combos[cid]
    roles = ["primary", "secondary", "accent", "highlight"]
    print(f"// Sanzo Wada — Combination #{cid} ({combo.get('type', '?')})")
    if "curated" in combo:
        print(f"// {combo['curated']['context']}")
    print("module.exports = {\n  theme: {\n    extend: {\n      colors: {")
    for i, cc in enumerate(combo["colors"]):
        r = roles[i] if i < len(roles) else f"color{i + 1}"
        comma = "," if i < len(combo["colors"]) - 1 else ""
        print(f"        '{r}': '{cc['hex']}'{comma}  // {cc['name']}")
    print("      }\n    }\n  }\n}")


def cmd_tokens(args, colors, combos):
    cid = int(args[0])
    if cid not in combos:
        print(f"Not found")
        return
    combo = combos[cid]
    roles = ["primary", "secondary", "accent", "highlight"]
    tokens = {"color": {}}
    for i, cc in enumerate(combo["colors"]):
        r = roles[i] if i < len(roles) else f"color-{i + 1}"
        tokens["color"][r] = {
            "value": cc["hex"],
            "type": "color",
            "description": cc["name"],
        }
    tokens["_meta"] = {
        "source": f"Sanzo Wada #{cid}",
        "type": combo.get("type", "?"),
        "wcag_aa": combo.get("contrast", {}).get("all_wcag_aa", False),
    }
    print(json.dumps(tokens, indent=2))


def cmd_scss(args, colors, combos):
    cid = int(args[0])
    if cid not in combos:
        print(f"Not found")
        return
    combo = combos[cid]
    roles = ["primary", "secondary", "accent", "highlight"]
    print(f"// Sanzo Wada — Combination #{cid}")
    for i, cc in enumerate(combo["colors"]):
        r = roles[i] if i < len(roles) else f"color-{i + 1}"
        print(f"$wada-{r}: {cc['hex']};  // {cc['name']}")
    print(f"\n$wada-palette: (")
    for i, cc in enumerate(combo["colors"]):
        r = roles[i] if i < len(roles) else f"color-{i + 1}"
        print(f"  '{r}': {cc['hex']}{',' if i < len(combo['colors']) - 1 else ''}")
    print(");")


def cmd_all(args, colors, combos):
    ctype = args[0] if args else None
    pool = {
        k: v
        for k, v in combos.items()
        if not ctype
        or v.get("type") == ctype
        or (ctype == "duo" and 1 <= k <= 120)
        or (ctype == "trio" and 121 <= k <= 240)
        or (ctype == "quad" and 241 <= k <= 348)
    }
    print(f"\n{ctype.title() if ctype else 'All'} palettes ({len(pool)}):\n")
    for cid in sorted(pool.keys()):
        c = pool[cid]
        hexes = " ".join(cc["hex"] for cc in c["colors"])
        names = ", ".join(cc["name"] for cc in c["colors"])
        w = "✅" if c.get("contrast", {}).get("all_wcag_aa") else "  "
        cu = "💡" if "curated" in c else "  "
        print(f"  #{cid:>3}  {hexes:<50} {w}{cu} {names}")


def cmd_stats(args, colors, combos):
    t = len(combos)
    d = len(
        [c for c in combos.values() if c.get("type") == "duo" or 1 <= c["id"] <= 120]
    )
    tr = len(
        [c for c in combos.values() if c.get("type") == "trio" or 121 <= c["id"] <= 240]
    )
    q = len(
        [c for c in combos.values() if c.get("type") == "quad" or 241 <= c["id"] <= 348]
    )
    aa = len([c for c in combos.values() if c.get("contrast", {}).get("all_wcag_aa")])
    al = len(
        [c for c in combos.values() if c.get("contrast", {}).get("all_wcag_aa_large")]
    )
    cb = len([c for c in combos.values() if c.get("colorblind_safe")])
    cu = len([c for c in combos.values() if "curated" in c])
    print(f"\n  Sanzo Wada — A Dictionary of Color Combinations")
    print(f"  {'─' * 45}")
    print(f"  Colors: {len(colors)}  |  Combinations: {t}")
    print(f"  Duos: {d}  |  Trios: {tr}  |  Quads: {q}")
    print(f"  WCAG AA: {aa}  |  AA-large: {al}  |  Colorblind-safe: {cb}")
    print(f"  Curated with design context: {cu}")


def _generate_preview_html(palettes, colors_db, title="Sanzo Wada — Color Preview"):
    """Generate a self-contained HTML page for visually previewing palettes"""
    cards_html = []
    for combo in palettes:
        cid = combo["id"]
        ctype = combo.get(
            "type", "duo" if cid <= 120 else "trio" if cid <= 240 else "quad"
        )

        # Color swatches
        swatches = ""
        color_labels = ""
        for cc in combo["colors"]:
            swatches += f'<div class="swatch" style="background:{cc["hex"]}" title="{cc["name"]} {cc["hex"]}"></div>\n'
            color_labels += f'<div class="color-label"><span class="dot" style="background:{cc["hex"]}"></span>{cc["name"]}<code>{cc["hex"]}</code></div>\n'

        # Badges
        badges = f'<span class="badge type">{ctype}</span>'
        if combo.get("contrast", {}).get("all_wcag_aa"):
            badges += '<span class="badge aa">AA ✓</span>'
        elif combo.get("contrast", {}).get("all_wcag_aa_large"):
            badges += '<span class="badge aa-lg">AA-lg</span>'
        if combo.get("colorblind_safe") == False:
            badges += '<span class="badge cb-warn">CB ⚠</span>'
        if "curated" in combo:
            badges += '<span class="badge curated">★</span>'

        # Curated note
        note = ""
        if "curated" in combo:
            cur = combo["curated"]
            note = f'<div class="note">{cur["context"]}<br><small>{", ".join(cur.get("mood", []))} · {", ".join(cur.get("domains", []))}</small></div>'

        # Contrast details
        contrast_html = ""
        pairs = combo.get("contrast", {}).get("pairs", [])
        if pairs:
            contrast_html = '<div class="contrast">'
            for p in pairs:
                icon = {"AAA": "✅", "AA": "✅", "AA-large": "⚠️", "fail": "❌"}.get(
                    p["grade"], ""
                )
                contrast_html += f'<div class="cpair">{icon} {p["ratio"]}:1 <small>{p["grade"]}</small></div>'
            contrast_html += "</div>"

        cards_html.append(f"""
        <div class="card">
            <div class="card-header">
                <span class="combo-id">#{cid}</span>
                {badges}
            </div>
            <div class="swatches">{swatches}</div>
            <div class="color-labels">{color_labels}</div>
            {contrast_html}
            {note}
        </div>""")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
         background: #f5f5f0; color: #2a2a2a; padding: 2rem; }}
  h1 {{ font-size: 1.6rem; font-weight: 600; margin-bottom: 0.3rem; }}
  .subtitle {{ color: #777; font-size: 0.85rem; margin-bottom: 2rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.5rem; }}
  .card {{ background: #fff; border-radius: 12px; padding: 1.2rem; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
           transition: box-shadow 0.2s; }}
  .card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,0.1); }}
  .card-header {{ display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.8rem; flex-wrap: wrap; }}
  .combo-id {{ font-weight: 700; font-size: 1.1rem; color: #333; }}
  .badge {{ font-size: 0.65rem; padding: 2px 7px; border-radius: 9999px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; }}
  .badge.type {{ background: #e8e8e8; color: #555; }}
  .badge.aa {{ background: #d4edda; color: #155724; }}
  .badge.aa-lg {{ background: #fff3cd; color: #856404; }}
  .badge.cb-warn {{ background: #f8d7da; color: #721c24; }}
  .badge.curated {{ background: #e8daef; color: #6c3483; }}
  .swatches {{ display: flex; border-radius: 8px; overflow: hidden; height: 80px; margin-bottom: 0.8rem; }}
  .swatch {{ flex: 1; cursor: pointer; position: relative; transition: flex 0.2s; }}
  .swatch:hover {{ flex: 1.5; }}
  .swatch::after {{ content: attr(title); position: absolute; bottom: 4px; left: 50%; transform: translateX(-50%);
                    font-size: 0.6rem; color: #fff; text-shadow: 0 1px 3px rgba(0,0,0,0.7);
                    opacity: 0; transition: opacity 0.2s; white-space: nowrap; pointer-events: none; }}
  .swatch:hover::after {{ opacity: 1; }}
  .color-labels {{ display: flex; flex-direction: column; gap: 0.25rem; margin-bottom: 0.6rem; }}
  .color-label {{ display: flex; align-items: center; gap: 0.4rem; font-size: 0.78rem; }}
  .color-label code {{ color: #888; font-size: 0.7rem; margin-left: auto; }}
  .dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; border: 1px solid rgba(0,0,0,0.1); }}
  .contrast {{ display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; }}
  .cpair {{ font-size: 0.7rem; color: #666; }}
  .note {{ font-size: 0.78rem; color: #555; background: #fafaf5; padding: 0.6rem 0.8rem;
           border-radius: 6px; border-left: 3px solid #c9b458; margin-top: 0.4rem; line-height: 1.4; }}
  .note small {{ color: #999; }}
  .filter-bar {{ display: flex; gap: 0.6rem; margin-bottom: 1.5rem; flex-wrap: wrap; }}
  .filter-btn {{ padding: 6px 14px; border-radius: 20px; border: 1px solid #ddd; background: #fff;
                 font-size: 0.8rem; cursor: pointer; transition: all 0.15s; }}
  .filter-btn:hover {{ border-color: #999; }}
  .filter-btn.active {{ background: #333; color: #fff; border-color: #333; }}
  .count {{ color: #999; font-size: 0.85rem; margin-bottom: 1rem; }}
  @media (max-width: 600px) {{ .grid {{ grid-template-columns: 1fr; }} body {{ padding: 1rem; }} }}
</style>
</head>
<body>
<h1>🎨 {title}</h1>
<p class="subtitle">Color combinations from "A Dictionary of Color Combinations" by Sanzo Wada (Seigensha, 2010)</p>
<div class="filter-bar">
  <button class="filter-btn active" onclick="filterCards('all')">All</button>
  <button class="filter-btn" onclick="filterCards('duo')">Duos</button>
  <button class="filter-btn" onclick="filterCards('trio')">Trios</button>
  <button class="filter-btn" onclick="filterCards('quad')">Quads</button>
  <button class="filter-btn" onclick="filterCards('aa')">WCAG AA ✓</button>
  <button class="filter-btn" onclick="filterCards('curated')">★ Curated</button>
</div>
<p class="count"><span id="shown">{len(palettes)}</span> palettes</p>
<div class="grid" id="grid">
{"".join(cards_html)}
</div>
<script>
function filterCards(type) {{
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  let shown = 0;
  document.querySelectorAll('.card').forEach(card => {{
    const badges = card.querySelector('.card-header').textContent;
    let show = true;
    if (type === 'duo') show = badges.includes('duo');
    else if (type === 'trio') show = badges.includes('trio');
    else if (type === 'quad') show = badges.includes('quad');
    else if (type === 'aa') show = badges.includes('AA ✓');
    else if (type === 'curated') show = badges.includes('★');
    card.style.display = show ? '' : 'none';
    if (show) shown++;
  }});
  document.getElementById('shown').textContent = shown;
}}
document.querySelectorAll('.swatch').forEach(s => {{
  s.addEventListener('click', () => {{
    const hex = s.title.split(' ').pop();
    navigator.clipboard.writeText(hex).then(() => {{
      const orig = s.style.outline;
      s.style.outline = '3px solid #333';
      setTimeout(() => s.style.outline = orig, 400);
    }});
  }});
}});
</script>
</body>
</html>"""


def cmd_preview(args, colors, combos):
    """Generate an HTML preview and open it in the browser"""
    import subprocess, tempfile

    if not args or args[0] == "all":
        palettes = sorted(combos.values(), key=lambda c: c["id"])
        title = "Sanzo Wada — All 348 Combinations"
    elif args[0] == "curated":
        palettes = [
            c for c in sorted(combos.values(), key=lambda c: c["id"]) if "curated" in c
        ]
        title = "Sanzo Wada — Curated Palettes"
    elif args[0] == "accessible":
        palettes = [
            c
            for c in sorted(combos.values(), key=lambda c: c["id"])
            if c.get("contrast", {}).get("all_wcag_aa") and c.get("color_count", 0) >= 2
        ]
        title = "Sanzo Wada — WCAG AA Accessible Palettes"
    elif args[0] in MOOD_MAP:
        # Collect all matching combos for this mood
        terms = MOOD_MAP[args[0]]
        matching = set()
        for c in colors:
            if any(t in c["name"].lower() for t in terms):
                matching.update(c["combinations"])
        palettes = [combos[cid] for cid in sorted(matching) if cid in combos]
        title = f"Sanzo Wada — {args[0].title()} Palettes"
    else:
        # Treat as comma-separated combo IDs
        try:
            ids = [int(x.strip()) for x in " ".join(args).replace(",", " ").split()]
            palettes = [combos[cid] for cid in ids if cid in combos]
            title = f"Sanzo Wada — Combinations {', '.join(f'#{i}' for i in ids)}"
        except ValueError:
            print(f"Usage: preview <all|curated|accessible|mood_keyword|combo_id,...>")
            return

    if not palettes:
        print("No palettes to preview.")
        return

    html = _generate_preview_html(palettes, colors, title)

    # Write to a temp file and open
    out_path = os.path.join(tempfile.gettempdir(), "sanzo-wada-preview.html")
    with open(out_path, "w") as f:
        f.write(html)

    print(f"Preview saved to: {out_path}")
    print(f"Showing {len(palettes)} palettes")

    # Try to open in browser
    import platform

    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["open", out_path], check=True)
        elif system == "Linux":
            subprocess.run(["xdg-open", out_path], check=True)
        elif system == "Windows":
            os.startfile(out_path)
        else:
            print(f"Open {out_path} in your browser to view.")
    except Exception:
        print(f"Could not auto-open. Open {out_path} in your browser.")


COMMANDS = {
    "palette": cmd_palette,
    "search": cmd_search,
    "match": cmd_match,
    "random": cmd_random,
    "mood": cmd_mood,
    "popular": cmd_popular,
    "accessible": cmd_accessible,
    "colorblind": cmd_colorblind,
    "curated": cmd_curated,
    "for-project": cmd_for_project,
    "css": cmd_css,
    "tailwind": cmd_tailwind,
    "tokens": cmd_tokens,
    "scss": cmd_scss,
    "all": cmd_all,
    "stats": cmd_stats,
    "preview": cmd_preview,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(0)
    colors, combos = load_data()
    COMMANDS[sys.argv[1]](sys.argv[2:], colors, combos)
