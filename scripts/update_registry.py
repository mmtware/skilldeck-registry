import json
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

def github_get(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "SkillDeck-Registry-Bot/1.0")
            req.add_header("Accept", "application/vnd.github+json")
            if GITHUB_TOKEN:
                req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
            else:
                raise e

def discover_github_skills():
    queries = [
        "topic:agent-skills stars:>=10",
        "\"SKILL.md\" in:readme,path stars:>=25"
    ]
    discovered = {}
    
    for q in queries:
        # safe="" parametresi ':' ve '>=' karakterlerini güvenli şekilde encode eder
        encoded_q = urllib.parse.quote(q, safe="")
        url = f"https://github.com{encoded_q}&sort=stars&order=desc&per_page=50"
        try:
            res = github_get(url)
            for item in res.get("items", []):
                full_name = item["full_name"]
                if full_name not in discovered:
                    discovered[full_name] = {
                        "id": full_name.replace("/", "-").lower(),
                        "owner": item["owner"]["login"],
                        "repo": item["name"],
                        "name": item["name"],
                        "description": item.get("description") or "Açıklama bulunmuyor.",
                        "stars": item.get("stargazers_count", 0),
                        "last_pushed": item.get("pushed_at"),
                        "html_url": item.get("html_url"),
                        "license": (item.get("license") or {}).get("spdx_id", "MIT"),
                        "install_method": "npx",
                        "command": f"npx skills add {full_name}",
                        "tags": item.get("topics", [])[:5] or ["community"]
                    }
            print(f"Keşif başarılı ({q}): {len(res.get('items', []))} repo bulundu.")
        except Exception as e:
            print(f"Arama hatası ({q}): {e}")
            
    return discovered

def main():
    skills_map = {}

    # 1. Otomatik GitHub keşfini çalıştır
    skills_map.update(discover_github_skills())

    # 2. Özel kaynak listesini ekle/güncelle
    if os.path.exists("sources.json"):
        with open("sources.json", "r", encoding="utf-8") as f:
            sources = json.load(f)
        for item in sources:
            full_name = f"{item['owner']}/{item['repo']}"
            try:
                data = github_get(f"https://github.com{full_name}")
                skills_map[full_name] = {
                    **item,
                    "name": data.get("name"),
                    "description": data.get("description") or "Açıklama bulunmuyor.",
                    "stars": data.get("stargazers_count", 0),
                    "last_pushed": data.get("pushed_at"),
                    "html_url": data.get("html_url"),
                    "license": (data.get("license") or {}).get("spdx_id", "MIT")
                }
                print(f"Özel repo eklendi: {full_name} (⭐ {data.get('stargazers_count', 0)})")
            except Exception as e:
                print(f"Özel repo hatası ({full_name}): {e}")

    all_skills = list(skills_map.values())
    all_skills.sort(key=lambda x: x["stars"], reverse=True)

    registry = {
        "version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_count": len(all_skills),
        "skills": all_skills
    }

    with open("registry.json", "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    print(f"Toplam {len(all_skills)} skill başarıyla registry.json dosyasına yazıldı.")

if __name__ == "__main__":
    main()
