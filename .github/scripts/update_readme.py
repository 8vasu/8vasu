#!/usr/bin/env python3
"""
update_readme.py
Fetches repo description and languages from GitHub API and updates README.md.
Repo list is read from repos.json.
"""

import json
import os
import re
import requests

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
USERNAME = "8vasu"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def fetch_repo(repo_name):
    r = requests.get(f"https://api.github.com/repos/{USERNAME}/{repo_name}", headers=HEADERS, timeout=10)
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
    languages = " · ".join(f"**{l}**" for l in fetch_languages(data["languages_url"]))
    lines = [f"[**{name}**]({url})"]
    if description:
        lines.append(f"_{description}_")
    if languages:
        lines.append(languages)
    return "\\\n".join(lines)


def build_section(repos):
    cards = []
    for repo_name in repos:
        try:
            cards.append(render_repo_card(fetch_repo(repo_name)))
        except Exception as e:
            print(f"Warning: could not fetch {repo_name}: {e}")
            cards.append(f"⬡ [{repo_name}](https://github.com/{USERNAME}/{repo_name})")
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