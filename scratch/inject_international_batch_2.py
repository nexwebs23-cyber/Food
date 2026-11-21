"""
Inject 5 International recipes (batch 2) into FAT index.html, update nutrition.json and recipe_dates.json.
"""
import json, re, os, sys

INDEX = r'D:\Food-main\index.html'

INJECT_IDS = [
    'korean-beef-bulgogi',
    'lebanese-shish-tawook',
    'vietnamese-banh-mi',
    'moroccan-lamb-tagine',
    'turkish-kiymali-pide',
]

ASSETS = {
    'korean-beef-bulgogi':    'assets/korean-beef-bulgogi.webp',
    'lebanese-shish-tawook':  'assets/lebanese-shish-tawook.webp',
    'vietnamese-banh-mi':     'assets/vietnamese-banh-mi.webp',
    'moroccan-lamb-tagine':   'assets/moroccan-lamb-tagine.webp',
    'turkish-kiymali-pide':   'assets/turkish-kiymali-pide.webp',
}

# 1. Load batch data
with open(r'D:\Food-main\international_batch_2.json', 'r', encoding='utf-8') as f:
    batch = json.load(f)

batch_map = {r['id']: r for r in batch}

# 2. Update nutrition.json
nut_path = r'D:\Food-main\nutrition.json'
if os.path.exists(nut_path):
    with open(nut_path, 'r', encoding='utf-8') as f:
        nutrition_data = json.load(f)
    for rid in INJECT_IDS:
        if rid in batch_map and 'nutrition' in batch_map[rid]:
            nutrition_data[rid] = batch_map[rid]['nutrition']
    with open(nut_path, 'w', encoding='utf-8') as f:
        json.dump(nutrition_data, f, ensure_ascii=False, indent=2)
    print("nutrition.json updated.")

# 3. Update recipe_dates.json
dates_path = r'D:\Food-main\recipe_dates.json'
if os.path.exists(dates_path):
    with open(dates_path, 'r', encoding='utf-8') as f:
        recipe_dates = json.load(f)
    for rid in INJECT_IDS:
        if 'article' in recipe_dates:
            recipe_dates['article'][rid] = {
                'published': '2026-11-21',
                'source': 'auto published on 2026-11-21'
            }
    with open(dates_path, 'w', encoding='utf-8') as f:
        json.dump(recipe_dates, f, ensure_ascii=False, indent=2)
    print("recipe_dates.json updated.")

# 4. Read index.html
with open(INDEX, 'r', encoding='utf-8') as f:
    content = f.read()

if 'var LANG_DATA' not in content:
    print('ERROR: index.html is slim! Restore FAT first.')
    sys.exit(1)

# Check which are to inject
already_present = [rid for rid in INJECT_IDS if f'"{rid}"' in content]
to_inject = [rid for rid in INJECT_IDS if rid not in already_present]

print(f"Already present: {already_present}")
print(f"To inject: {to_inject}")

if not to_inject:
    print("All recipes already present!")
    sys.exit(0)

# Inject into var RECIPES
recipes_match = re.search(r'(var RECIPES=\[)(.*?)(\];)', content, re.DOTALL)
if not recipes_match:
    print('ERROR: could not find var RECIPES=[...]')
    sys.exit(1)

recipes_json_str = recipes_match.group(2)
recipes = json.loads('[' + recipes_json_str + ']')
print(f"Current recipe count: {len(recipes)}")

new_recipes = []
for rid in to_inject:
    r = dict(batch_map[rid])
    r['img'] = ASSETS[rid]
    r['shape'] = 'wide'
    r.pop('nutrition', None)
    new_recipes.append(r)

recipes.extend(new_recipes)
print(f"Updated recipe count: {len(recipes)}")

new_recipes_str = json.dumps(recipes, ensure_ascii=False, separators=(',', ':'))[1:-1]
content = content[:recipes_match.start(2)] + new_recipes_str + content[recipes_match.end(2):]

# Inject into LANG_DATA
for rid in to_inject:
    r = batch_map[rid]
    lang = r.get('lang', {})
    for lang_code, lang_data in lang.items():
        lang_entry = json.dumps({rid: lang_data}, ensure_ascii=False, separators=(',', ':'))[1:-1]
        lang_start = content.find(f'"{lang_code}":{{')
        if lang_start < 0:
            print(f'Warning: lang key "{lang_code}" not found')
            continue
        depth = 0
        pos = lang_start + len(f'"{lang_code}":')
        in_string = False
        escape = False
        for i in range(pos, len(content)):
            c = content[i]
            if escape:
                escape = False
                continue
            if c == '\\' and in_string:
                escape = True
                continue
            if c == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    content = content[:i] + ',' + lang_entry + content[i:]
                    print(f'Injected lang {lang_code} for {rid}')
                    break

# Inject IMG_DIMS
dims_match = re.search(r'(var IMG_DIMS=\{)(.*?)(\};)', content, re.DOTALL)
if not dims_match:
    print('ERROR: could not find var IMG_DIMS')
    sys.exit(1)

for rid in to_inject:
    img_path = ASSETS[rid]
    img_key = json.dumps(img_path)
    img_val = '[1792,1344]'
    dims_match2 = re.search(r'(var IMG_DIMS=\{)(.*?)(\};)', content, re.DOTALL)
    insert_pos = dims_match2.end(2)
    content = content[:insert_pos] + ',' + img_key + ':' + img_val + content[insert_pos:]
    print(f'Injected IMG_DIMS for {rid}: {img_path}')

with open(INDEX, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Successfully updated {INDEX}. New size: {os.path.getsize(INDEX):,} bytes")
