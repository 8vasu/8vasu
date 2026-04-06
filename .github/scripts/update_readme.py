#!/usr/bin/env python3
"""
update_readme.py
Fetches repo description and languages from GitHub API and updates README.md.
Generates SVG badge files for each language encountered.
Repo list is read from repos.json.
"""

import colorsys
import json
import os
import random
import re
import requests
import time

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
USERNAME = "8vasu"
LANGS_DIR = "langs"

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
VB_H = 16
BASELINE = 15

def random_dark_color():
    """Generate a random color with guaranteed contrast on white background."""
    h = random.random()
    s = random.uniform(0.5, 1.0)
    l = random.uniform(0.15, 0.40)
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


def make_svg(text, color):
    vb_w = int(len(text) * CHAR_WIDTH + PAD)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {vb_w} {VB_H}" width="{vb_w}">'
        f'<text x="{PAD_LEFT}" y="{BASELINE}" font-family="monospace" '
        f'font-size="{FONT_SIZE}" font-weight="bold" fill="{color}">{text}</text>'
        f'</svg>'
    )


def ensure_lang(lang):
    svg_path = f"{LANGS_DIR}/{lang}.svg"
    os.makedirs(LANGS_DIR, exist_ok=True)
    with open(svg_path, "w") as f:
        f.write(make_svg(lang, random_dark_color()))
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


def render_repo_card(data):
    name = data["name"]
    description = data.get("description") or ""
    url = data["html_url"]
    lang_names = fetch_languages(data["languages_url"])
    badges = " | ".join(
        f'<img alt="{l}" src="{ensure_lang(l)}?v={int(time.time())}"/>'
        for l in lang_names
    )
    parts = [f"[**{name}**]({url})"]
    if description:
        parts.append(f"_{description}_")
    if badges:
        parts.append(badges)
    return "- " + " ".join(parts)


def build_section(repos):
    cards = []
    for repo_name in repos:
        try:
            cards.append(render_repo_card(fetch_repo(repo_name)))
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
