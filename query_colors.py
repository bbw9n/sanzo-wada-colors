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
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(0)
    colors, combos = load_data()
    COMMANDS[sys.argv[1]](sys.argv[2:], colors, combos)
