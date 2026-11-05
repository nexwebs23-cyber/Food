#!/usr/bin/env python3
"""
auto_publish_recipes.py
Automated daily recipe publisher for Zaika Worlds.
Reads up to `BATCH_SIZE` (default 3) recipes from `recipes_queue.json`,
appends them to `index.html` (var RECIPES and var LANG_DATA),
updates `recipe_dates.json` and `recipe_nutrition.json`,
runs `build_site.py` to regenerate all static pages and sitemap,
and updates `recipes_queue.json`.
"""

import os
import sys
import json
import datetime
import subprocess
import build_site

BATCH_SIZE = int(os.environ.get("PUBLISH_BATCH_SIZE", 3))
QUEUE_FILE = "recipes_queue.json"
INDEX_FILE = "index.html"
DATES_FILE = "recipe_dates.json"
NUTRITION_FILE = "nutrition.json"

def main():
    if not os.path.exists(QUEUE_FILE):
        print(f"No queue file found: {QUEUE_FILE}")
        return 0

    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        queue = json.load(f)

    if not queue:
        print("Queue is empty. No recipes to publish today.")
        return 0

    to_publish = queue[:BATCH_SIZE]
    remaining = queue[BATCH_SIZE:]
    today_str = datetime.date.today().isoformat()

    print(f"Publishing {len(to_publish)} recipe(s) today ({today_str}):")
    for r in to_publish:
        print(f"  - {r['id']}: {r['name']} ({r.get('country', '')})")

    # Read current index.html
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        src = f.read()

    # 1. Update var RECIPES in index.html
    raw_recipes, s_rec, e_rec = build_site.find_literal(src, "var RECIPES=[", "[")
    existing_recipes, _ = build_site.parse_js_literal(raw_recipes)
    existing_ids = {r["id"] for r in existing_recipes}

    new_recipes = []
    for r in to_publish:
        if r["id"] in existing_ids:
            print(f"Warning: recipe {r['id']} already exists in RECIPES, skipping duplicate.")
            continue
        # Strip queue-only helper keys before injecting to RECIPES
        clean_r = {k: v for k, v in r.items() if k not in ("nutrition", "lang")}
        clean_r["published"] = today_str
        new_recipes.append(clean_r)

    if not new_recipes:
        print("No new valid recipes to add.")
        return 0

    all_recipes = existing_recipes + new_recipes
    new_recipes_json = json.dumps(all_recipes, ensure_ascii=False)
    src = src[:s_rec] + new_recipes_json + src[e_rec:]

    # 2. Update var LANG_DATA in index.html
    raw_lang, s_lang, e_lang = build_site.find_literal(src, "var LANG_DATA={", "{")
    existing_lang, _ = build_site.parse_js_literal(raw_lang)

    for r in to_publish:
        rid = r["id"]
        lang_info = r.get("lang", {})
        existing_lang[rid] = {
            "ru": lang_info.get("ru", {
                "name": r["name"],
                "catLabel": r.get("catLabel", "Desi Dishes"),
                "diff": "Darmiyana",
                "servings": r.get("servings", "4 log"),
                "desc": r.get("desc", ""),
                "alt": r.get("alt", "")
            }),
            "hi": lang_info.get("hi", {
                "name": r["name"],
                "catLabel": r.get("catLabel", "Desi Dishes"),
                "diff": "Medium",
                "servings": r.get("servings", "4 log"),
                "desc": r.get("desc", ""),
                "alt": r.get("alt", "")
            })
        }

    new_lang_json = json.dumps(existing_lang, ensure_ascii=False)
    src = src[:s_lang] + new_lang_json + src[e_lang:]

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"Updated {INDEX_FILE} with {len(new_recipes)} new recipes.")

    # 3. Update recipe_dates.json
    dates_data = {}
    if os.path.exists(DATES_FILE):
        with open(DATES_FILE, "r", encoding="utf-8") as f:
            dates_data = json.load(f)
    if "article" not in dates_data:
        dates_data["article"] = {}
    for r in new_recipes:
        dates_data["article"][r["id"]] = {
            "published": today_str,
            "source": f"auto published on {today_str}"
        }
    with open(DATES_FILE, "w", encoding="utf-8") as f:
        json.dump(dates_data, f, indent=2, ensure_ascii=False)
    print(f"Updated {DATES_FILE}.")

    # 4. Update recipe_nutrition.json
    nut_data = {}
    if os.path.exists(NUTRITION_FILE):
        with open(NUTRITION_FILE, "r", encoding="utf-8") as f:
            nut_data = json.load(f)
    for r in to_publish:
        if "nutrition" in r:
            nut_data[r["id"]] = r["nutrition"]
    with open(NUTRITION_FILE, "w", encoding="utf-8") as f:
        json.dump(nut_data, f, indent=2, ensure_ascii=False)
    print(f"Updated {NUTRITION_FILE}.")

    # 5. Run build_site.py to regenerate all static pages & sitemap
    print("Running build_site.py...")
    ret = build_site.main(["build_site.py"])
    if ret != 0:
        print(f"build_site failed with exit code {ret}")
        sys.exit(ret)

    # 6. Save updated queue
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(remaining, f, indent=2, ensure_ascii=False)
    print(f"Updated {QUEUE_FILE} ({len(remaining)} recipes remaining in queue).")
    print("Auto-publish completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
