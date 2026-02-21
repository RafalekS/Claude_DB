---
name: web-asset-generator
description: Generate favicons, app icons, and social media images from logos, text, or emojis. Use when user mentions favicon, icon, Open Graph, PWA icons, or social media images.
allowed-tools: Bash, Read, Write, Glob
---

# Web Asset Generator

Generate professional favicons, app icons, and social media images from logos, text, or emojis with integrated validation and framework detection.

## Features

- **Browser Favicons**: Multiple sizes (16×16, 32×32, 96×96, favicon.ico)
- **PWA Icons**: App icons (180×180, 192×192, 512×512) with manifest.json
- **Social Media Images**: Open Graph images for Facebook, Twitter, LinkedIn (1200×630, 1200×675)
- **Framework Detection**: Auto-detects Next.js, Vite, React, etc.
- **Validation**: Verifies generated assets meet requirements

## Prerequisites

- Python 3.8+
- Pillow library: `pip install pillow`
- Optional: emoji support via `pip install emoji`

## Usage

Invoke this skill when the user asks to:
- Create or generate favicons
- Generate app icons or PWA icons
- Create Open Graph / social media images
- Set up web assets from a logo or emoji

## Scripts

- `generate_favicons.py` - Favicon creation from emojis or images
- `generate_og_images.py` - Social media image generation
- `emoji_utils.py` - Emoji selection and processing
- `check_dependencies.py` - Validation tool
- `validators.py` - File and accessibility verification

## Example Workflow

1. Detect project framework (Next.js, Vite, etc.)
2. Ask user for source (logo file, text, or emoji)
3. Generate appropriate assets for the framework
4. Place files in correct locations
5. Update manifest.json if needed
6. Validate generated assets

## Source

Clone from https://github.com/alonw0/web-asset-generator
