#!/usr/bin/env python3
"""
Build the enhanced Sanzo Wada color dataset:
1. Compute L*a*b* values from RGB (sRGB -> XYZ -> LAB with D50 illuminant)
2. Build combination-level JSON with metadata
3. Pre-compute WCAG contrast ratios for each combination
4. Add curated design context annotations
"""

import json
import math
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "data", "colors.json")
OUTPUT_COLORS = os.path.join(SCRIPT_DIR, "data", "colors_enhanced.json")
OUTPUT_COMBOS = os.path.join(SCRIPT_DIR, "data", "combinations.json")

# === sRGB -> L*a*b* conversion (D50 illuminant) ===

def srgb_to_linear(c):
    c = c / 255.0
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4

def rgb_to_xyz(r, g, b):
    """sRGB to XYZ (D50 adapted via Bradford)"""
    rl = srgb_to_linear(r)
    gl = srgb_to_linear(g)
    bl = srgb_to_linear(b)
    # sRGB to XYZ (D65)
    x = 0.4124564 * rl + 0.3575761 * gl + 0.1804375 * bl
    y = 0.2126729 * rl + 0.7151522 * gl + 0.0721750 * bl
    z = 0.0193339 * rl + 0.1191920 * gl + 0.9503041 * bl
    # Bradford chromatic adaptation D65 -> D50
    xd = 1.0478112 * x + 0.0228866 * y - 0.0501270 * z
    yd = 0.0295424 * x + 0.9904844 * y - 0.0170491 * z
    zd = -0.0092345 * x + 0.0150436 * y + 0.7521316 * z
    return xd, yd, zd

# D50 reference white
XN, YN, ZN = 0.96422, 1.00000, 0.82521

def f_lab(t):
    if t > (6/29)**3:
        return t ** (1/3)
    return t / (3 * (6/29)**2) + 4/29

def xyz_to_lab(x, y, z):
    fx = f_lab(x / XN)
    fy = f_lab(y / YN)
    fz = f_lab(z / ZN)
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    return L, a, b

def rgb_to_lab(r, g, b):
    x, y, z = rgb_to_xyz(r, g, b)
    return xyz_to_lab(x, y, z)

# === WCAG Contrast Ratio ===

def relative_luminance(r, g, b):
    """WCAG 2.1 relative luminance"""
    rs = srgb_to_linear(r)
    gs = srgb_to_linear(g)
    bs = srgb_to_linear(b)
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs

def contrast_ratio(rgb1, rgb2):
    """WCAG contrast ratio between two RGB colors"""
    l1 = relative_luminance(*rgb1)
    l2 = relative_luminance(*rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def wcag_grade(ratio):
    """Return WCAG compliance level"""
    if ratio >= 7.0:
        return "AAA"
    elif ratio >= 4.5:
        return "AA"
    elif ratio >= 3.0:
        return "AA-large"
    else:
        return "fail"

# === Delta E (CIE76) ===

def delta_e_76(lab1, lab2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))

# === Color temperature classification ===

def classify_temperature(r, g, b):
    """Classify a color as warm, cool, or neutral"""
    # Simple heuristic based on red-blue balance
    warmth = (r * 1.0 + g * 0.5) - (b * 1.0 + g * 0.2)
    if warmth > 80:
        return "warm"
    elif warmth < -80:
        return "cool"
    return "neutral"

def classify_lightness(L):
    if L > 75:
        return "light"
    elif L > 45:
        return "mid"
    else:
        return "dark"

def classify_saturation(a_val, b_val):
    chroma = math.sqrt(a_val**2 + b_val**2)
    if chroma > 50:
        return "vivid"
    elif chroma > 25:
        return "moderate"
    else:
        return "muted"

# === Curated design context for top combinations ===

CURATED_COMBOS = {
    1: {"context": "Bold contrast — warm orange against cool teal. Strong for CTAs and hero sections.", "mood": ["energetic", "bold"], "domains": ["web", "branding"]},
    6: {"context": "Grenadine Pink with Deep Indigo — dramatic feminine palette with high contrast.", "mood": ["dramatic", "elegant"], "domains": ["fashion", "branding"]},
    14: {"context": "Spinel Red with Naples Yellow — warm complementary pair with vintage charm.", "mood": ["warm", "vintage"], "domains": ["interior", "print"]},
    18: {"context": "Cameo Pink, Fawn, and Dusky Madder Violet — soft muted trio with depth.", "mood": ["soft", "sophisticated"], "domains": ["fashion", "interior"]},
    22: {"context": "Pure Yellow with Yellow Orange and Deep Lyons Blue — primary triad energy.", "mood": ["bold", "playful"], "domains": ["web", "branding", "packaging"]},
    25: {"context": "Etruscan Red with Nile Blue — warm red cooled by mint. Balanced tension.", "mood": ["balanced", "fresh"], "domains": ["interior", "web"]},
    42: {"context": "Yellow Ocher and Violet — classic complementary with artistic gravitas.", "mood": ["artistic", "bold"], "domains": ["branding", "print", "interior"]},
    44: {"context": "Light Porcelain Green and Olympic Blue — cool analogous, trustworthy.", "mood": ["calm", "professional"], "domains": ["web", "branding", "data-viz"]},
    55: {"context": "White and Old Rose — minimal and refined. Excellent for luxury.", "mood": ["minimal", "elegant"], "domains": ["fashion", "branding", "web"]},
    67: {"context": "Olympic Blue and Dark Tyrian Blue — monochromatic blue depth.", "mood": ["professional", "serious"], "domains": ["web", "branding", "data-viz"]},
    84: {"context": "Seashell Pink and Deep Slate Green — nature-inspired contrast.", "mood": ["natural", "balanced"], "domains": ["interior", "fashion", "web"]},
    99: {"context": "Pale Lemon Yellow and Benzol Green — fresh spring energy.", "mood": ["fresh", "spring"], "domains": ["web", "packaging", "interior"]},
    125: {"context": "Cameo Pink, Fawn, Cerulian Blue, Violet Blue — rich quad with depth.", "mood": ["sophisticated", "artistic"], "domains": ["interior", "fashion", "print"]},
    130: {"context": "Carmine Red, Raw Sienna, Violet — earthy triad with punch.", "mood": ["earthy", "bold"], "domains": ["branding", "packaging", "interior"]},
    141: {"context": "Orange, Yellow Green, Dark Tyrian Blue — high-energy triad.", "mood": ["energetic", "playful"], "domains": ["web", "packaging", "branding"]},
    147: {"context": "Spinel Red, Vandyke Red, Turquoise Green — dramatic with relief.", "mood": ["dramatic", "luxurious"], "domains": ["fashion", "interior", "print"]},
    157: {"context": "Pansy Purple, Olive Ocher, Olympic Blue — unexpected harmony.", "mood": ["artistic", "unconventional"], "domains": ["branding", "fashion", "print"]},
    194: {"context": "Jasper Red, Seashell Pink, Olympic Blue — patriotic warmth.", "mood": ["warm", "confident"], "domains": ["branding", "web"]},
    198: {"context": "Burnt Sienna, Apricot Yellow, Green — natural vitality.", "mood": ["natural", "warm"], "domains": ["interior", "packaging", "web"]},
    232: {"context": "Carmine, Pinkish Cinnamon, Deep Indigo — warm to cold gradient.", "mood": ["dramatic", "sophisticated"], "domains": ["fashion", "branding", "print"]},
    242: {"context": "Eosine Pink, Burnt Sienna, Diamine Green, Black — rich quad.", "mood": ["bold", "artistic"], "domains": ["print", "packaging", "branding"]},
    250: {"context": "Sea Green, Peach Red, Nile Blue, Pyrite Yellow — vibrant quad.", "mood": ["vibrant", "playful"], "domains": ["web", "packaging", "interior"]},
    264: {"context": "Corinthian Pink, Red Orange, Cerulian Blue, Dark Greenish Glaucous — balanced quad.", "mood": ["balanced", "harmonious"], "domains": ["interior", "fashion", "web"]},
    285: {"context": "Light Brown Drab, Peach Red, Turquoise Green, Burnt Sienna — earthy warmth.", "mood": ["earthy", "warm"], "domains": ["interior", "fashion"]},
    293: {"context": "Raw Sienna, Turquoise Green, Artemesia Green, Green — nature palette.", "mood": ["natural", "organic"], "domains": ["interior", "web", "branding"]},
    308: {"context": "Cameo Pink, Fawn, Scarlet, English Red, Cobalt Green — rich 5-color.", "mood": ["rich", "artistic"], "domains": ["fashion", "print"]},
    322: {"context": "Spectrum Red, Brick Red, Blue Violet — deep contrast triad.", "mood": ["dramatic", "powerful"], "domains": ["branding", "packaging"]},
    332: {"context": "Coral Red, Scarlet, Deep Slate Olive, Nile Blue, Dusky Green — complex.", "mood": ["complex", "natural"], "domains": ["interior", "fashion"]},
    340: {"context": "Sea Green, Grenadine Pink, Black, Neutral Gray — modern contrast.", "mood": ["modern", "clean"], "domains": ["web", "branding", "data-viz"]},
    348: {"context": "Cossack Green, Olive Buff, Deep Slate Olive, Cotinga Purple — deep earth.", "mood": ["earthy", "dramatic"], "domains": ["interior", "fashion", "print"]},
}


def main():
    with open(INPUT_FILE) as f:
        data = json.load(f)
    colors = data["colors"]

    # Step 1: Enhance each color with LAB, temperature, lightness, saturation
    for c in colors:
        r, g, b = c["rgb_array"]
        L, a, b_val = rgb_to_lab(r, g, b)
        c["lab"] = [round(L, 2), round(a, 2), round(b_val, 2)]
        c["luminance"] = round(relative_luminance(r, g, b), 4)
        c["temperature"] = classify_temperature(r, g, b)
        c["lightness_class"] = classify_lightness(L)
        c["saturation_class"] = classify_saturation(a, b_val)

    # Step 2: Build combination-level data
    combos_map = {}
    for c in colors:
        for cid in c["combinations"]:
            if cid not in combos_map:
                combos_map[cid] = []
            combos_map[cid].append(c["index"])

    combinations = []
    for cid in sorted(combos_map.keys()):
        color_indices = combos_map[cid]
        palette_colors = [c for c in colors if c["index"] in color_indices]

        # Determine type
        n = len(palette_colors)
        if 1 <= cid <= 120:
            ctype = "duo"
        elif 121 <= cid <= 240:
            ctype = "trio"
        else:
            ctype = "quad"

        # Compute all pairwise contrast ratios
        contrast_pairs = []
        max_contrast = 0
        min_contrast = float('inf')
        all_aa = True
        all_aa_large = True
        for i in range(len(palette_colors)):
            for j in range(i + 1, len(palette_colors)):
                rgb_i = tuple(palette_colors[i]["rgb_array"])
                rgb_j = tuple(palette_colors[j]["rgb_array"])
                ratio = contrast_ratio(rgb_i, rgb_j)
                grade = wcag_grade(ratio)
                contrast_pairs.append({
                    "colors": [palette_colors[i]["name"], palette_colors[j]["name"]],
                    "ratio": round(ratio, 2),
                    "grade": grade
                })
                max_contrast = max(max_contrast, ratio)
                min_contrast = min(min_contrast, ratio)
                if grade == "fail":
                    all_aa_large = False
                    all_aa = False
                elif grade == "AA-large":
                    all_aa = False

        # Classify palette temperature
        temps = [c_item["temperature"] for c_item in palette_colors]
        if all(t == "warm" for t in temps):
            palette_temp = "warm"
        elif all(t == "cool" for t in temps):
            palette_temp = "cool"
        elif "warm" in temps and "cool" in temps:
            palette_temp = "complementary"
        else:
            palette_temp = "neutral"

        # Lightness range
        lums = [c_item["luminance"] for c_item in palette_colors]
        lightness_range = "high-contrast" if max(lums) - min(lums) > 0.4 else "low-contrast"

        # Colorblind safety heuristic
        # Flag if any pair has similar luminance AND both are in red-green range
        colorblind_safe = True
        for i in range(len(palette_colors)):
            for j in range(i + 1, len(palette_colors)):
                ri, gi, bi = palette_colors[i]["rgb_array"]
                rj, gj, bj = palette_colors[j]["rgb_array"]
                # Check if both colors are in the red-green confusion zone
                lum_diff = abs(palette_colors[i]["luminance"] - palette_colors[j]["luminance"])
                # Simple deuteranopia simulation: if R and G channels are similar between colors
                # but they look different to normal vision, flag it
                rg_sim_i = abs(ri - gi)
                rg_sim_j = abs(rj - gj)
                if lum_diff < 0.1:
                    # Low luminance difference — check if both are reddish/greenish
                    if (ri > 100 and gi > 60 and bi < 100) or (gi > 100 and ri > 60 and bi < 100):
                        if (rj > 100 and gj > 60 and bj < 100) or (gj > 100 and rj > 60 and bj < 100):
                            colorblind_safe = False

        combo_entry = {
            "id": cid,
            "type": ctype,
            "color_count": n,
            "colors": [{"index": pc["index"], "name": pc["name"], "hex": pc["hex"]} for pc in palette_colors],
            "hex_codes": [pc["hex"] for pc in palette_colors],
            "contrast": {
                "pairs": contrast_pairs,
                "max_ratio": round(max_contrast, 2),
                "min_ratio": round(min_contrast, 2) if min_contrast != float('inf') else 0,
                "all_wcag_aa": all_aa,
                "all_wcag_aa_large": all_aa_large,
            },
            "palette_temperature": palette_temp,
            "lightness_range": lightness_range,
            "colorblind_safe": colorblind_safe,
        }

        # Add curated context if available
        if cid in CURATED_COMBOS:
            combo_entry["curated"] = CURATED_COMBOS[cid]

        combinations.append(combo_entry)

    # Step 3: Compute statistics
    wcag_aa_combos = [c for c in combinations if c["contrast"]["all_wcag_aa"]]
    wcag_aa_large_combos = [c for c in combinations if c["contrast"]["all_wcag_aa_large"]]
    colorblind_safe_combos = [c for c in combinations if c["colorblind_safe"]]

    stats = {
        "total_colors": len(colors),
        "total_combinations": len(combinations),
        "duos": len([c for c in combinations if c["type"] == "duo"]),
        "trios": len([c for c in combinations if c["type"] == "trio"]),
        "quads": len([c for c in combinations if c["type"] == "quad"]),
        "wcag_aa_count": len(wcag_aa_combos),
        "wcag_aa_large_count": len(wcag_aa_large_combos),
        "colorblind_safe_count": len(colorblind_safe_combos),
        "curated_count": len(CURATED_COMBOS),
    }

    # Save enhanced colors
    with open(OUTPUT_COLORS, "w") as f:
        json.dump({"colors": colors, "stats": stats}, f, indent=2)
    print(f"Saved enhanced colors to {OUTPUT_COLORS}")

    # Save combinations
    with open(OUTPUT_COMBOS, "w") as f:
        json.dump({"combinations": combinations, "stats": stats}, f, indent=2)
    print(f"Saved {len(combinations)} combinations to {OUTPUT_COMBOS}")

    # Print summary
    print(f"\n=== Dataset Summary ===")
    print(f"Colors: {stats['total_colors']}")
    print(f"Combinations: {stats['total_combinations']} (duos: {stats['duos']}, trios: {stats['trios']}, quads: {stats['quads']})")
    print(f"WCAG AA compliant (all pairs): {stats['wcag_aa_count']}")
    print(f"WCAG AA-large compliant (all pairs): {stats['wcag_aa_large_count']}")
    print(f"Colorblind-safe palettes: {stats['colorblind_safe_count']}")
    print(f"Curated with design context: {stats['curated_count']}")

if __name__ == "__main__":
    main()
