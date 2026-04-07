#!/usr/bin/env python3
"""
update_readme.py
Fetches repo description and languages from GitHub API and updates README.md.
Generates SVG badge files for each language encountered.
Repo list is read from repos.json.
"""

import json
import os
import random
import re
import requests
import time

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
USERNAME = "8vasu"
LANGS_DIR = "lang_badges"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# SVG dimensions
FONT_SIZE = 12
CHAR_WIDTH = 7.5
PAD = 4
PAD_LEFT = 3
VB_H = 22
BASELINE = 18

# Separator SVG
SEP_W = 6
SEP_H = 18
SEP_COLOR = "#333333"
SEP_PATH = f"{LANGS_DIR}/_sep_.svg"

PALETTE = [
    # Reds
    "#e74c3c", "#c0392b", "#a93226", "#cb4335", "#922b21",
    # Oranges
    "#e67e22", "#d35400", "#ba4a00", "#a04000", "#e64a19",
    # Yellows / Ambers
    "#f39c12", "#d4ac0d", "#9a7d0a", "#f57f17", "#e65100",
    # Purples
    "#8e44ad", "#7d3c98", "#6c3483", "#6a1b9a", "#4a148c",
    "#5b2c6f", "#9b59b6",
    # Pinks / Magentas
    "#e91e63", "#c2185b", "#ad1457", "#880e4f",
    # Blues
    "#2980b9", "#1a5276", "#1f618d", "#0277bd", "#1c3f6e",
    # Greens
    "#27ae60", "#1e8449", "#33691e", "#558b2f",
    # Teals
    "#16a085", "#00695c",
    # Browns
    "#6d4c41", "#4e342e", "#795548", "#5d4037",
    # Dark indigos
    "#1f3a93", "#1a237e", "#283593",
]


def random_color():
    return random.choice(PALETTE)


def make_svg(text, color):
    vb_w = int(len(text) * CHAR_WIDTH + PAD)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {vb_w} {VB_H}" width="{vb_w}">'
        f'<text x="{PAD_LEFT}" y="{BASELINE}" font-family="monospace" '
        f'font-size="{FONT_SIZE}" font-weight="bold" fill="{color}">{text}</text>'
        f'</svg>'
    )


def make_sep_svg():
    cx = SEP_W // 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {SEP_W} {SEP_H}" width="{SEP_W}">'
        f'<line x1="{cx}" y1="0" x2="{cx}" y2="{SEP_H}" '
        f'stroke="{SEP_COLOR}" stroke-width="1"/>'
        f'</svg>'
    )


def ensure_sep():
    os.makedirs(LANGS_DIR, exist_ok=True)
    with open(SEP_PATH, "w") as f:
        f.write(make_sep_svg())
    return SEP_PATH


def ensure_lang(lang):
    svg_path = f"{LANGS_DIR}/{lang}.svg"
    os.makedirs(LANGS_DIR, exist_ok=True)
    with open(svg_path, "w") as f:
        f.write(make_svg(lang, random_color()))
    return svg_path


def fetch_repo(repo_name):
    r = requests.get(
        f"https://api.github.com/repos/{USERNAME}/{repo_name}",
        headers=HEADERS, timeout=10
    )
    r.raise_for_status()
    return r.json()


def fetch_languages(languages_url):
    r = requests.get(languages_url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return list(r.json().keys())


def render_repo_card(data, sep_img):
    name = data["name"]
    description = data.get("description") or ""
    url = data["html_url"]
    lang_names = fetch_languages(data["languages_url"])
    ts = int(time.time())
    badge_imgs = [
        f'<img alt="{l}" src="{ensure_lang(l)}?v={ts}"/>'
        for l in lang_names
    ]
    badges = sep_img.join(badge_imgs)
    parts = [f"[**{name}**]({url})"]
    if description:
        parts.append(f"_{description}_")
    if badges:
        parts.append(badges)
    return "- " + " ".join(parts)


def build_section(repos):
    sep_path = ensure_sep()
    ts = int(time.time())
    sep_img = f'<img alt="|" src="{sep_path}?v={ts}"/>'
    cards = []
    for repo_name in repos:
        try:
            cards.append(render_repo_card(fetch_repo(repo_name), sep_img))
        except Exception as e:
            print(f"Warning: could not fetch {repo_name}: {e}")
            cards.append(f"- [**{repo_name}**](https://github.com/{USERNAME}/{repo_name})")
    return "\n\n".join(cards)


def update_readme(readme_path="README.md", repos_path="repos.json"):
    with open(repos_path) as f:
        repos = json.load(f)
    with open(readme_path) as f:
        content = f.read()
    content = re.sub(
        r"<!-- REPOS_START -->.*?<!-- REPOS_END -->",
        f"<!-- REPOS_START -->\n{build_section(repos)}\n<!-- REPOS_END -->",
        content, flags=re.DOTALL,
    )
    with open(readme_path, "w") as f:
        f.write(content)
    print("README updated.")


if __name__ == "__main__":
    update_readme()