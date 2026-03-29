# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0

"""
Generate optimized Social Preview images (1280x640) for Zenzic.
Uses CairoSVG to render theme-aware backgrounds and logos.
"""

import os

import cairosvg


ASSETS_DIR = "docs/assets"
OUTPUT_DIR = "docs/assets"
WIDTH = 1280
HEIGHT = 640

# Theme configurations
THEMES = {
    "dark": {
        "bg": "#0d1117",  # GitHub Dark background
        "logo": "logo-dark.svg",
        "output": "social-preview-dark.png",
    },
    "light": {
        "bg": "#ffffff",  # Pure white
        "logo": "logo-light.svg",
        "output": "social-preview-light.png",
    },
}


def generate_social_preview(name, config):
    logo_path = os.path.join(ASSETS_DIR, config["logo"])
    output_path = os.path.join(OUTPUT_DIR, config["output"])

    # Read logo SVG content
    with open(logo_path) as f:
        logo_svg = f.read()

    # Create a container SVG with the desired dimensions and background
    # We embed the logo SVG inside a <g> and center it.
    # The logo svgs are 640x200. We scale them to fit comfortably.
    container_svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}">
        <rect width="100%" height="100%" fill="{config["bg"]}" />
        <g transform="translate({(WIDTH - 640) // 2}, {(HEIGHT - 200) // 2})">
            {logo_svg}
        </g>
    </svg>
    """

    print(f"Generating {name} social preview: {output_path}...")
    cairosvg.svg2png(bytestring=container_svg.encode("utf-8"), write_to=output_path)
    print(f"Done: {output_path}")


if __name__ == "__main__":
    for name, config in THEMES.items():
        if os.path.exists(os.path.join(ASSETS_DIR, config["logo"])):
            generate_social_preview(name, config)
        else:
            print(f"Warning: {config['logo']} not found, skipping {name} theme.")
