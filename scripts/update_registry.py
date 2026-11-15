import json
import os
import urllib.request
from datetime import datetime, timezone

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

def fetch_repo_data(owner, repo):
    url = f"https://github.com{owner}/{repo}"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "SkillDeck-Registry-Bot")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def main():
    with open("sources.json", "r", encoding="utf-8") as f:
        sources = json.load(f)

    registry = {
        "version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "skills": []
    }

    for item in sources:
        try:
            data = fetch_repo_data(item["owner"], item["repo"])
            registry["skills"].append({
                **item,
                "name": data.get("name"),
                "description": data.get("description") or "Açıklama bulunmuyor.",
                "stars": data.get("stargazers_count", 0),
                "last_pushed": data.get("pushed_at"),
                "html_url": data.get("html_url"),
                "license": (data.get("license") or {}).get("spdx_id", "MIT")
            })
            print(f"OK: {item['owner']}/{item['repo']} -> ⭐ {data.get('stargazers_count')}")
        except Exception as e:
            print(f"HATA ({item['owner']}/{item['repo']}): {e}")

    # Yıldız sayısına göre en popülerden en aza sırala
    registry["skills"].sort(key=lambda x: x["stars"], reverse=True)

    with open("registry.json", "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
