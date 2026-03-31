#!/usr/bin/env python3
"""Build icons.json Iconify pack from SVG files in icons/ folder.

Run this script after adding, removing, or updating SVG icons to regenerate
the icons.json pack used by mermaid-cli for architecture-beta diagrams.

Supports multiple icon naming conventions:
- Azure: {ID}-icon-service-{ServiceName}.svg (18x18)
- Dynamics 365: {CamelCase}_scalable.svg (96x96, prefixed with "dynamics-365-")
- Power Platform: {CamelCase}_scalable.svg (96x96, prefixed with "power-platform-" or as-is)

Usage:
    python3 build-icons.py
"""

import os
import re
import json
import glob

ICONS_DIR = os.path.join(os.path.dirname(__file__), "icons")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "icons.json")

# Category prefixes for icon naming
CATEGORY_PREFIXES = {
    "dynamics-365": "d365",
    "power-platform": "pp",
}


def camel_to_kebab(name):
    """Convert CamelCase to kebab-case: 'BusinessCentral' -> 'business-central'."""
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", name)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s)
    return s.lower()


def parse_svg(svg_content):
    """Extract body, width, and height from SVG content."""
    body_match = re.search(r"<svg[^>]*>(.*)</svg>", svg_content, re.DOTALL)
    if not body_match:
        return None, None, None

    body = body_match.group(1).strip()

    # Extract viewBox or width/height
    vb_match = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg_content)
    if vb_match:
        width = int(vb_match.group(1))
        height = int(vb_match.group(2))
    else:
        w_match = re.search(r'width="(\d+)"', svg_content)
        h_match = re.search(r'height="(\d+)"', svg_content)
        width = int(w_match.group(1)) if w_match else 18
        height = int(h_match.group(1)) if h_match else 18

    return body, width, height


def build_icon_pack():
    icons = {}

    for svg_path in sorted(
        glob.glob(os.path.join(ICONS_DIR, "**", "*.svg"), recursive=True)
    ):
        filename = os.path.basename(svg_path)
        category = os.path.basename(os.path.dirname(svg_path))

        # Pattern 1: Azure icons — {ID}-icon-service-{ServiceName}.svg
        azure_match = re.match(r"\d+-icon-service-(.+)\.svg$", filename)
        # Pattern 2: Scalable icons — {CamelCase}_scalable.svg
        scalable_match = re.match(r"(.+)_scalable\.svg$", filename)

        if azure_match:
            service_name = azure_match.group(1)
            icon_name = service_name.lower()
            icon_name = re.sub(r"\(([^)]+)\)", r"\1", icon_name)
            icon_name = re.sub(r"-+", "-", icon_name).strip("-")
            icon_name = icon_name.replace("-+-", "-and-")
            icon_name = icon_name.strip()
        elif scalable_match:
            raw_name = scalable_match.group(1)
            kebab = camel_to_kebab(raw_name)
            # Add category prefix for disambiguation
            if category == "dynamics-365":
                # Special case: "Dynamics365" is just "dynamics-365"
                if raw_name == "Dynamics365":
                    icon_name = "dynamics-365"
                else:
                    icon_name = f"d365-{kebab}"
            elif category == "power-platform":
                icon_name = f"pp-{kebab}"
            else:
                icon_name = kebab
        else:
            continue

        with open(svg_path, "r") as f:
            svg_content = f.read()

        body, width, height = parse_svg(svg_content)
        if body is None:
            continue

        # Build icon entry
        entry = {"body": body}
        # Only add width/height if different from pack default (18x18)
        if width != 18 or height != 18:
            entry["width"] = width
            entry["height"] = height

        # First occurrence wins (dedup across categories)
        if icon_name not in icons:
            icons[icon_name] = entry

    # Build Iconify pack
    pack = {
        "prefix": "azure",
        "lastModified": int(os.path.getmtime(ICONS_DIR)),
        "icons": dict(sorted(icons.items())),
        "width": 18,
        "height": 18,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(pack, f, separators=(",", ":"))

    # Summary
    default_size = sum(1 for v in icons.values() if "width" not in v)
    custom_size = sum(1 for v in icons.values() if "width" in v)
    print(f"Built {OUTPUT_PATH}: {len(icons)} icons ({default_size} @18x18, {custom_size} @custom size), {os.path.getsize(OUTPUT_PATH)} bytes")


if __name__ == "__main__":
    build_icon_pack()
