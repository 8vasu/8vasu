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

PALETTE = [
    "#3776AB", "#555555", "#00ADD8", "#7F5AB6", "#008080",
    "#000080", "#E34C26", "#B07219", "#427819", "#c30b4e",
    "#4F5D95", "#2b7489", "#701516", "#563d7c", "#1a1a99",
    "#006400", "#8B4513", "#4B0082", "#2F4F4F", "#800000",
    "#556B2F", "#8B008B", "#1C6B48", "#A0522D", "#483D8B",
    "#8B0000", "#2E8B57", "#6A5ACD", "#D2691E", "#CD5C5C",
    "#20B2AA", "#C71585",
]

# SVG dimensions — all sizing decisions live here
FONT_SIZE = 12
CHAR_WIDTH = 7.5
PAD = 4
VB_H = 16
BASELINE = 12
IMG_HEIGHT = 16


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
    return random.choice(remaining) if remaining else random.choice(PALETTE)


def make_svg(text, color):
    vb_w = int(len(text) * CHAR_WIDTH + PAD)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {vb_w} {VB_H}" width="{vb_w}" height="{VB_H}">'
        f'<text x="0" y="{BASELINE}" font-family="monospace" '
        f'font-size="{FONT_SIZE}" font-weight="bold" fill="{color}">{text}</text>'
        f'</svg>'
    )


def ensure_lang(lang, langs):
    if lang not in langs:
        langs[lang] = {"color": next_color(langs), "svg": f"{LANGS_DIR}/{lang}.svg"}
    entry = langs[lang]
    os.makedirs(LANGS_DIR, exist_ok=True)
    with open(entry["svg"], "w") as f:
        f.write(make_svg(lang, entry["color"]))
    return entry["svg"]


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


def render_repo_card(data, langs):
    name = data["name"]
    description = data.get("description") or ""
    url = data["html_url"]
    lang_names = fetch_languages(data["languages_url"])
    badges = " ".join(
        f'<img alt="{l}" src="{ensure_lang(l, langs)}" height="{IMG_HEIGHT}"/>'
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
    content = re.sub(
        r"<!-- REPOS_START -->.*?<!-- REPOS_END -->",
        f"<!-- REPOS_START -->\n{build_section(repos, langs)}\n<!-- REPOS_END -->",
        content, flags=re.DOTALL,
    )
    with open(readme_path, "w") as f:
        f.write(content)
    save_langs(langs)
    print("README updated.")


if __name__ == "__main__":
    update_readme()