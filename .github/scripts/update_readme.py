#!/usr/bin/env python3
"""
update_readme.py
Fetches repo description and languages from GitHub API and updates README.md.
Generates SVG badge files for each language encountered.
Repo list is read from repos.json.
Language color/svg registry is stored in langs.json.
"""

import json
import os
import re
import random
import requests

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
USERNAME = "8vasu"
LANGS_DIR = "langs"
LANGS_JSON = "langs.json"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Colors with good contrast on white background
PALETTE = [
    "#3776AB",  # Python blue
    "#555555",  # C gray
    "#00ADD8",  # Go cyan
    "#7F5AB6",  # purple
    "#008080",  # teal
    "#000080",  # navy
    "#E34C26",  # orange-red
    "#B07219",  # dark gold
    "#427819",  # dark green
    "#c30b4e",  # crimson
    "#4F5D95",  # slate blue
    "#2b7489",  # dark cyan
    "#701516",  # dark red
    "#563d7c",  # dark purple
    "#1a1a99",  # dark indigo
    "#006400",  # dark green 2
    "#8B4513",  # saddle brown
    "#4B0082",  # indigo
    "#2F4F4F",  # dark slate gray
    "#800000",  # maroon
    "#556B2F",  # dark olive green
    "#8B008B",  # dark magenta
    "#1C6B48",  # forest green
    "#A0522D",  # sienna
    "#483D8B",  # dark slate blue
    "#8B0000",  # dark red 2
    "#2E8B57",  # sea green
    "#6A5ACD",  # slate blue 2
    "#D2691E",  # chocolate
    "#CD5C5C",  # indian red
    "#20B2AA",  # light sea green
    "#C71585",  # medium violet red
]


def load_langs():
    if os.path.exists(LANGS_JSON):
        with open(LANGS_JSON) as f:
            return json.load(f)
    return {}


def save_langs(langs):
    with open(LANGS_JSON, "w") as f:
        json.dump(langs, f, indent=2)


def next_color(langs):
    used = {v["color"] for v in langs.values()}
    remaining = [c for c in PALETTE if c not in used]
    if remaining:
        return random.choice(remaining)
    return random.choice(PALETTE)


def make_svg(text, color):
    # Approximate width: 7.5px per char, bold font, no background
    width = int(len(text) * 7.5 + 4)
    height = 16
    # vertical-align via dominant-baseline keeps text aligned with surrounding text
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'style="vertical-align: -0.2em;">'
        f'<text x="0" y="13" font-family="monospace" font-size="12" '
        f'font-weight="bold" fill="{color}">{text}</text>'
        f'</svg>'
    )


def ensure_lang(lang, langs):
    if lang not in langs:
        color = next_color(langs)
        svg_path = f"{LANGS_DIR}/{lang}.svg"
        langs[lang] = {"color": color, "svg": svg_path}

    entry = langs[lang]
    svg_path = entry["svg"]
    os.makedirs(LANGS_DIR, exist_ok=True)
    svg = make_svg(lang, entry["color"])
    with open(svg_path, "w") as f:
        f.write(svg)

    return svg_path


def fetch_repo(repo_name):
    r = requests.get(f"https://api.github.com/repos/{USERNAME}/{repo_name}", headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()


def fetch_languages(languages_url):
    r = requests.get(languages_url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return list(r.json().keys())


def render_repo_card(data, langs):
    name = data["name"]
    description = data.get("description") or ""
    url = data["html_url"]
    lang_names = fetch_languages(data["languages_url"])
    badges = " ".join(
        f'<img alt="{l}" src="{ensure_lang(l, langs)}" height="14" style="vertical-align: 0.1em;"/>'
        for l in lang_names
    )
    parts = [f"[**{name}**]({url})"]
    if description:
        parts.append(f"_{description}_")
    if badges:
        parts.append(badges)
    return "- " + " ".join(parts)


def build_section(repos, langs):
    cards = []
    for repo_name in repos:
        try:
            cards.append(render_repo_card(fetch_repo(repo_name), langs))
        except Exception as e:
            print(f"Warning: could not fetch {repo_name}: {e}")
            cards.append(f"- [**{repo_name}**](https://github.com/{USERNAME}/{repo_name})")
    return "\n\n".join(cards)


def update_readme(readme_path="README.md", repos_path="repos.json"):
    with open(repos_path) as f:
        repos = json.load(f)

    langs = load_langs()

    with open(readme_path) as f:
        content = f.read()

    section = build_section(repos, langs)

    content = re.sub(
        r"<!-- REPOS_START -->.*?<!-- REPOS_END -->",
        f"<!-- REPOS_START -->\n{section}\n<!-- REPOS_END -->",
        content, flags=re.DOTALL,
    )

    with open(readme_path, "w") as f:
        f.write(content)

    save_langs(langs)
    print("README updated.")


if __name__ == "__main__":
    update_readme()