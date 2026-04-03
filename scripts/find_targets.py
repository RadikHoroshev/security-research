#!/usr/bin/env python3
"""
Huntr target finder — scrapes bounty list, filters by criteria, outputs JSON.
Usage: python3 find_targets.py [--min-reward 200] [--lang python,nodejs]
Output: /Users/code/project/intel/results/phase1_targets.json
"""
import json, time, sys, re
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

OUT = Path("/Users/code/project/intel/results/phase1_targets.json")
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "text/html,application/xhtml+xml"}

MIN_REWARD = int(sys.argv[sys.argv.index("--min-reward")+1]) if "--min-reward" in sys.argv else 200
LANGS = sys.argv[sys.argv.index("--lang")+1].split(",") if "--lang" in sys.argv else ["python","nodejs","javascript"]

def fetch(url):
    try:
        req = Request(url, headers=HEADERS)
        return urlopen(req, timeout=15).read().decode("utf-8", errors="ignore")
    except URLError as e:
        return f"ERROR:{e}"

def parse_programs(html):
    # Extract program cards: name, repo, reward
    programs = []
    # Pattern: github org/repo links with reward amounts
    repos = re.findall(r'href="https://github\.com/([^/"]+/[^/"]+)"', html)
    rewards = re.findall(r'\$?([\d,]+)\s*(?:dollars|USD|\$)', html)
    # Simpler: find bounty links
    bounty_links = re.findall(r'href="(/bounties/[^"]+)"', html)

    seen = set()
    for repo in repos:
        if repo not in seen and "/" in repo:
            seen.add(repo)
            programs.append({"repo": repo, "url": f"https://github.com/{repo}"})
    return programs, bounty_links

def score_target(repo_name):
    """Score target by desirability for bug hunting."""
    score = 0
    name = repo_name.lower()
    # AI/ML bonus (higher payouts)
    if any(x in name for x in ["llm","ai","ml","model","inference","torch","transform","diffus","vector","embed"]):
        score += 30
    # Known vuln-rich patterns
    if any(x in name for x in ["server","api","web","app","hub","upload","file","worker"]):
        score += 20
    # Language preference
    if any(x in name for x in ["python","flask","django","fastapi","langchain"]):
        score += 15
    # Less audited (smaller orgs)
    if name.count("/") == 1:
        org = name.split("/")[0]
        if len(org) > 8:  # longer org names = less known
            score += 10
    return score

# Fetch main bounty pages
pages = [
    "https://huntr.com/bounties",
    "https://huntr.com/bounties/disclose",
]

all_repos = []
all_links = []
for url in pages:
    html = fetch(url)
    if html.startswith("ERROR"):
        continue
    repos, links = parse_programs(html)
    all_repos.extend(repos)
    all_links.extend(links)
    time.sleep(1)

# Score and sort
for r in all_repos:
    r["score"] = score_target(r["repo"])
    r["org"] = r["repo"].split("/")[0]
    r["name"] = r["repo"].split("/")[1] if "/" in r["repo"] else r["repo"]

# Deduplicate
seen = set()
unique = []
for r in all_repos:
    if r["repo"] not in seen:
        seen.add(r["repo"])
        unique.append(r)

# Sort by score
unique.sort(key=lambda x: x["score"], reverse=True)
top = unique[:20]

result = {
    "phase": 1,
    "agent": "find_targets",
    "status": "ok",
    "ts": int(time.time()),
    "data": {
        "total_found": len(unique),
        "top_targets": top,
        "recommended": top[0] if top else None
    }
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2))
print(f"Found {len(unique)} targets → {OUT}")
if top:
    print(f"Top pick: {top[0]['repo']} (score={top[0]['score']})")
    print(json.dumps(top[:5], indent=2))
