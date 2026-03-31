#!/usr/bin/env python3
"""Build icons.json Iconify pack from SVG files in icons/ folder.

Run this script after adding, removing, or updating SVG icons to regenerate
the icons.json pack used by mermaid-cli for architecture-beta diagrams.

Usage:
    python3 build-icons.py
"""

import os
import re
import json
import glob

ICONS_DIR = os.path.join(os.path.dirname(__file__), "icons")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "icons.json")


def build_icon_pack():
    icons = {}

    for svg_path in sorted(
        glob.glob(os.path.join(ICONS_DIR, "**", "*.svg"), recursive=True)
    ):
        filename = os.path.basename(svg_path)

        # Extract service name: {ID}-icon-service-{ServiceName}.svg
        match = re.match(r"\d+-icon-service-(.+)\.svg$", filename)
        if not match:
            continue

        service_name = match.group(1)
        # Convert to kebab-case lowercase
        icon_name = service_name.lower()
        # Remove parentheses content: "(classic)" -> "classic"
        icon_name = re.sub(r"\(([^)]+)\)", r"\1", icon_name)
        # Clean up double/trailing hyphens
        icon_name = re.sub(r"-+", "-", icon_name).strip("-")
        # Replace "+" with "and"
        icon_name = icon_name.replace("-+-", "-and-")
        icon_name = icon_name.strip()

        with open(svg_path, "r") as f:
            svg_content = f.read()

        # Extract SVG body (content between <svg> tags)
        body_match = re.search(r"<svg[^>]*>(.*)</svg>", svg_content, re.DOTALL)
        if not body_match:
            continue

        body = body_match.group(1).strip()

        # First occurrence wins (dedup across categories)
        if icon_name not in icons:
            icons[icon_name] = {"body": body}

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

    print(f"Built {OUTPUT_PATH}: {len(icons)} icons, {os.path.getsize(OUTPUT_PATH)} bytes")


if __name__ == "__main__":
    build_icon_pack()
