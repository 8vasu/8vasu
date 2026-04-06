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

# Curated palette of visually distinct, readable colors (bg, fg)
PALETTE = [
    ("#3776AB", "#ffffff"),
    ("#555555", "#ffffff"),
    ("#00ADD8", "#ffffff"),
    ("#7F5AB6", "#ffffff"),
    ("#008080", "#ffffff"),
    ("#000080", "#ffffff"),
    ("#E34C26", "#ffffff"),
    ("#B07219", "#ffffff"),
    ("#89E051", "#000000"),
    ("#F7DF1E", "#000000"),
    ("#DEA584", "#000000"),
    ("#427819", "#ffffff"),
    ("#c30b4e", "#ffffff"),
    ("#4F5D95", "#ffffff"),
    ("#2b7489", "#ffffff"),
    ("#701516", "#ffffff"),
    ("#563d7c", "#ffffff"),
    ("#A97BFF", "#000000"),
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
    remaining = [c for c in PALETTE if c[0] not in used]
    if remaining:
        return random.choice(remaining)
    # All palette colors used, pick a random one anyway
    return random.choice(PALETTE)


def make_svg(text, bg, fg):
    width = len(text) * 7 + 12
    height = 18
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
        f'<rect width="{width}" height="{height}" rx="3" fill="{bg}"/>'
        f'<text x="{width // 2}" y="13" font-family="monospace" font-size="11" '
        f'fill="{fg}" text-anchor="middle">{text}</text>'
        f'</svg>'
    )


def ensure_lang(lang, langs):
    if lang not in langs:
        bg, fg = next_color(langs)
        svg_path = f"{LANGS_DIR}/{lang}.svg"
        langs[lang] = {"color": bg, "fg": fg, "svg": svg_path}

    entry = langs[lang]
    svg_path = entry["svg"]
    os.makedirs(LANGS_DIR, exist_ok=True)

    if not os.path.exists(svg_path):
        svg = make_svg(lang, entry["color"], entry["fg"])
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
        f'<img alt="{l}" src="{ensure_lang(l, langs)}" height="18"/>'
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