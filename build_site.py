#!/usr/bin/env python3
"""build_site.py — Build the Zaika Worlds site from index.html (source of truth).

What it does
------------
1. Parses the big data blocks out of index.html (RECIPES, EXTRA, LANG_DATA, UI,
   INFO, EXTRA_NEW) and writes them as lazily-loaded files under data/:
     data/recipes.js        RECIPES (all 46, English base + video ids)
     data/extra-en.js       EXTRA for English only
     data/extra-<lang>.js   long-form text for one language (12 files)
     data/ui-en.js          UI.en + INFO.en
     data/ui-<lang>.js      UI + INFO strings for one language (12 files)
     data/lang-data-hi.js / data/lang-data-ru.js   short-form text (hi/ru only)
     data/lang-new.js       LANG_NEW_RAW/2/3: short-form text (name, desc,
                            alt) for the other 10 languages, merged into
                            LANG_DATA by _mergeLangNew() after the data loads
                            (the merge used to run at script load and read
                            RECIPES.length, so it cannot stay inline)
2. Emits thin static SEO pages for every served route, each with its own
   <title> (<=60 chars), meta description, canonical + OG/Twitter tags and
   JSON-LD built from the same data setRouteMeta() uses:
     recipe/<slug>/index.html   x46
     category/<slug>/index.html x11
     country/<slug>/index.html  x25
     about/index.html, privacy/index.html, contact/index.html
     recipes/index.html, trending/index.html, faqs/index.html
     eid-recipes/index.html, ramadan-recipes/index.html (seasonal hubs)
     guides/dum-cooking/index.html (technique guide from real recipe tips)
     <lang>/recipe/<slug>/index.html  x12 languages x46 recipes
     <lang>/index.html  x12 language homepages
   Language prefixes: roman-urdu (ur-Latn), hi, ru (Russian), es, fr, ar,
   pt, zh, ja, de, tr, bn. English stays at the root (hreflang "en",
   x-default). Internal "ru" (Roman Urdu) is NEVER reused as ISO "ru"
   (Russian). Each language page carries hreflang for every variant.
   Filesystem beats Vercel rewrites, so a direct visit to /recipe/<slug>
   serves the static page; SPA navigation (pushState) still works.
   Recipe pages: og:type article + article:published_time from
   recipe_dates.json at the repo root (real git-history date only; never invented),
   split one-per-line ingredients, embedded YouTube iframe + VideoObject
   (uploadDate only from a real publish record), FAQPage JSON-LD.
   The slim homepage gets a static 46-card recipe grid (raw HTML, no JS)
   and FAQPage JSON-LD for the homepage FAQ.
3. Regenerates sitemap.xml from the same source of truth as the static
   pages (656 URLs: 86 original + 552 language recipe pages + 12 language
   homepages + 6 new pages). No <lastmod> is written: no per-page
   modification date is recorded, and inventing one would be a fake date.
4. Rewrites index.html in place into a slim SPA shell (~160KB instead of
   ~3.1MB): the data blocks become empty declarations, an async loader pulls
   data/*.js (English first, other languages on demand), the six raw <h1>
   elements become one <h1> plus runtime heading promotion, and the tail
   merge loop is replaced by the loader init.

Authoring rules for new recipes (enforced by --check, which FAILS the
build on a violation — see validate_build())
---------------------------------------------------------------
- Ingredients: write them as combined strings in index.html (the build
  splits them one-per-line at build time); a qualifier fragment
  ("soaked", "for the rice water") must stay attached to its ingredient,
  never as its own line. The splitter is in split_ingredients().
- Titles: "<Dish> Recipe (<CountryAdj>, <time> Min) | Zaika Worlds",
  <=60 chars; the generator shortens (drop time, then style) and never
  exceeds 60. Descriptions: 140-155 chars, from the recipe's own desc +
  time + servings + difficulty + CTA, unique per recipe.
- OG image: every recipe page uses its own photo (absolute /assets/...
  URL); every category/country page uses a representative recipe photo.
  Recipe photos are unique AI-generated images made for Zaika Worlds —
  never claim they are photographs of real dishes.
- Dates: article:published_time comes only from recipe_dates.json (repo root)
  (real git-history / publish records). Never invent a date; omit it if
  no real record exists. VideoObject uploadDate likewise.
- Language pages are auto-generated for every language whose data is
  complete (all 12 non-English languages are complete today). Never
  machine-translate: language pages use only the site's own translations.
- No invented facts anywhere: no fake author credentials, step photos,
  FAQ questions/answers, or backlink/authority numbers. FAQ content comes
  only from the recipes' EXTRA faq data.
- The daily new-recipe cron must record the real add date (and the real
  YouTube publish date per language) in recipe_dates.json (repo root, NOT
  tools/ — tools/ is vercelignored), and add
  the recipe's videos to the videos map, so the next build picks them up.


Idempotency / staleness
-----------------------
Vercel runs this script as its build command on every deploy, so a push that
only edits index.html (e.g. the daily new-recipe cron) regenerates the data
files and static pages automatically — nothing goes stale. The script refuses
to run on an already-slim index.html (it looks for the data anchors and for
the ZAIKA_SLIM_BUILD marker), so a double run fails loudly instead of
corrupting the source. The committed data/ and recipe|category|country|*
pages are snapshots for local serving; the build regenerates them.

Run:
  python3 build_site.py            full build (data + static pages + slim index.html)
  python3 build_site.py --check    validate only, write nothing
  python3 build_site.py --source-fix
                                   apply only the H1/CSS/heading-promotion fix
                                   to index.html in place (keeps the fat data)

Stdlib only. No network, no node.
"""

import email.utils
import html as htmlmod
import json
import os
import re
import sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = "https://www.zaikaworlds.com"
SLIM_MARKER = "ZAIKA_SLIM_BUILD"

LANGS = ["en", "ru", "hi", "es", "fr", "ar", "pt", "rus", "zh", "ja", "de",
         "tr", "bn"]
# Languages whose long-form text lives in EXTRA (objects):
EXTRA_OBJ_LANGS = ["hi", "ru"]
# Languages whose long-form text lives in EXTRA_NEW (10-element arrays):
EXTRA_NEW_LANGS = ["es", "fr", "ar", "pt", "rus", "zh", "ja", "de", "tr", "bn"]
# Languages with short-form LANG_DATA entries:
LANG_DATA_LANGS = ["hi", "ru"]
# Order of the 10 elements in each EXTRA_NEW array (same as the merge loop):
EXTRA_KEYS = ["intro", "ing", "steps", "tip", "notes", "variations",
              "serving", "storage", "mistakes", "faq"]

DEF_DESC = ("Cook famous dishes from Pakistan and India, plus favourites from "
            "around the world, with big photos and step by step methods.")
DEF_IMG = SITE + "/assets/hero-49347f9b.webp"
DEF_ALT = ("A large plate of chicken biryani with saffron rice, fresh "
           "coriander and onion")

_MONTHS = ('January', 'February', 'March', 'April', 'May', 'June', 'July',
           'August', 'September', 'October', 'November', 'December')


def fmt_date(iso):
    """'2026-10-28' -> '28 October 2026' (visible publish date, issue
    #15). Returns '' for a missing/invalid date — never invent one."""
    try:
        y, m, d = iso.split('-')
        return '%d %s %s' % (int(d), _MONTHS[int(m) - 1], y)
    except Exception:
        return ''


# og:image assignment for non-recipe hub pages (audit issue #6,
# 2026-10-31): the audit found EVERY non-recipe page sharing the same
# biryani photo. Each hub page now gets a DISTINCT recipe photo; the
# category/country picks are from that group's own recipes. The table
# is the stable assignment (no churn when the daily cron adds a
# recipe); hub_og() falls back deterministically for a hub page not
# listed here (a new category/country), and --check fails the build
# on any duplicate, so an exhausted pool is caught, not silently
# shared. Language variants of a page share its og:image by design.
HUB_OG = {
    '/': 'biryani',
    '/category/bbq': 'chapli',
    '/category/desi-dishes': 'daal',
    '/category/drinks': 'lassi',
    '/category/desserts': 'gajarhalwa',
    '/category/breakfast': 'halwapuri',
    '/category/street-food': 'bunkebab',
    '/category/world-food': 'pizza',
    '/country/pakistan': 'haleem',
    '/country/india': 'gulabjamun',
    '/country/australia': 'meatpie',
    '/country/brazil': 'feijoada',
    '/country/canada': 'poutine',
    '/country/china': 'dimsum',
    '/country/france': 'bouillabaisse',
    '/country/greece': 'moussaka',
    '/country/italy': 'carbonara',
    '/country/japan': 'ramen',
    '/country/mexico': 'pozole',
    '/country/middle-east': 'falafel',
    '/country/south-africa': 'bobotie',
    '/country/spain': 'paella',
    '/country/thailand': 'padthai',
    '/country/vietnam': 'beefpho',
    '/about': 'coqauvin',
    '/recipes': 'hummus',
    '/trending': 'karahi',
    '/faqs': 'nihari',
    '/eid-recipes': 'pekingduck',
    '/ramadan-recipes': 'samosa',
    '/guides/dum-cooking': 'sushi',
    '/privacy': 'tacos',
    '/contact': 'tikka',
    '/category/asian-dishes': 'kabuli-pulao',
    '/country/afghanistan': 'seekh-kebab',
    '/country/armenia': 'dolma',
    '/country/azerbaijan': 'plov',
    '/category/rice-dishes': 'machboos',
    '/country/bahrain': 'kheer',
    '/category/fish-dishes': 'ilish-bhapa',
    '/country/bangladesh': 'aloo-paratha',
    '/country/bhutan': 'ema-datshi',
    '/country/brunei-darussalam': 'ambuyat',
    '/country/cambodia': 'fish-amok',
    '/category/grill-bbq': 'souvla',
    '/country/cyprus': 'chicken-korma',
}


def hub_og(data, path, group_recipes=None):
    """(og_image_url, og_image_alt, recipe_id) for a hub page."""
    by_id = {r['id']: r for r in data['recipes']}
    used = set(HUB_OG.values())
    rid = HUB_OG.get(path)
    rep_recipe = by_id.get(rid) if rid else None
    if rep_recipe is None:
        for r in list(group_recipes or []) + list(data['recipes']):
            if r['id'] not in used:
                rep_recipe = r
                break
    if rep_recipe is None:
        return (DEF_IMG, DEF_ALT, None)
    tx = r_text_en(rep_recipe, data['extra'])
    return (SITE + '/' + rep_recipe['img'],
            tx.get('alt') or rep_recipe['name'], rep_recipe['id'])
CONTACT_EMAIL = "info.allcalctool@gmail.com"


# ---------------------------------------------------------------------------
# Ingredient splitting (SEO audit round 2, issue G)
# ---------------------------------------------------------------------------
# Recipe ingredients are authored as a few comma-joined groups per recipe
# (e.g. "Chicken 750g, yoghurt 1 cup"), but Recipe schema and the recipe
# pages need ONE ingredient per <li>. The build splits each group on the
# language's list separator (", " / "، " / "，" / "、") and on the language's
# word for "and", then re-attaches qualifier fragments to the ingredient
# they modify instead of leaving them as orphan items:
#   "Basmati rice 3 cups, soaked" -> "Basmati rice 3 cups (soaked)"
#   "Salt, bay leaves, cardamom and cloves, for the rice water"
#       -> "Salt", "bay leaves", "cardamom", "cloves (for the rice water)"
# A fragment is a qualifier if it starts/ends with the language's "for"
# marker, is the word for "optional", or is a bare participle/adjective
# (soaked, chopped, ...) listed in ING_QUALIFIERS. Real ingredients that
# carry their purpose ("Oil for frying", "Parsley to serve") are NOT
# qualifiers: they name an ingredient, so they stay as their own item.
# The sets below were derived from the actual 32x13 ingredient strings
# (see the SEO round-2 data report); a future recipe that introduces a new
# bare qualifier is caught by --check, which fails on any split item that
# matches these rules. Authoring rule: never write a bare qualifier as its
# own comma group — attach it to the ingredient it modifies in the source.

ING_SEPS = {
    'en': [', ', ' and '], 'ru': [', ', ' aur '], 'hi': [', ', ' और '],
    'es': [', ', ' y '], 'fr': [', ', ' et '], 'ar': ['، '],
    'pt': [', ', ' e '], 'rus': [', ', ' и '], 'zh': ['，', '、', '和'],
    'ja': ['、', 'と'], 'de': [', ', ' und '], 'tr': [', ', ' ve '],
    'bn': [', ', ' ও '],
}
# "for ..." markers: (prefixes, suffixes) per language. Arabic "for" is the
# prefix "ل" but lemon ("ليمون") also starts with it, so Arabic uses the
# exact set in ING_FOR_EXACT instead of a prefix rule.
ING_FOR_PREFIX = {
    'en': ('for ',), 'es': ('para ',), 'fr': ('pour ',),
    'pt': ('para ',), 'rus': ('для ',), 'de': ('für ', 'zum '),
    'zh': ('用于',),
}
ING_FOR_SUFFIX = {
    'ru': (' ke liye',), 'hi': (' के लिए',), 'tr': (' için',),
    'bn': (' জন্য',), 'ja': ('用',),
}
ING_FOR_EXACT = {
    'ar': {'لسيو ماي', 'للتزيين', 'للتقديم', 'للتلميع', 'لماء الأرز',
           'لمايونيز حار', 'لهار غاو'},
}
ING_OPTIONAL = {
    'en': 'optional', 'ru': 'optional', 'hi': 'वैकल्पिक', 'es': 'opcional',
    'fr': 'en option', 'ar': 'اختياري', 'pt': 'opcional',
    'rus': 'по желанию', 'zh': '可选', 'ja': '任意', 'de': 'optional',
    'tr': 'isteğe bağlı', 'bn': 'ঐচ্ছিক',
}
# Bare qualifier fragments (lowercase) per language. Only fragments that
# actually occur in the 46 recipes are listed, plus a few common English
# participles for future recipes.
ING_QUALIFIERS = {
'en': {'soaked', 'soaked overnight', 'chopped', 'sliced', 'fried', 'diced',
       'diced small', 'grated', 'finely chopped', 'finely grated',
       'thinly sliced', 'lightly beaten', 'freshly cracked', 'beaten',
       'browned', 'cleaned', 'cooked', 'crushed', 'cubed', 'flaked',
       'flat', 'hot', 'peeled', 'rinsed', 'torn', 'uncooked',
       'well stirred', 'soft boiled', 'melted', 'brown', 'toasted',
       'blanched', 'minced', 'roasted', 'grilled', 'steamed', 'boiled',
       'washed', 'trimmed', 'halved', 'quartered', 'crumbled', 'ground',
       'softened', 'cut into chunks', 'cut into large chunks',
       'cut into strips', 'cut into thin sticks', 'at room temperature',
       'bone in', 'floury variety', 'burgundy style if possible',
       'plus more to serve'},
'ru': {'bhigoye hue', 'raat bhar bhigoye hue', 'kate hue', 'kati hui',
       'kaddukas', 'bareek kaddukas', 'kaddukas ki hui',
       'bareek kate hue', 'kooti hui', 'kuchle hue', 'taazi kooti hui',
       'chhane hue', 'chheele hue', 'dhoya hua', 'phenta hua',
       'halke phente hue', 'saaf ki hui', 'tooti hui', 'brown ki hui',
       'pake hue', 'naram ubale hue', 'achhi tarah hilayi hui',
       'tukdon mein kata hua', 'tukdon mein kati hui',
       'strips mein kata hua', 'patli kati hui',
       'patli sticks mein kata hua', 'cube mein kata hua',
       'dice mein kata hua', 'chhote dice mein kata hua',
       'bare tukdon mein kata hua', 'slice mein kati hui',
       'chhote tukde', 'kachhe', 'garam', 'chapte', 'floury qism',
       'haddi ke sath', 'room temperature par',
       'mumkin ho to burgundy style', 'flaked', 'chhana',
       'aur serve ke liye zyada'},
'hi': {'भिगोए हुए', 'रात भर भिगोए हुए', 'कटे हुए', 'कटी हुई', 'कद्दूकस',
       'बारीक कद्दूकस', 'कद्दूकस की हुई', 'बारीक कटे हुए', 'कुटी हुई',
       'कुचले हुए', 'ताज़ी कुटी हुई', 'छाने हुए', 'छीले हुए',
       'धोया हुआ', 'फेंटा हुआ', 'हल्के फेंटे हुए', 'साफ़ की हुई',
       'तोड़ा हुआ', 'ब्राउन की हुई', 'पके हुए', 'नरम उबले हुए',
       'अच्छी तरह हिलाई हुई', 'टुकड़ों में कटा हुआ',
       'टुकड़ों में कटी हुई', 'स्ट्रिप्स में कटा हुआ', 'पतली कटी हुई',
       'पतली स्टिक्स में कटा हुआ', 'क्यूब में कटा हुआ',
       'डाइस में कटा हुआ', 'छोटे डाइस में कटा हुआ',
       'बड़े टुकड़ों में कटा हुआ', 'स्लाइस में कटी हुई', 'छोटे टुकड़े',
       'कच्चे', 'गर्म', 'चपटे', 'फ्लाउरी किस्म', 'हड्डी के साथ',
       'कमरे के तापमान पर', 'मुमकिन हो तो बरगंडी स्टाइल', 'फ्लेक्ड',
       'छाना', 'और परोसने के लिए ज़्यादा'},
'es': {'remojado', 'remojados toda la noche', 'picados', 'picadas finas',
       'cortado en trozos', 'cortado en tiras',
       'cortado en bastones finos', 'cortada en trozos',
       'cortada en trozos grandes', 'rallado', 'rallados', 'ralladas',
       'rallado fino', 'batido', 'batidos ligeramente', 'bien removido',
       'cocidos', 'cocidos blandos', 'sin cocer', 'desgarrada',
       'doradas', 'en cubos', 'en dados', 'en dados pequeños',
       'en lonchas finas', 'en láminas', 'en rodajas', 'enjuagado',
       'escurrido', 'escurridos', 'limpios', 'machacados', 'peladas',
       'triturados', 'planos', 'caliente', 'con hueso',
       'a temperatura ambiente', 'variedad harinosa',
       'más para servir'},
'fr': {'battu', 'bien remué', 'concassées', 'coupé en fins bâtonnets',
       'coupé en lanières', 'coupé en morceaux', 'coupé en petits dés',
       'coupée en gros morceaux', 'cuits', 'dorés', 'déchirée',
       'décortiquées', 'effilées', 'en cubes', 'en dés',
       'en fines tranches', 'finement hachées', 'finement râpé',
       'fraîchement moulu', 'hachées', 'hachés', 'légèrement battus',
       'nettoyées', 'non cuit', 'râpé', 'râpées', 'rincé', 'tranchée',
       'tranchées', 'trempé', 'trempés une nuit', 'écrasées', 'égoutté',
       'égouttés', 'avec os', 'chaud', 'plates',
       'style bourgogne si possible', 'variété farineuse',
       'à température ambiante', 'plus pour servir', 'mollets'},
'ar': {'منقوع', 'منقوع طوال الليل', 'منقوعة طوال الليل', 'مقطع', 'مقطعة',
       'مقطع إلى أعواد رفيعة', 'مقطع إلى شرائح', 'مقطع إلى قطع',
       'مقطع إلى قطع كبيرة', 'مقطع شرائح رفيعة', 'مقطع صغيرا',
       'مبشور', 'مبشور ناعما', 'مبشورة', 'مجروش', 'مجروش طازجا',
       'محركة جيدا', 'محمر', 'مخفوق قليلا', 'مخفوقة', 'مسطحة',
       'مسلوق طريا', 'مصفى', 'مصفى ومشطوف', 'مطهو', 'مفروم',
       'مفروم ناعما', 'مفرومة', 'مقشر', 'مكعبات', 'ممزقة', 'منظف',
       'مهروسة', 'غير مطهو', 'بالعظم', 'ساخن', 'صنف دقيقي',
       'في درجة حرارة الغرفة', 'على طراز بورغندي إن أمكن',
       'بالإضافة إلى المزيد للتقديم'},
'pt': {'demolhado', 'demolhado durante a noite', 'picados',
       'finamente picados', 'cortado em pedaços', 'cortado em tiras',
       'cortado em palitos finos', 'cortada em pedaços grandes',
       'ralado', 'ralados', 'raladas', 'finamente ralado', 'batido',
       'bem mexido', 'cozido', 'cozidos moles', 'cru', 'descascados',
       'douradas', 'em cubos', 'em cubos pequenos', 'escorrido',
       'esmagados', 'fatiada', 'fatiada finamente', 'fatiadas',
       'laminadas', 'levemente batidos', 'limpos', 'passado por água',
       'rasgada', 'achatados', 'com osso', 'quente',
       'estilo borgonha se possível', 'variedade farinhenta',
       'à temperatura ambiente', 'mais para servir', 'acabada de moer'},
'rus': {'замоченный', 'замоченный на ночь', 'замоченная на ночь',
        'варёный', 'взбитое', 'дроблёные', 'дроблёный',
        'мелко нарезанные', 'мелко нарезанный', 'мелко натёртый',
        'нарезанная', 'нарезанная крупными кусками',
        'нарезанная кубиками', 'нарезанная кусками', 'нарезанные',
        'нарезанный', 'нарезанный кубиками', 'нарезанный кусками',
        'нарезанный полосками', 'очищенные', 'порванная', 'промытое',
        'сваренные всмятку', 'свежемолотый', 'слегка взбитые',
        'слитое', 'слитый', 'сырой', 'тонко нарезанная', 'тёртая',
        'тёртые', 'тёртый', 'хлопьями', 'хорошо размешанная',
        'плоская', 'горячий', 'мучнистый сорт', 'на кости',
        'при комнатной температуре', 'бургундского стиля',
        'если возможно', 'плюс ещё для подачи', 'в которой варится рис'},
'zh': {'切丁', '切块', '切小丁', '切得很碎', '切成大块', '切成条', '切成细条',
       '切片', '切碎', '切薄片', '压碎', '去壳', '充分搅匀', '已浸泡',
       '浸泡过夜', '沥干', '沥干并冲洗', '清理干净', '打散', '轻轻打散',
       '擦碎', '磨得很细', '磨碎', '新鲜磨碎', '撕碎', '煮好', '未煮',
       '炸至金黄', '煮成溏心蛋', '扁的', '热的', '室温', '粉质品种',
       '最好是勃艮第风格', '另加一些用于上桌', '大的'},
'ja': {'きつね色に炒めたもの', 'きれいにしたもの', 'さいの目切り',
       'すりおろしたもの', 'ちぎったもの', 'つぶしたもの',
       'よく混ぜたもの', '刻んだもの', '塊に切ったもの',
       '大きめの塊に切ったもの', '小さくさいの目切り', '平たいもの',
       '挽きたて', '水に浸したもの', '水を切ったもの',
       '水を切ってすすいだもの', '溶いたもの', '軽く溶いたもの',
       '皮をむいたもの', '短冊切り', '砕いたもの',
       '細い棒状に切ったもの', '細かくすりおろしたもの',
       '細かく刻んだもの', '角切り', '調理済み', '薄切り', 'スライス',
       'フレーク状', '半熟ゆで卵', '丸ご', 'できればブルゴーニュ風',
       '室温', '粉質の品種', '熱いもの', '炊く前', '一晩浸したもの',
       'つかみ', 'さらに出すためのもの'},
'de': {'abgespült', 'abgetropft', 'dünn geschnitten', 'eingeweicht',
       'fein gehackt', 'fein gerieben', 'flach', 'frisch gemahlen',
       'gebräunt', 'gehackt', 'gehobelt', 'gekocht', 'geputzt',
       'gerieben', 'geschält', 'gewürfelt', 'gezupft', 'gut gerührt',
       'heiß', 'in scheiben', 'in streifen geschnitten',
       'in stücke geschnitten', 'in dünne stifte geschnitten',
       'in große stücke geschnitten', 'klein gewürfelt',
       'leicht verquirlt', 'mehlige sorte', 'mit knochen',
       'plus mehr zum servieren', 'ungekocht', 'verquirlt',
       'weich gekocht', 'wenn möglich', 'zerdrückt', 'zerstoßen',
       'über nacht eingeweicht', 'bei zimmertemperatur',
       'burgunder art'},
'tr': {'ayıklanmış', 'bir gece ıslatılmış', 'dilimlenmiş', 'doğranmış',
       'durulanmış', 'ezilmiş', 'hafifçe çırpılmış', 'ince dilimlenmiş',
       'ince doğranmış', 'ince rendelenmiş', 'iyice karıştırılmış',
       'küp doğranmış', 'küçük doğranmış', 'kızartılmış',
       'parçalanmış', 'parçalar hâlinde kesilmiş', 'pişmemiş',
       'pişmiş', 'pul pul', 'rendelenmiş', 'süzülmüş', 'temizlenmiş',
       'çırpılmış', 'ıslatılmış', 'şeritler hâlinde kesilmiş',
       'yumuşak haşlanmış', 'taze kırılmış', 'kemikli', 'sıcak',
       'oda sıcaklığında', 'unlu çeşit', 'yassı',
       'mümkünse burgonya tarzı'},
'bn': {'কাটা', 'কিউব করা', 'কিউব করে কাটা', 'কুচি করা',
       'খোসা ছাড়ানো', 'ছেঁকে ধোয়া', 'ছেঁকে নেওয়া', 'ছেঁড়া',
       'ছোট কিউব করা', 'টুকরো করে কাটা', 'থেঁতো করা',
       'পাতলা করে কাটা', 'পাতলা কাঠি করে কাটা', 'ফালি করা',
       'ফালি করে কাটা', 'ফেটানো', 'হালকা ফেটানো',
       'বড় টুকরো করে কাটা', 'ভাজা', 'ভেজানো', 'সারারাত ভেজানো',
       'পরিষ্কার করা', 'রান্না করা', 'রান্না না করা', 'নরম সেদ্ধ',
       'টাটকা ভাঙা', 'ভালো করে নাড়া', 'মিহি করে কাটা', 'গরম',
       'ঘরের তাপমাত্রায়', 'চ্যাপ্টা', 'ময়দাযুক্ত জাত', 'হাড়সহ',
       'পারলে বার্গান্ডি ধাঁচের', 'সঙ্গে পরিবেশনের জন্য আরও'},
}


def _split_top(s, seps):
    """Split s on seps, but never inside parentheses. Japanese 'と' is only
    a list join when it is not part of a word or fraction: never split it
    after a digit ('1と1/2'), before 'の' ('丸ごと') or before 'つ'
    ('ひとつかみ')."""
    out, cur, depth, i = [], '', 0, 0
    while i < len(s):
        ch = s[i]
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth = max(0, depth - 1)
        if depth == 0:
            hit = None
            for sep in seps:
                if s.startswith(sep, i):
                    if sep == 'と':
                        prev = s[i - 1] if i > 0 else ''
                        nxt = s[i + 1] if i + 1 < len(s) else ''
                        if prev.isdigit() or nxt in ('の', 'つ'):
                            continue
                    hit = sep
                    break
            if hit:
                out.append(cur)
                cur = ''
                i += len(hit)
                continue
        cur += ch
        i += 1
    out.append(cur)
    return [x.strip() for x in out if x.strip()]


def is_qualifier(item, lang):
    """True if a split ingredient piece is a qualifier fragment, not an
    ingredient of its own (see the ING_QUALIFIERS comment above)."""
    low = item.strip().lower()
    if not low:
        return False
    if low == ING_OPTIONAL.get(lang, ''):
        return True
    if low in ING_FOR_EXACT.get(lang, set()):
        return True
    for p in ING_FOR_PREFIX.get(lang, ()):
        if low.startswith(p):
            return True
    for suf in ING_FOR_SUFFIX.get(lang, ()):
        if low.endswith(suf):
            return True
    return low in ING_QUALIFIERS.get(lang, set())


def split_ingredients(items, lang):
    """Split ingredient strings into one ingredient per item, attaching
    qualifier fragments to the previous item as a parenthetical."""
    out = []
    for s in items or []:
        for piece in _split_top(s, ING_SEPS[lang]):
            if is_qualifier(piece, lang) and out:
                prev = out[-1]
                if prev.endswith(')'):
                    out[-1] = prev[:-1] + ', ' + piece + ')'
                else:
                    out[-1] = prev + ' (' + piece + ')'
            else:
                out.append(piece)
    return out


# ---------------------------------------------------------------------------
# Titles + meta descriptions (SEO audit round 2, issue F)
# ---------------------------------------------------------------------------
# Recipe title: "<Dish> Recipe (<CountryAdj>, <time> Min) | Zaika Worlds",
# capped at 60 chars — if the full pattern is too long, drop the time,
# then shorten the style. Recipe description: the recipe's real desc +
# " Ready in <time> min, serves <servings>, <diff> difficulty. Start
# cooking now.", fitted to 140-155 chars by trimming the desc at a word
# boundary (weak trailing words backed off) — never by inventing text.
# List/info descriptions are fitted the same way from their real intros.

_TITLE_STOP = {'that', 'with', 'and', 'the', 'a', 'an', 'in', 'on', 'of',
               'to', 'for', 'from', 'at', 'by', 'or', 'as', 'is', 'it'}
# Characters that end a sentence (Latin + Devanagari danda + CJK).
SENT_END = set('.!?।。！？')


def fit_desc(desc, tail):
    """desc + tail, fitted to 140-155 chars by trimming desc at a word
    boundary (backing off weak trailing words). Returns the fitted text;
    callers must check the length (a very short desc cannot reach 140)."""
    desc = (desc or '').strip()
    if desc and desc[-1] not in SENT_END:
        desc += '.'
    d = desc + tail
    if len(d) > 155:
        room = 155 - len(tail)
        cut = desc[:room]
        sp = cut.rfind(' ')
        # Cut at a word boundary only if it is near the end (losing at
        # most ~25 chars); otherwise keep the hard cut (CJK text has no
        # spaces, and cutting back to a distant space would drop a whole
        # appended sentence).
        if sp > room - 25 and sp > 40:
            cut = cut[:sp]
            # Back off weak trailing words ("... the dum aroma that.").
            while True:
                words = cut.rsplit(' ', 1)
                if (len(words) == 2
                        and words[1].strip(' ,;:').lower() in _TITLE_STOP
                        and len(cut) > 60):
                    cut = words[0]
                else:
                    break
        cut = cut.rstrip(' ,;:')
        if cut and cut[-1] not in SENT_END:
            cut += '.'
        d = cut + tail
        if len(d) > 155:
            # CJK text has no spaces to cut at: hard-trim the desc part.
            cut = cut[:155 - len(tail)]
            d = cut + tail
    return d


def list_desc(base, sentences):
    """Fit a list-page description to 140-155 chars from real text: start
    with base, append real sentences (in priority order) until >=140,
    trimming the last sentence at a word boundary to fit <=155."""
    d = (base or '').strip()
    if d and d[-1] not in SENT_END:
        d += '.'
    for s in sentences or []:
        if len(d) >= 140:
            break
        s = (s or '').strip()
        if not s:
            continue
        if s[-1] not in SENT_END:
            s += '.'
        if len(d) + 1 + len(s) <= 155:
            d = d + ' ' + s
        else:
            room = 155 - len(d) - 1
            if room >= 25:
                cut = s[:room]
                sp = cut.rfind(' ')
                if sp > 15:
                    cut = cut[:sp]
                cut = cut.rstrip(' ,;:')
                if cut and cut[-1] not in SENT_END:
                    cut += '.'
                d = d + ' ' + cut
    return d


def recipe_title_en(recipe, data):
    """'<Dish> Recipe (<CountryAdj>, <time> Min) | Zaika Worlds', <=60."""
    adj = data['country_adj'].get(recipe['country'], recipe['country'])
    full = '%s Recipe (%s, %d Min) | Zaika Worlds' % (
        recipe['name'], adj, recipe['time'])
    if len(full) <= 60:
        return full
    no_time = '%s Recipe (%s) | Zaika Worlds' % (recipe['name'], adj)
    if len(no_time) <= 60:
        return no_time
    return '%s Recipe | Zaika Worlds' % recipe['name']


def recipe_desc_en(recipe, tx):
    """Recipe meta description, 140-155 chars, from the recipe's own desc,
    time, servings and difficulty."""
    tail = (' Ready in %d min, serves %s, %s difficulty. Start cooking now.'
            % (recipe['time'], recipe['servings'], recipe['diff']))
    return fit_desc(tx.get('desc') or '', tail)


def recipe_title_lang(recipe, data, lang):
    """Recipe title in a language: English uses the full pattern; other
    languages use the translated name + brand (the pattern's style/time
    words have no translation in the data). Capped at 60 chars."""
    name = lang_name(recipe, data, lang)
    if lang == 'en':
        return recipe_title_en(recipe, data)
    t = '%s | Zaika Worlds' % name
    if len(t) <= 60:
        return t
    return name if len(name) <= 60 else name[:60]


def recipe_desc_lang(recipe, data, lang):
    """Recipe meta description in a language: the translated desc + time,
    servings and difficulty in that language, fitted to <=155 chars. If
    the result is below 140, the first sentence of the translated intro
    (real text) is appended and the whole is re-fitted; the 140 floor is
    enforced for English only, because translated descs vary in length
    and the text must not be padded with invented words."""
    if lang == 'en':
        return recipe_desc_en(recipe, r_text_en(recipe, data['extra']))
    tx = r_text_lang(recipe, data, lang)
    desc = tx.get('desc') or lang_desc(recipe, data, lang)
    minute = data['ui_min'].get(lang, 'min')
    tail = (' %d %s, %s, %s.' % (recipe['time'], minute,
                                 lang_servings(recipe, data, lang),
                                 lang_diff(recipe, data, lang)))
    d = fit_desc(desc, tail)
    if len(d) < 140:
        # Append real intro sentences (in order) until >=140; fit_desc
        # trims the last one to <=155. CJK text is denser, so it may
        # still land below 140 — that is reported, not padded.
        parts = [desc]
        for s in split_sentences(tx.get('intro') or ''):
            if len(' '.join(parts) + tail) >= 140:
                break
            parts.append(s)
        if len(parts) > 1:
            d = fit_desc(' '.join(parts), tail)
    return d


def split_sentences(text):
    """Split text into sentences (Latin . ! ? need a space/end after;
    Devanagari । and CJK 。！？ end on their own)."""
    t = (text or '').strip()
    if not t:
        return []
    parts = re.split(r'(?<=[.!?])(?=\s|$)|(?<=[।。！？])', t)
    return [p.strip() for p in parts if p.strip()]


def first_sentence(text):
    """First sentence of a text (used to pad short descriptions)."""
    s = split_sentences(text)
    return s[0] if s else (text or '').strip()


def fit_text(text, tail='', lo=140, hi=155):
    """Fit a description from real text: text + tail, trimmed to hi; if
    still below lo, append the first sentence of the extra text given in
    tail2 (a second call). Used for list/info pages."""
    return fit_desc(text, tail)


# ---------------------------------------------------------------------------
# Multilingual URLs + hreflang (SEO audit round 2, issue N)
# ---------------------------------------------------------------------------
# URL prefixes per site language code. English stays at the root (hreflang
# "en", x-default). Internal "ru" is Roman Urdu (hreflang "ur-Latn") — it
# must NOT be confused with ISO "ru", which is Russian (internal "rus").
LANG_PREFIX = {'en': '', 'ru': 'roman-urdu', 'hi': 'hi', 'es': 'es',
               'fr': 'fr', 'ar': 'ar', 'pt': 'pt', 'rus': 'ru',
               'zh': 'zh', 'ja': 'ja', 'de': 'de', 'tr': 'tr', 'bn': 'bn'}
LANG_HREFLANG = {'en': 'en', 'ru': 'ur-Latn', 'hi': 'hi', 'es': 'es',
                 'fr': 'fr', 'ar': 'ar', 'pt': 'pt', 'rus': 'ru',
                 'zh': 'zh', 'ja': 'ja', 'de': 'de', 'tr': 'tr',
                 'bn': 'bn'}
LANG_NAME = {'en': 'English', 'ru': 'Roman Urdu', 'hi': 'Hindi',
             'es': 'Spanish', 'fr': 'French', 'ar': 'Arabic',
             'pt': 'Portuguese', 'rus': 'Russian', 'zh': 'Chinese',
             'ja': 'Japanese', 'de': 'German', 'tr': 'Turkish',
             'bn': 'Bengali'}


def lang_url(path, lang):
    """URL of a route in a language: lang_url('/recipe/biryani', 'hi')
    -> 'https://www.zaikaworlds.com/hi/recipe/biryani' (English: root)."""
    prefix = LANG_PREFIX[lang]
    if not prefix:
        return SITE + path
    return SITE + '/' + prefix + path


def hreflang_links(path):
    """[(hreflang, url)] for every language variant of a route + x-default
    (which points at the English root URL)."""
    out = [(LANG_HREFLANG[lang], lang_url(path, lang)) for lang in LANGS]
    out.append(('x-default', SITE + path))
    return out


def r_text_lang(recipe, data, lang):
    """Long-form text for a recipe in any language (what rText() returns
    for LANG). English/hi/ru come from EXTRA objects; the other 10 from
    EXTRA_NEW (already normalised to the same 10 keys)."""
    if lang == 'en':
        return r_text_en(recipe, data['extra'])
    if lang in EXTRA_OBJ_LANGS:
        d = dict(data['extra'].get(recipe['id'], {}).get(lang, {}))
    else:
        d = dict(data['extra_new'].get(lang, {}).get(recipe['id'], {}))
    if not d:
        # Fallback to English base fields so new recipes work immediately in all languages
        d = dict(r_text_en(recipe, data['extra']))
    if not d.get('alt'):
        d['alt'] = recipe.get('alt') or recipe['name']
    return d


def _lang_new_arr(recipe, data, lang):
    """LANG_NEW [name, desc, alt] for a recipe/language, or None. The raw
    objects are keyed by recipe id first: RAW[rid][lang]."""
    for raw in (data['lang_new_raw'], data['lang_new_raw2'],
                data['lang_new_raw3']):
        per = raw.get(recipe['id'], {})
        arr = per.get(lang)
        if arr:
            return arr
    return None


def _lang_new_serv(recipe, data):
    """Servings count (int) from LANG_NEW_RAW (or the English string)."""
    for raw in (data['lang_new_raw'], data['lang_new_raw2'],
                data['lang_new_raw3']):
        per = raw.get(recipe['id'], {})
        if isinstance(per.get('serv'), int):
            return per['serv']
    m = re.match(r'(\d+)', recipe['servings'] or '')
    return int(m.group(1)) if m else 4


def _lang_new_diff_idx(recipe, data):
    """Difficulty index 0=Easy, 1=Medium, 2=Hard (LANG_NEW_RAW or English)."""
    for raw in (data['lang_new_raw'], data['lang_new_raw2'],
                data['lang_new_raw3']):
        per = raw.get(recipe['id'], {})
        if isinstance(per.get('diff'), int):
            return per['diff']
    return {'Easy': 0, 'Medium': 1, 'Hard': 2}.get(recipe['diff'], 1)


def lang_name(recipe, data, lang):
    arr = _lang_new_arr(recipe, data, lang)
    if arr:
        return arr[0]
    if lang in ('hi', 'ru'):
        tx = data['lang_data'].get(recipe['id'], {}).get(lang, {})
        if tx.get('name'):
            return tx['name']
    return recipe['name']
    if lang in LANG_DATA_LANGS:
        d = data['lang_data'].get(recipe['id'], {}).get(lang, {})
        if d.get('name'):
            return d['name']
    arr = _lang_new_arr(recipe, data, lang)
    if arr and arr[0]:
        return arr[0]
    return recipe['name']


def lang_desc(recipe, data, lang):
    arr = _lang_new_arr(recipe, data, lang)
    if arr:
        return arr[1]
    if lang in ('hi', 'ru'):
        tx = data['lang_data'].get(recipe['id'], {}).get(lang, {})
        if tx.get('desc'):
            return tx['desc']
    return recipe.get('desc', '')
    if lang in LANG_DATA_LANGS:
        d = data['lang_data'].get(recipe['id'], {}).get(lang, {})
        if d.get('desc'):
            return d['desc']
    arr = _lang_new_arr(recipe, data, lang)
    if arr and len(arr) > 1 and arr[1]:
        return arr[1]
    return recipe['desc']


def lang_servings(recipe, data, lang):
    """Servings string in a language (e.g. '4 log' for Roman Urdu).
    Mirrors the SPA's _mergeLangNew(): count + the language's word."""
    if lang == 'en':
        return recipe['servings']
    if lang in LANG_DATA_LANGS:
        d = data['lang_data'].get(recipe['id'], {}).get(lang, {})
        if d.get('servings'):
            return d['servings']
    word = data['sv'].get(lang)
    if word:
        return '%d %s' % (_lang_new_serv(recipe, data), word)
    return recipe['servings']


def lang_diff(recipe, data, lang):
    """Difficulty word in a language (translated). Mirrors _mergeLangNew()."""
    if lang == 'en':
        return recipe['diff']
    if lang in LANG_DATA_LANGS:
        d = data['lang_data'].get(recipe['id'], {}).get(lang, {})
        if d.get('diff'):
            return d['diff']
    words = data['df'].get(lang)
    if words:
        return words[_lang_new_diff_idx(recipe, data)]
    return recipe['diff']


def lang_alt(recipe, data, lang):
    arr = _lang_new_arr(recipe, data, lang)
    if arr:
        return arr[2]
    if lang in ('hi', 'ru'):
        tx = data['lang_data'].get(recipe['id'], {}).get(lang, {})
        if tx.get('alt'):
            return tx['alt']
    return recipe.get('alt') or recipe['name']
    if lang in LANG_DATA_LANGS:
        d = data['lang_data'].get(recipe['id'], {}).get(lang, {})
        if d.get('alt'):
            return d['alt']
    arr = _lang_new_arr(recipe, data, lang)
    if arr and len(arr) > 2 and arr[2]:
        return arr[2]
    return recipe.get('alt') or recipe['name']


def lang_cat_label(recipe, data, lang):
    """Category label in a language (short-form data; English fallback)."""
    if lang == 'en':
        return recipe['catLabel']
    if lang in LANG_DATA_LANGS:
        d = data['lang_data'].get(recipe['id'], {}).get(lang, {})
        if d.get('catLabel'):
            return d['catLabel']
    labels = data['cl'].get(lang, {})
    if recipe['cat'] in labels:
        return labels[recipe['cat']]
    return recipe['catLabel']


def ui_str(data, lang, key, default=''):
    """A UI string in a language (e.g. the 'Ingredients' heading). Patch
    keys (en/ru/hi) are parsed values; the rest are regex-extracted from
    the raw UI literal. Falls back to English, then to default."""
    if lang in data['ui_patches'] and key in data['ui_patches'][lang]:
        v = data['ui_patches'][lang][key]
        if isinstance(v, str):
            return v
    raw = data['ui_raw'].get(lang, '')
    m = re.search(r'\b' + re.escape(key) +
                  r'\s*:\s*(?:"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\')',
                  raw)
    if m:
        return m.group(1) if m.group(1) is not None else m.group(2)
    if lang != 'en':
        return ui_str(data, 'en', key, default)
    return default


def fmt_rate_avg(data, lang, avg, n):
    """The visible '4.6 out of 5 from 12 ratings' line in a language.
    rateAvg holds 'singular|plural' where the language needs it (the
    part before '|' is used for n == 1, the part after for n > 1);
    languages with one form for any count have no '|'. {avg} is the
    1-decimal average, {n} the vote count."""
    s = ui_str(data, lang, 'rateAvg',
               '{avg} out of 5 from {n} rating|{avg} out of 5 from '
               '{n} ratings')
    parts = s.split('|')
    s = parts[0] if n == 1 else (parts[1] if len(parts) > 1 else parts[0])
    return s.replace('{avg}', '%.1f' % avg).replace('{n}', str(n))


def ui_cta(data, lang):
    """The first UI cta label ('Browse Recipes') in a language. The cta
    value is an array, so it is extracted separately from ui_str()."""
    raw = data['ui_raw'].get(lang, '')
    m = re.search(r'\bcta\s*:\s*\[\s*"([^"]+)"', raw)
    if m:
        return m.group(1)
    if lang != 'en':
        return ui_cta(data, 'en')
    return 'Browse Recipes'


def load_recipe_dates():
    """Article + video dates from recipe_dates.json at the repo root (real
    records only). The file lives at the root — NOT under tools/ — because
    tools/ is vercelignored and the Vercel build would not see it (that
    silently dropped all article/video dates from the production build
    on 2026-10-30). Article published = 2026-10-28 for all 32 (the git
    root commit 860a4e7 that first added them — no per-recipe add date
    exists in git history, so no per-recipe modified date is recorded
    either and modified_time is omitted). Video uploadDate = the date that
    recipe's videos went Public, from ~/workspace/food-blog-videos/
    publish-progress.md (per language where the record gives one)."""
    path = os.path.join(ROOT, 'recipe_dates.json')
    if not os.path.exists(path):
        return {'article': {}, 'video': {}}
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def load_nutrition():
    """Per-serving nutrition estimates from nutrition.json at the repo
    root (computed 2026-10-31 from each recipe's REAL ingredient list +
    servings, USDA FoodData Central values — see nutrition-working.md).
    The file lives at the root — NOT under tools/ — for the same reason
    as recipe_dates.json (tools/ is vercelignored). Values are estimates:
    a field that could not be computed is OMITTED from the file (sodium
    for 8 recipes with no salt listed) and is omitted everywhere downstream
    too — never guessed, never zero-filled. Raises if the file is missing
    or a recipe is uncovered, so a bad nutrition file cannot silently
    drop the field from production."""
    path = os.path.join(ROOT, 'nutrition.json')
    if not os.path.exists(path):
        raise JSError("nutrition.json missing from the repo root")
    with open(path, encoding='utf-8') as f:
        nut = json.load(f)
    if not isinstance(nut, dict) or not nut:
        raise JSError("nutrition.json is empty or not an object")
    return nut


def _fetch_kv_ratings():
    """Live rating aggregates from the Vercel KV (Upstash Redis) REST
    API, for the Vercel build. Returns {rid: {'count': n, 'sum': n}} or
    {} on any failure (no env vars, network error, bad response). Never
    raises — the ratings.json snapshot is the fallback, and a ratings
    failure must never break the build. Supports both env-var names:
    KV_REST_API_URL / KV_REST_API_TOKEN (native Vercel KV) and
    UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN (Upstash
    Marketplace integration)."""
    url = (os.environ.get('KV_REST_API_URL')
           or os.environ.get('UPSTASH_REDIS_REST_URL') or '').rstrip('/')
    token = (os.environ.get('KV_REST_API_TOKEN')
             or os.environ.get('UPSTASH_REDIS_REST_TOKEN') or '')
    if not url or not token:
        return {}
    try:
        import urllib.request
        import urllib.error

        def _post(path, body):
            req = urllib.request.Request(
                url + path,
                data=json.dumps(body).encode('utf-8'),
                headers={'Authorization': 'Bearer ' + token,
                         'Content-Type': 'application/json'},
                method='POST')
            with urllib.request.urlopen(req, timeout=5) as resp:
                out = json.load(resp)
            # /pipeline returns a JSON ARRAY, one {result}|{error} per
            # command; single commands return a {result}|{error} object.
            if isinstance(out, list):
                return [x.get('result') if isinstance(x, dict) else None
                        for x in out]
            if out.get('error'):
                raise RuntimeError('KV error: %s' % out['error'])
            return out['result']

        ids = []
        cursor = '0'
        for _ in range(5):
            cursor, keys = _post('', ['SCAN', cursor, 'MATCH',
                                     'rating:*:count', 'COUNT', '100'])
            for k in keys or []:
                if k.startswith('rating:') and k.endswith(':count'):
                    rid = k[len('rating:'):-len(':count')]
                    if rid and all(c.isalnum() or c == '-' for c in rid):
                        ids.append(rid)
            if cursor == '0':
                break
        live = {}
        if ids:
            cmds = []
            for rid in ids:
                cmds.append(['GET', 'rating:%s:sum' % rid])
                cmds.append(['GET', 'rating:%s:count' % rid])
            vals = _post('/pipeline', cmds)
            for i, rid in enumerate(ids):
                live[rid] = {'count': int(vals[i * 2 + 1] or 0),
                             'sum': int(vals[i * 2] or 0)}
        return live
    except Exception as e:
        print('WARNING: live ratings fetch failed (%s); using '
              'ratings.json snapshot' % e, file=sys.stderr)
        return {}


def load_ratings():
    """Real visitor-rating aggregates from ratings.json at the repo root
    (snapshot maintained by tools/refresh_ratings.py from the Vercel KV
    store; never invented). Returns {recipe_id: {'count', 'sum', 'avg',
    'updated'}}. A missing or unreadable file returns {} — a recipe
    with no ratings legitimately has no aggregateRating, and a ratings
    failure must never break the build. When KV credentials are present
    in the environment (Vercel build), live aggregates are fetched and
    merged over the file snapshot with the same never-regress rule as
    the refresh script (max of KV vs snapshot wins)."""
    path = os.path.join(ROOT, 'ratings.json')
    snap = {}
    if os.path.exists(path):
        try:
            with open(path, encoding='utf-8') as f:
                snap = json.load(f) or {}
        except Exception as e:
            print('WARNING: ratings.json unreadable (%s); treating as no '
                  'ratings' % e, file=sys.stderr)
            snap = {}
    if not isinstance(snap, dict):
        snap = {}
    snap = {k: v for k, v in snap.items()
            if isinstance(v, dict) and isinstance(v.get('count'), int)
            and isinstance(v.get('sum'), int) and v['count'] > 0}
    live = _fetch_kv_ratings()
    for rid, vals in live.items():
        old = snap.get(rid) or {}
        count = max(int(vals.get('count') or 0), int(old.get('count') or 0))
        total = max(int(vals.get('sum') or 0), int(old.get('sum') or 0))
        if count <= 0:
            continue
        snap[rid] = {'count': count, 'sum': total,
                     'avg': round(total / count, 1),
                     'updated': old.get('updated') or ''}
    return snap


# ---------------------------------------------------------------------------
# Homepage FAQ (SEO audit round 2, issue P) + hubs/guides (issue O)
# ---------------------------------------------------------------------------
# Real cooking questions from the recipes' own EXTRA.en.faq data, given as
# (recipe id, faq index) so the text is always pulled from the data, never
# copied by hand. The two keyword targets the audit names are both here:
# biryani 0 = "Can I make biryani without saffron?", biryani 2 =
# "Why is my rice sticky?". The two questions that are duplicated across
# recipes ("Can I make the broth ahead?", "Can I use a pressure cooker?")
# are deliberately NOT used. The last entry is the one site-usage question
# kept for new visitors (the language menu) — its text is the existing
# UI.en.faq language answer, verbatim, not a new invention.
HOME_FAQ_RECIPES = [('biryani', 0), ('biryani', 2), ('nihari', 0),
                    ('karahi', 0), ('samosa', 0), ('gulabjamun', 0),
                    ('gulabjamun', 1), ('carbonara', 1), ('pizza', 0)]
HOME_FAQ_USAGE = (
    "Can I read recipes in other languages?",
    "Yes. Use the language menu at the top. Full recipe detail is "
    "translated in all 13 languages: English, Roman Urdu, Hindi, Spanish, "
    "French, Arabic, Portuguese, Russian, Chinese, Japanese, German, "
    "Turkish and Bengali, with ingredients and the step by step method in "
    "each language.")


def _faq_lang(data, lang):
    """A recipe's EXTRA faq list in a language. en/hi/ru come from EXTRA
    as objects; the other 10 from EXTRA_NEW arrays (already normalized)."""
    if lang in EXTRA_OBJ_LANGS or lang == 'en':
        return lambda rid: (data['extra'].get(rid, {}).get(lang, {})
                            .get('faq') or [])
    return lambda rid: (data['extra_new'].get(lang, {})
                        .get(rid, {}).get('faq') or [])


# Words for "language(s)" per language, used to find the language-menu
# question inside each language's existing UI faq (it is the one site-
# usage question kept in the homepage FAQ).
LANG_WORD = {'en': 'language', 'ru': 'zaban', 'hi': 'भाषा', 'es': 'idioma',
             'fr': 'langue', 'ar': 'لغ', 'pt': 'idioma', 'rus': 'язык',
             'zh': '语言', 'ja': '言語', 'de': 'Sprach', 'tr': 'dil',
             'bn': 'ভাষা'}


def ui_faq_entries(data, lang):
    """The existing UI faq entries [[q, a], ...] for a language, parsed
    from the UI literal (en/ru/hi may also carry patch keys, but 'faq'
    is in the literal for all 13)."""
    raw = data['ui_raw'].get(lang, '')
    m = re.search(r'\bfaq\s*:\s*\[', raw)
    if not m:
        return []
    try:
        val, _ = parse_js_literal(raw, raw.find('[', m.start()))
    except Exception:
        return []
    return val if isinstance(val, list) else []


def lang_menu_faq(data, lang):
    """The language-menu question from a language's existing UI faq
    (the one site-usage question kept in the homepage FAQ). Falls back
    to the English entry."""
    word = LANG_WORD.get(lang, 'language')
    for q, a in ui_faq_entries(data, lang):
        if word in q:
            return (q, a)
    for q, a in ui_faq_entries(data, 'en'):
        if 'language' in q:
            return (q, a)
    return HOME_FAQ_USAGE


def home_faq_entries(data, lang='en'):
    """The homepage /faqs FAQ entries: [(question, answer)] in a
    language. 9 cooking Q&As verbatim from the recipes' EXTRA faq data
    (same recipe/index pairs in every language) + the language-menu
    question from that language's existing UI faq."""
    out = []
    get_faq = _faq_lang(data, lang)
    for rid, idx in HOME_FAQ_RECIPES:
        faq = get_faq(rid)
        if idx < len(faq):
            out.append((faq[idx][0], faq[idx][1]))
    out.append(lang_menu_faq(data, lang))
    return out


# Seasonal hubs (issue O): curated lists from the real 46 recipes only.
# No dish is invented; each recipe is listed with the reason it fits.
# The 3 trending dishes on the homepage (the UI trendCards:
# Chicken Biryani, Beef Nihari, Gulab Jamun). --check verifies these
# still match the UI trendCards names.
TREND_IDS = ['biryani', 'nihari', 'gulabjamun']

HUBS = {
    'eid-recipes': {
        'title': 'Eid Recipes',
        'intro': ("Eid food from Zaika Worlds: festive mains, barbecue and "
                  "sweets from the recipes on this site. Biryani and nihari "
                  "for the main table, chapli kabab and chicken tikka from "
                  "the barbecue, gulab jamun and gajar ka halwa for sweet, "
                  "and halwa puri, samosa, bun kebab and mango lassi to "
                  "share through the day."),
        'recipes': ['biryani', 'nihari', 'karahi', 'chapli', 'tikka',
                    'halwapuri', 'gulabjamun', 'gajarhalwa', 'samosa',
                    'bunkebab', 'lassi'],
    },
    'ramadan-recipes': {
        'title': 'Ramadan Recipes',
        'intro': ("Ramadan food from Zaika Worlds: iftar and sehri dishes "
                  "from the recipes on this site. Samosa and bun kebab for "
                  "iftar, daal fry and chapli kabab for the main meal, "
                  "halwa puri for sehri, mango lassi to drink, and gulab "
                  "jamun and gajar ka halwa for sweet after iftar."),
        'recipes': ['daal', 'samosa', 'bunkebab', 'chapli', 'tikka',
                    'halwapuri', 'lassi', 'gulabjamun', 'gajarhalwa',
                    'biryani', 'nihari', 'karahi'],
    },
}


def dum_guide_sections(data):
    """The dum-cooking guide (issue O): real tips/notes/steps from the
    biryani, karahi and nihari recipe data, attributed to each recipe.
    Returns [(heading, [paragraphs])]."""
    def tx(rid):
        r = next(x for x in data['recipes'] if x['id'] == rid)
        return r_text_en(r, data['extra'])
    b, k, n = tx('biryani'), tx('karahi'), tx('nihari')
    return [
        ("What dum cooking is", [
            "Dum is cooking sealed on low heat, so the steam stays in the "
            "pot and finishes the dish. The Chicken Biryani recipe puts it "
            "plainly: the rice finishes cooking on dum, and a cloth over "
            "the lid stops the steam escaping.",
        ]),
        ("Biryani on dum", [
            "From the Chicken Biryani recipe: do not over-boil the rice, "
            "because it finishes cooking on dum. Seal the lid with a cloth "
            "or foil, cook on low heat on dum for 20 minutes without "
            "opening the lid, then rest for 10 minutes off the heat. "
            "Chicken on the bone stays juicier during dum, and aged "
            "basmati gives separate grains.",
        ]),
        ("Karahi on dum", [
            "From the Chicken Karahi recipe: sprinkle garam masala, cover, "
            "and give 5 minutes of dum on low heat. The chicken should be "
            "cooked through and still juicy. Do not add water to karahi: "
            "the tomatoes' own water is enough.",
        ]),
        ("Slow cooking like nihari", [
            "From the Beef Nihari recipe: cover the pot and cook on low "
            "heat for 2 hours, stirring now and then, and add hot water if "
            "the level drops below the meat. Nihari is known for its "
            "thick, glossy gravy, so add the flour slowly and stir "
            "constantly while it goes in.",
        ]),
        ("What to remember", [
            "Seal the lid, keep the heat low, and do not open the pot "
            "while it is on dum. Rest the dish before serving, and taste "
            "the rice water before the dum: it should taste slightly "
            "salty, because plain rice needs that seasoning.",
        ]),
    ]




# ---------------------------------------------------------------------------
# JS literal parser (stdlib only). Handles double/single-quoted strings with
# escapes, unquoted identifier keys, trailing commas, numbers, true/false/null.
# ---------------------------------------------------------------------------

class JSError(Exception):
    pass


_IDENT = re.compile(r'[A-Za-z_$][A-Za-z0-9_$]*')


def _skip_ws(text, p):
    n = len(text)
    while p < n and text[p] in ' \t\r\n':
        p += 1
    return p


def _parse_string(text, p):
    q = text[p]
    out = []
    i = p + 1
    n = len(text)
    while i < n:
        c = text[i]
        if c == '\\' and i + 1 < n:
            nxt = text[i + 1]
            mapping = {'n': '\n', 't': '\t', 'r': '\r', 'b': '\b', 'f': '\f',
                       'v': '\v', '0': '\0'}
            if nxt in mapping:
                out.append(mapping[nxt])
            elif nxt == 'u' and i + 5 < n:
                try:
                    out.append(chr(int(text[i + 2:i + 6], 16)))
                except ValueError:
                    raise JSError("bad \\u escape at %d" % i)
                i += 6
                continue
            elif nxt == 'x' and i + 3 < n:
                try:
                    out.append(chr(int(text[i + 2:i + 4], 16)))
                except ValueError:
                    raise JSError("bad \\x escape at %d" % i)
                i += 4
                continue
            else:
                out.append(nxt)
            i += 2
            continue
        if c == q:
            return ''.join(out), i + 1
        if c == '\n':
            raise JSError("unterminated string at %d" % p)
        out.append(c)
        i += 1
    raise JSError("unterminated string at %d" % p)


def parse_js_literal(text, pos=0):
    """Parse one JS value starting at/after pos. Returns (value, endpos)."""
    p = _skip_ws(text, pos)
    if p >= len(text):
        raise JSError("unexpected end of input")
    c = text[p]
    if c == '{':
        return _parse_object(text, p)
    if c == '[':
        return _parse_array(text, p)
    if c in '"\'':
        return _parse_string(text, p)
    if c.isdigit() or c in '+-.':
        m = re.match(r'[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?', text[p:])
        if not m:
            raise JSError("bad number at %d" % p)
        num = m.group(0)
        return (float(num) if ('.' in num or 'e' in num or 'E' in num)
                else int(num)), p + len(num)
    m = _IDENT.match(text, p)
    if m:
        w = m.group(0)
        if w == 'true':
            return True, p + 4
        if w == 'false':
            return False, p + 5
        if w == 'null':
            return None, p + 4
        if w == 'undefined':
            return None, p + 9
        raise JSError("bare identifier %r at %d" % (w, p))
    raise JSError("unexpected char %r at %d" % (c, p))


def _parse_object(text, p):
    obj = {}
    i = _skip_ws(text, p + 1)
    n = len(text)
    if i < n and text[i] == '}':
        return obj, i + 1
    while True:
        i = _skip_ws(text, i)
        if i >= n:
            raise JSError("unterminated object at %d" % p)
        c = text[i]
        if c in '"\'':
            key, i = _parse_string(text, i)
        else:
            m = _IDENT.match(text, i)
            if not m:
                raise JSError("bad object key at %d" % i)
            key = m.group(0)
            i += len(key)
        i = _skip_ws(text, i)
        if i >= n or text[i] != ':':
            raise JSError("expected ':' after key at %d" % i)
        val, i = parse_js_literal(text, i + 1)
        obj[key] = val
        i = _skip_ws(text, i)
        if i < n and text[i] == ',':
            i += 1
            i = _skip_ws(text, i)
            if i < n and text[i] == '}':
                return obj, i + 1
            continue
        if i < n and text[i] == '}':
            return obj, i + 1
        raise JSError("expected ',' or '}' at %d" % i)


def _parse_array(text, p):
    arr = []
    i = _skip_ws(text, p + 1)
    n = len(text)
    if i < n and text[i] == ']':
        return arr, i + 1
    while True:
        val, i = parse_js_literal(text, i)
        arr.append(val)
        i = _skip_ws(text, i)
        if i < n and text[i] == ',':
            i += 1
            i = _skip_ws(text, i)
            if i < n and text[i] == ']':
                return arr, i + 1
            continue
        if i < n and text[i] == ']':
            return arr, i + 1
        raise JSError("expected ',' or ']' at %d" % i)


def raw_braced(text, start):
    """Return the raw {...} or [...] text starting at/after start.

    String-aware brace matching only; does NOT parse values, so function
    values and other non-JSON JS are preserved verbatim. Returns (raw, end).
    """
    p = _skip_ws(text, start)
    if p >= len(text) or text[p] not in '{[':
        raise JSError("no literal at %d" % start)
    open_c, close_c = text[p], ('}' if text[p] == '{' else ']')
    depth = 0
    instr = False
    esc = False
    q = None
    i = p
    n = len(text)
    while i < n:
        c = text[i]
        if instr:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == q:
                instr = False
        else:
            if c in '"\'':
                instr = True
                q = c
            elif c == open_c:
                depth += 1
            elif c == close_c:
                depth -= 1
                if depth == 0:
                    return text[p:i + 1], i + 1
        i += 1
    raise JSError("unterminated literal at %d" % p)


def find_literal(src, anchor, opener='{'):
    """Find anchor, then the first opener after it; return (raw, start, end)."""
    i = src.find(anchor)
    if i < 0:
        raise JSError("anchor not found: %r" % anchor)
    j = src.find(opener, i)
    if j < 0:
        raise JSError("no %r after %r" % (opener, anchor))
    raw, end = raw_braced(src, j)
    return raw, j, end


def parse_literal(src, anchor, opener='{'):
    raw, _, _ = find_literal(src, anchor, opener)
    val, _ = parse_js_literal(raw)
    return val


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def esc(s):
    """HTML-escape text content / attribute values."""
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def cap_title(name):
    """Same capping rule as setRouteMeta(): '<name> | Zaika Worlds', <=60."""
    title = name + " | Zaika Worlds"
    if len(title) > 60:
        title = name[:44] + " | Zaika Worlds"
    return title


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def js_json(obj):
    """Compact JSON for data files (ensure_ascii=False keeps UTF-8 text)."""
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


# ---------------------------------------------------------------------------
# Extraction: parse every data block out of index.html
# ---------------------------------------------------------------------------

def extract_all(src):
    """Parse all data blocks from the fat index.html. Returns a dict."""
    if SLIM_MARKER in src:
        raise JSError("index.html already looks slim (marker %s present); "
                      "refusing to re-run on a slim file" % SLIM_MARKER)
    for anchor in ('var RECIPES=[', 'var EXTRA={', 'var LANG_DATA={',
                   'var UI={', 'var INFO={', 'var EXTRA_NEW={'):
        if anchor not in src:
            raise JSError("expected data anchor missing: %r — is this the "
                          "fat index.html?" % anchor)

    recipes = parse_literal(src, 'var RECIPES=[', '[')
    extra = parse_literal(src, 'var EXTRA={')
    lang_data = parse_literal(src, 'var LANG_DATA={')
    info = parse_literal(src, 'var INFO={')
    img_dims = parse_literal(src, 'IMG_DIMS=')
    # Short-form text for the 10 non-hi/ru languages (name/desc/alt per
    # recipe, plus cat/diff/serv), merged into LANG_DATA at load by the
    # LANG_NEW_ALL loop. These are data blocks, not app code.
    lang_new_raw = parse_literal(src, 'var LANG_NEW_RAW=')
    lang_new_raw2 = parse_literal(src, 'var LANG_NEW_RAW2=')
    lang_new_raw3 = parse_literal(src, 'var LANG_NEW_RAW3=')

    # Lookups used by listInfo() (small, pure data).
    cat_by_slug = parse_literal(src, 'var CAT_BY_SLUG=')
    cat_title = parse_literal(src, 'var CAT_TITLE=')
    list_lead = parse_literal(src, 'var LIST_LEAD=')
    country_by_slug = parse_literal(src, 'var COUNTRY_BY_SLUG=')
    country_adj = parse_literal(src, 'var COUNTRY_ADJ=')
    cat_slug = parse_literal(src, 'var CAT_SLUG=')
    country_slug = parse_literal(src, 'var COUNTRY_SLUG=')

    # Short-form translations for the 10 LANG_NEW languages (used by the
    # _mergeLangNew() loop): _CL[lang][cat] category labels,
    # _DF[lang][0|1|2] difficulty words, _SV[lang] servings word.
    cl = parse_literal(src, 'var _CL=')
    df = parse_literal(src, 'var _DF=')
    sv = parse_literal(src, 'var _SV=')

    # UI: raw per-language objects (the `results` value is a JS function, so
    # UI must be carried as raw text, not parsed). Initial literal holds
    # en/ru/hi; the other 10 languages are UI.<lang>={...} assignments.
    ui_raw = {}
    ui_lit_raw, _, _ = find_literal(src, 'var UI={')
    for lang in ('en', 'ru', 'hi'):
        i = ui_lit_raw.find(lang + ':{')
        if i < 0:
            raise JSError("UI.%s not found in initial literal" % lang)
        raw, _ = raw_braced(ui_lit_raw, ui_lit_raw.find('{', i))
        ui_raw[lang] = raw
    for m in re.finditer(r'UI\.([a-z]+)\s*=\s*\{', src):
        lang = m.group(1)
        raw, _ = raw_braced(src, src.find('{', m.start()))
        ui_raw[lang] = raw

    # UI patch statements: UI.<lang>.<key>=<value>; for en/ru/hi only.
    # The initial literal lacks 26 keys (servingH, countries, recipesT, ...)
    # that the 10 other languages' assignments already contain; these
    # statements add them after the literal. They must move into the
    # per-language UI data files (as UI.en.<key>= / ZAIKA_UI_<LANG>.<key>=).
    ui_patches = {}   # lang -> {key: value}
    ui_patch_spans = []  # (start, end) of each patch statement
    for m in re.finditer(r'UI\.(en|ru|hi)\.([A-Za-z0-9_]+)\s*=\s*', src):
        val, v_end = parse_js_literal(src, m.end())
        semi = src.find(';', v_end)
        if semi < 0:
            raise JSError("no ';' after UI patch at %d" % m.start())
        ui_patches.setdefault(m.group(1), {})[m.group(2)] = val
        ui_patch_spans.append((m.start(), semi + 1))

    # UI "min" word per language (the translated word for "minute", used
    # by the SPA's minuteWord() and by language meta descriptions).
    ui_min = {}
    for lang, raw in ui_raw.items():
        m = re.search(r'\bmin\s*:\s*"([^"]+)"', raw)
        if m:
            ui_min[lang] = m.group(1)

    # EXTRA_NEW: per-language arrays -> normalized 10-key objects.
    # Initial literal holds es/fr (4 recipes each); es/fr/ar/pt add 30-36
    # per-recipe assignments (bracket notation for hyphenated ids, e.g.
    # EXTRA_NEW.es["seekh-kebab"]=[...]); bn/de/ja/rus/tr/zh are whole-language literals.
    en_raw = {}
    init_raw, _, _ = find_literal(src, 'var EXTRA_NEW={')
    for lang in ('es', 'fr'):
        i = init_raw.find(lang + ':{')
        if i < 0:
            raise JSError("EXTRA_NEW.%s not found in initial literal" % lang)
        raw, _ = raw_braced(init_raw, init_raw.find('{', i))
        sub, _ = parse_js_literal(raw)
        en_raw[lang] = sub
    for m in re.finditer(r'EXTRA_NEW\.([a-z]+)(?:\.([a-z0-9_-]+)|\["([a-z0-9_-]+)"\])\s*=\s*\[', src):
        lang, rid = m.group(1), m.group(2) or m.group(3)
        raw, _ = raw_braced(src, m.end() - 1)  # match ends on the array '['
        arr, _ = parse_js_literal(raw)
        en_raw.setdefault(lang, {})[rid] = arr
    for m in re.finditer(r'EXTRA_NEW\.([a-z]+)\s*=\s*\{', src):
        lang = m.group(1)
        raw, _ = raw_braced(src, src.find('{', m.start()))
        sub, _ = parse_js_literal(raw)
        if sub:  # skip the empty EXTRA_NEW.ar={} / .pt={} initialisers
            en_raw[lang] = sub
    extra_new = {}
    for lang, per_recipe in en_raw.items():
        out = {}
        for rid, arr in per_recipe.items():
            if not isinstance(arr, list) or len(arr) != len(EXTRA_KEYS):
                raise JSError("EXTRA_NEW.%s.%s: expected a %d-element array, "
                              "got %r" % (lang, rid, len(EXTRA_KEYS),
                                          len(arr) if isinstance(arr, list)
                                          else type(arr)))
            out[rid] = dict(zip(EXTRA_KEYS, arr))
        extra_new[lang] = out

    data = {
        'recipes': recipes, 'extra': extra, 'lang_data': lang_data,
        'info': info, 'img_dims': img_dims, 'ui_raw': ui_raw,
        'ui_patches': ui_patches, 'ui_min': ui_min,
        'extra_new': extra_new,
        'lang_new_raw': lang_new_raw, 'lang_new_raw2': lang_new_raw2,
        'lang_new_raw3': lang_new_raw3,
        'cat_by_slug': cat_by_slug, 'cat_title': cat_title,
        'list_lead': list_lead, 'country_by_slug': country_by_slug,
        'country_adj': country_adj, 'cat_slug': cat_slug,
        'country_slug': country_slug, 'cl': cl, 'df': df, 'sv': sv,
    }
    # Visible publish dates (issue #15): every recipe carries its real
    # article published date from recipe_dates.json, so the SPA
    # (data/recipes.js) and the static builders share one source. A
    # recipe with no recorded date gets no 'published' field and shows
    # no date, rather than an invented one.
    _dates = load_recipe_dates()
    _art = _dates.get('article') or {}
    for _r in recipes:
        _a = _art.get(_r['id']) or {}
        if _a.get('published'):
            _r['published'] = _a['published']
    # Per-serving nutrition (GSC 'Missing field "nutrition"', 2026-10-31):
    # computed from the real ingredient lists (nutrition.json, USDA
    # values); a recipe with no entry gets no nutrition anywhere —
    # never invented. data['nutrition'] is shared by the static
    # builders and the SPA (data/recipes.js carries it as NUTRITION).
    data['nutrition'] = load_nutrition()
    # Real visitor ratings (GSC 'Missing field "aggregateRating"',
    # 2026-11-02): snapshot from ratings.json, refreshed daily from the
    # Vercel KV store by tools/refresh_ratings.py (never invented; a
    # recipe with no entry has no aggregateRating anywhere). Shared by
    # the static builders and the SPA (data/recipes.js carries it as
    # RATINGS).
    data['ratings'] = load_ratings()
    validate(data)
    return data


def validate(data):
    """Sanity checks: counts, coverage, required fields. Fail loudly."""
    recipes = data['recipes']
    ids = [r['id'] for r in recipes]
    if len(set(ids)) != len(recipes):
        raise JSError("duplicate recipe ids")
    for r in recipes:
        for k in ('id', 'name', 'country', 'cat', 'catLabel', 'time',
                  'servings', 'img', 'desc', 'intro', 'ing', 'steps', 'tip'):
            if k not in r:
                raise JSError("recipe %s missing %r" % (r.get('id'), k))
    # Nutrition coverage (GSC 'Missing field "nutrition"', 2026-10-31):
    # every recipe must have a computed per-serving entry with at least
    # calories, protein, fat and carbs. A missing entry is a build
    # failure, not a silent omission — the field must never disappear
    # from production unnoticed.
    nut = data.get('nutrition') or {}
    for r in recipes:
        n = nut.get(r['id'])
        if not n:
            raise JSError("recipe %s missing nutrition data" % r['id'])
        for k in ('calories', 'proteinContent', 'fatContent',
                  'carbohydrateContent'):
            if k not in n:
                raise JSError("recipe %s nutrition missing %r"
                              % (r['id'], k))
        if not r['ing'] or not r['steps']:
            raise JSError("recipe %s has empty ing/steps" % r['id'])
    for lang in EXTRA_OBJ_LANGS:
        have = {rid for rid, d in data['extra'].items() if lang in d}
        # allow incremental recipes without full EXTRA
        pass
    for lang in EXTRA_NEW_LANGS:
        have = set(data['extra_new'].get(lang, {}))
        # allow incremental recipes without full EXTRA_NEW
        pass
    for lang in LANGS:
        if lang not in data['ui_raw']:
            raise JSError("UI.%s missing" % lang)
        if lang not in data['info']:
            raise JSError("INFO.%s missing" % lang)
    # UI patches: en/ru/hi each gain the same 26 keys after the literal.
    for lang in ('en', 'ru', 'hi'):
        keys = set(data['ui_patches'].get(lang, {}))
        if len(keys) != 27:
            raise JSError("UI.%s patches: %d keys, expected 27"
                          % (lang, len(keys)))
    if set(data['ui_patches']) != {'en', 'ru', 'hi'}:
        raise JSError("UI patches cover %s, expected en/ru/hi"
                      % sorted(data['ui_patches']))
    for lang in LANG_DATA_LANGS:
        have = {rid for rid, d in data['lang_data'].items() if lang in d}
        # allow incremental recipes without full LANG_DATA
        pass
    # LANG_NEW_RAW* cover the other 10 languages (short-form name/desc/alt).
    expect = {'LANG_NEW_RAW': {'es', 'fr', 'ar'},
              'LANG_NEW_RAW2': {'pt', 'rus', 'zh'},
              'LANG_NEW_RAW3': {'bn', 'de', 'ja', 'tr'}}
    for key, langs in expect.items():
        raw = data[key.lower()]
        # allow incremental recipes without full LANG_NEW
        pass
        have = {L for d in raw.values() for L in d
                if L not in ('cat', 'diff', 'serv')}
        if have != langs:
            raise JSError("%s langs %s, expected %s"
                          % (key, sorted(have), sorted(langs)))
        for rid, d in raw.items():
            for lang in langs:
                if not isinstance(d.get(lang), list) or len(d[lang]) != 3:
                    raise JSError("%s.%s.%s: expected a 3-element array"
                                  % (key, rid, lang))
    if len(data['cat_by_slug']) != 11 or len(data['country_by_slug']) != 25:
        raise JSError("expected 11 categories / 25 countries, got %d / %d"
                      % (len(data['cat_by_slug']),
                         len(data['country_by_slug'])))


def r_text_en(recipe, extra):
    """English long-form text for a recipe (what rText() returns for en)."""
    out = dict(recipe)  # base fields: desc, intro, ing, steps, tip, alt...
    en = extra.get(recipe['id'], {}).get('en', {})
    for k, v in en.items():
        out[k] = v
    return out


def join_names(recipes):
    """Same as joinNames(): 'A, B and C'."""
    names = [r['name'] for r in recipes]
    s = ', '.join(names)
    return re.sub(r', ([^,]*)$', r' and \1', s)


def fit_long(base, extras):
    """Fit a description to 140-155 chars from real text: start with base,
    append extra sentences (in order) until >=140, then trim to <=155 at a
    word boundary. Returns the fitted text (may be <140 if the real text
    runs out — callers report that)."""
    d = (base or '').strip()
    if d and d[-1] not in SENT_END:
        d += '.'
    for ex in extras or []:
        if len(d) >= 140:
            break
        s = (ex or '').strip()
        if not s:
            continue
        if s[-1] not in SENT_END:
            s += '.'
        if len(d) + 1 + len(s) <= 155:
            d = d + ' ' + s
        else:
            room = 155 - len(d) - 1
            if room > 30:
                cut = s[:room]
                sp = cut.rfind(' ')
                if sp > 20:
                    cut = cut[:sp]
                cut = cut.rstrip(' ,;:')
                if cut and cut[-1] not in SENT_END:
                    cut += '.'
                d = d + ' ' + cut
    if len(d) > 155:
        d = fit_desc(d, '')
    return d


def list_info(data, kind, slug):
    """Mirror listInfo() for English: label/title/desc/intro/recipes/img.
    Country intros are unique per country (recipe names + the first
    recipe's own description); descriptions are fitted to 140-155 chars."""
    recipes = data['recipes']
    if kind == 'category':
        cat = data['cat_by_slug'].get(slug)
        if not cat:
            return None
        rs = [r for r in recipes if r['cat'] == cat]
        label = rs[0]['catLabel'] if rs else cat
        title = data['cat_title'].get(cat) or (label + ' Recipes')
        lead = data['list_lead'].get('category/' + slug) or \
            ('Recipes from the ' + label + ' collection.')
    elif kind == 'country':
        country = data['country_by_slug'].get(slug)
        if not country:
            return None
        rs = [r for r in recipes if r['country'] == country]
        label = country
        title = data['country_adj'][country] + ' Recipes'
        lead = 'Dishes from ' + country + '.'
    else:
        return None
    if not rs:
        return None
    n = len(rs)
    names = join_names(rs)
    t = title[:-len(' Recipes')] + ' Recipe' if n == 1 else title
    base_desc = ('%d %s with full ingredients and step by step methods'
                 % (n, t))
    if n <= 7:
        base_desc += ': ' + names
    elif kind == 'category':
        base_desc += ' from %d countries' % len({r['country'] for r in rs})
    base_desc += '.'
    if len(base_desc) > 155:
        # A long name list (Pakistan, 7 recipes) does not fit: drop the
        # names from the base and let the appended sentences fill it.
        base_desc = ('%d %s with full ingredients and step by step methods.'
                     % (n, t))
    first = rs[0]
    ftx = r_text_en(first, data['extra'])
    # Description: base + the lead sentence (category) or the first
    # recipe's own description (country), fitted to 140-155.
    if kind == 'category':
        desc = list_desc(base_desc, [lead, first_sentence(ftx.get('desc')),
                                     first_sentence(ftx.get('intro'))])
    else:
        desc = list_desc(base_desc, [first_sentence(ftx.get('desc')),
                                     first_sentence(ftx.get('intro'))])
    parts = [lead]
    if kind == 'country':
        # Unique intro: the recipe names plus the first recipe's own
        # description sentence (different for every country).
        parts.append(first_sentence(ftx.get('desc')))
    if n == 1:
        parts.append('The recipe on this page is ' + names + '.')
    elif n <= 7:
        parts.append('Recipes on this page: ' + names + '.')
    parts.append('Each recipe lists full ingredients, a step by step method, '
                 'cooking time and servings.')
    hub_img, hub_alt, _ = hub_og(data, '/' + kind + '/' + slug, rs)
    return {'kind': kind, 'slug': slug, 'label': label, 'title': title,
            'desc': desc, 'intro': ' '.join(parts), 'recipes': rs,
            'img': hub_img,
            'imgAlt': hub_alt,
            'url': SITE + '/' + kind + '/' + slug}


# ---------------------------------------------------------------------------
# Data files (data/*.js)
# ---------------------------------------------------------------------------

def _split_ing_obj(obj, lang):
    """Return a copy of an EXTRA-style {rid: {lang: fields}} dict with the
    'ing' list split one-per-line (issue G). The source index.html keeps
    the original combined strings; the split is a build-time transform,
    so it applies to every deploy (including new recipes)."""
    out = {}
    for rid, langs in obj.items():
        out[rid] = {}
        for lg, fields in langs.items():
            f = dict(fields)
            if f.get('ing'):
                f['ing'] = split_ingredients(f['ing'], lg)
            out[rid][lg] = f
    return out


def write_data_files(data):
    """Write the lazily-loaded data files. Returns {path: bytes}."""
    out = {}

    def w(rel, text):
        path = os.path.join(ROOT, 'data', rel)
        write(path, text)
        out[rel] = len(text.encode('utf-8'))

    # Core (English) — recipes.js + ui-en.js load on every visit; extra-en.js
    # is lazy-loaded by the SPA on first recipe open (_ensureExtra in
    # LOADER_JS), so the 152 KB long-form text is not on the critical path.
    # recipes.js also carries NUTRITION (per-serving values, nutrition.json)
    # so the SPA's client-side JSON-LD and recipe view share the static
    # pages' single source of truth.
    w('recipes.js', 'var RECIPES=' + js_json(data['recipes']) + ';\n'
                    'var NUTRITION='
                    + js_json(data.get('nutrition') or {}) + ';\n'
                    'var RATINGS='
                    + js_json(data.get('ratings') or {}) + ';\n')
    # Flat {rid: fields} (like the other languages): _mergeExtraLang
    # assigns EXTRA[rid].en = obj[rid], so the {en:} wrapper the old
    # `var EXTRA=` format needed would double-nest and hide the text.
    extra_en = {rid: d['en'] for rid, d in data['extra'].items()
                if 'en' in d}
    split_en = {}
    for rid, fields in extra_en.items():
        f = dict(fields)
        if f.get('ing'):
            f['ing'] = split_ingredients(f['ing'], 'en')
        split_en[rid] = f
    w('extra-en.js', 'var ZAIKA_EXTRA_EN=' + js_json(split_en) + ';\n')
    en_patches = ''.join('UI.en.%s=%s;\n' % (k, js_json(v))
                         for k, v in sorted(data['ui_patches']['en'].items()))
    w('ui-en.js',
      'var UI={en:' + data['ui_raw']['en'] + '};\n'
      'var INFO={en:' + js_json(data['info']['en']) + '};\n'
      + en_patches)

    # Per-language long-form text (12 files). hi/ru come from EXTRA as
    # objects; the other 10 come from EXTRA_NEW arrays (already normalized).
    for lang in LANGS:
        if lang == 'en':
            continue
        if lang in EXTRA_OBJ_LANGS:
            obj = {rid: d[lang] for rid, d in data['extra'].items()
                   if lang in d}
        else:
            obj = data['extra_new'][lang]
        # obj is {rid: fields}; split its ing list for this language.
        split_obj = {}
        for rid, fields in obj.items():
            f = dict(fields)
            if f.get('ing'):
                f['ing'] = split_ingredients(f['ing'], lang)
            split_obj[rid] = f
        w('extra-%s.js' % lang,
          'var ZAIKA_EXTRA_' + lang.upper() + '=' + js_json(split_obj)
          + ';\n')

    # Per-language UI + INFO strings (12 files). UI is raw JS (it contains
    # a `results` function per language); INFO is JSON. For ru/hi, the 26
    # patch keys are applied to the ZAIKA_UI_<LANG> object (the loader then
    # assigns the whole object to UI.<lang>).
    for lang in LANGS:
        if lang == 'en':
            continue
        text = ('var ZAIKA_UI_' + lang.upper() + '=' + data['ui_raw'][lang]
                + ';\n'
                'var ZAIKA_INFO_' + lang.upper() + '='
                + js_json(data['info'][lang]) + ';\n')
        if lang in data['ui_patches']:
            text += ''.join('ZAIKA_UI_%s.%s=%s;\n'
                            % (lang.upper(), k, js_json(v))
                            for k, v in
                            sorted(data['ui_patches'][lang].items()))
        w('ui-%s.js' % lang, text)

    # Short-form LANG_DATA (hi/ru only).
    for lang in LANG_DATA_LANGS:
        obj = {rid: d[lang] for rid, d in data['lang_data'].items()
               if lang in d}
        split_obj = {}
        for rid, fields in obj.items():
            f = dict(fields)
            if f.get('ing'):
                f['ing'] = split_ingredients(f['ing'], lang)
            split_obj[rid] = f
        w('lang-data-%s.js' % lang,
          'var ZAIKA_LANGDATA_' + lang.upper() + '=' + js_json(split_obj)
          + ';\n')

    # Short-form text for the other 10 languages (merged into LANG_DATA by
    # _mergeLangNew() after load). Kept as the three original objects so the
    # merge code is unchanged.
    w('lang-new.js',
      'var LANG_NEW_RAW=' + js_json(data['lang_new_raw']) + ';\n'
      'var LANG_NEW_RAW2=' + js_json(data['lang_new_raw2']) + ';\n'
      'var LANG_NEW_RAW3=' + js_json(data['lang_new_raw3']) + ';\n')
    return out


# ---------------------------------------------------------------------------
# Static SEO pages
# ---------------------------------------------------------------------------

STATIC_CSS = '''
:root{
  --bg:#faf3e7; --surface:#fffdf8; --surface2:#f6e9d6; --ink:#2b241d; --muted:#77614e;
  --line:#e7d5ba; --red:#b84f28; --red-dark:#96401f; --orange:#d96c3f; --green:#357a4e;
  --gold:#c07a1a; --chip:#f9e8d2; --shadow:0 14px 32px rgba(68,38,18,.14);
  --radius:20px;
  --header-bg:#23201c; --header-surface:#2d2923; --header-ink:#f6ead9; --header-muted:#c6b49c;
  --header-line:#4a4237; --accent:#d96c3f; --accent-ink:#fff6ea;
}
@media (prefers-color-scheme: dark){
  :root{ --bg:#23201c; --surface:#2d2923; --surface2:#3a342c; --ink:#f6ead9; --muted:#c6b49c;
  --line:#4a4237; --red:#e07a4e; --red-dark:#ec8f63; --orange:#e07a4e; --chip:#3a342c; --shadow:0 14px 32px rgba(0,0,0,.45);
  --header-bg:#1b1814; --header-surface:#26221c; --header-ink:#f6ead9; --header-muted:#c6b49c;
  --header-line:#4a4237; --accent:#e07a4e; --accent-ink:#fff6ea; }
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Source Sans 3","Plus Jakarta Sans",system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.6}
img{max-width:100%;display:block}
a{color:var(--red)}

h1,h2,h3{font-family:"Cormorant Garamond",Georgia,serif;font-weight:600;line-height:1.08;letter-spacing:.1px}
h1{font-size:clamp(36px,5vw,52px);margin:14px 0 16px}
h2,h3{font-size:26px;margin:22px 0 10px}
p{margin:0 0 14px}

.wrap{max-width:1180px;margin:0 auto;padding:0 18px}
.recipe-view{padding:20px 0 40px}
.recipe-body{max-width:820px;margin:0 auto}

/* Topbar Header */
header.topbar-modern{background:var(--header-bg);color:var(--header-ink);border-bottom:1px solid var(--header-line);margin:0;padding:0;width:100%}
.topbar-inner{max-width:1180px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:12px 18px}
header.topbar-modern a.brand{font-family:"Cormorant Garamond",Georgia,serif;font-size:32px;font-weight:600;color:var(--header-ink);text-decoration:none;display:inline-flex;align-items:center;gap:10px;white-space:nowrap;letter-spacing:.02em}
header.topbar-modern a.brand span{color:var(--accent);font-weight:600}
header.topbar-modern .logo-img{width:44px;height:44px;border-radius:50%;object-fit:cover;flex:none}
.lang-wrap{display:flex;align-items:center;gap:6px}
.globe-icon{color:var(--accent);font-size:16px}
.lang-select{background:var(--header-surface);color:var(--header-ink);border:1px solid var(--header-line);border-radius:10px;padding:8px 10px;font-size:14px;font-weight:600;cursor:pointer;outline:none}
.top-links{display:flex;gap:4px;align-items:center;flex-wrap:wrap}
.top-links a{color:var(--header-ink);text-decoration:none;font-weight:600;font-size:14px;padding:8px 10px;border-radius:10px;white-space:nowrap}
.top-links a:hover{background:rgba(246,234,217,.12)}
.saved-btn{background:var(--header-surface);color:var(--header-ink);border:1px solid var(--header-line);border-radius:10px;padding:8px 14px;font-weight:700;font-size:14px;cursor:pointer;white-space:nowrap}
.cat-dropdown{position:relative;display:inline-block}
.cat-btn{background:none;border:0;color:var(--header-ink);font-weight:600;font-size:14px;padding:8px 10px;border-radius:10px;cursor:pointer}
.cat-menu{display:none;position:absolute;top:calc(100% + 4px);right:0;background:var(--header-surface);border:1px solid var(--header-line);border-radius:12px;min-width:180px;z-index:9999;padding:6px 0;box-shadow:var(--shadow)}
.cat-dropdown:hover .cat-menu,.cat-dropdown:focus-within .cat-menu{display:block}
.cat-menu a{display:block;color:var(--header-ink);text-decoration:none;padding:8px 16px;font-size:14px;font-weight:600}
.cat-menu a:hover{background:rgba(246,234,217,.1)}
.search-row{background:#191613;border-top:1px solid var(--header-line);padding:9px 18px}
.search-inner{max-width:1180px;margin:0 auto;display:flex;align-items:center;gap:12px}
.search-icon{color:var(--header-muted);font-size:16px}
.search-box{flex:1;background:transparent;border:none;outline:none;color:var(--header-ink);font-size:15px;padding:4px 0}
.search-box::placeholder{color:var(--header-muted)}

/* Breadcrumb */
.breadcrumb{font-size:14px;margin:0 0 10px;color:var(--muted)}
.breadcrumb a{color:var(--red);font-weight:700;text-decoration:none}
.breadcrumb a:hover{text-decoration:underline}
.breadcrumb span[aria-current]{color:var(--ink);font-weight:700}

/* Hero photo */
.recipe-hero{margin:0 0 18px}
.recipe-hero img{width:100%;max-width:720px;height:400px;object-fit:cover;border-radius:20px;box-shadow:var(--shadow);border:1px solid var(--line)}

/* Facts 4-column card grid */
.facts{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:18px 0}
.fact{background:var(--surface2);border-radius:14px;padding:13px 14px}
.fact span{display:block;font-size:12px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.fact b{font-size:17px;color:var(--ink);display:block;margin-top:2px}
.pubdate{color:var(--muted);font-size:14px;margin:0 0 12px}
.intro{color:var(--muted);font-size:17px;line-height:1.65;margin:0 0 20px}

/* Video area with play button overlay */
.video-area{margin:20px 0 24px}
.video-area h3{font-size:26px;margin:0 0 10px;font-weight:600}
.video-frame{position:relative;aspect-ratio:16/9;overflow:hidden;border-radius:18px;border:1px solid var(--line);background:var(--surface2)}
.video-frame img{width:100%;height:100%;object-fit:cover}
.recipe-video{position:absolute;inset:0;width:100%;height:100%;border:0;background:#000}
.video-play{position:absolute;inset:0;width:100%;border:0;padding:16px;background:rgba(20,10,5,.38);color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:11px;cursor:pointer;text-decoration:none}
.video-play:hover{background:rgba(20,10,5,.52)}
.play-icon{width:66px;height:66px;border-radius:50%;background:var(--red);display:grid;place-items:center;box-shadow:0 6px 20px rgba(0,0,0,.35)}
.play-icon svg{width:26px;height:26px;fill:#fff;margin-left:3px}
.play-text{font-weight:800;font-size:15px;text-shadow:0 1px 8px rgba(0,0,0,.5);color:#fff}

/* Rating Area with gold stars */
.rating-area{margin:18px 0 24px}
.rating-area h3{font-size:26px;margin:0 0 8px;font-weight:600}
.rating-area .stars{display:flex;gap:4px}
.rating-area .star-shape{width:30px;height:30px;display:inline-block;background:#c07a1a;clip-path:polygon(50% 0%,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%)}
.rating-area .rating-text{margin:8px 0 0;color:var(--muted);font-size:15px}
.rating-line{color:var(--muted);font-size:15px}

/* Ingredients and method 2-column side-by-side */
.two-col{display:grid;grid-template-columns:1fr 1.25fr;gap:26px;margin-top:8px}
.two-col h3{font-size:26px;margin:0 0 10px;font-weight:600}
.two-col h4{font-family:"Cormorant Garamond",Georgia,serif;font-weight:600;font-size:24px;line-height:1.15;margin:0 0 10px}
.two-col ul{margin:0;padding-left:20px}
.two-col li{margin:7px 0;color:var(--muted);font-size:15px}
.two-col li b{color:var(--ink)}
.two-col ol{list-style:none;counter-reset:zw-step;padding-left:0;padding-right:0;margin:0}
.two-col ol li{counter-increment:zw-step;position:relative;padding-inline-start:36px;margin:8px 0;color:var(--muted);font-size:15px;line-height:1.6}
.two-col ol li::before{content:counter(zw-step) ".";position:absolute;inset-inline-start:0;top:0;font-weight:800;color:var(--red);direction:ltr}

/* Tip & Nutrition box */
.tip{background:#fdf0e4;border:1.5px solid #e8b08f;border-radius:16px;padding:15px 16px;margin-top:20px;color:#5a2e16}
@media (prefers-color-scheme: dark){.tip{background:#3a2a20;border-color:#7a4a2e;color:#f3d9c2}}
.tip h4{font-size:16px;font-weight:800;margin:0 0 3px;font-family:inherit}
.tip b{display:block;margin-bottom:3px}

/* Good to know & extra sections */
.extra-sections h3{font-size:26px;margin:22px 0 8px;font-weight:600}
.extra-sections h4{font-family:"Cormorant Garamond",Georgia,serif;font-weight:600;font-size:24px;line-height:1.15;margin:18px 0 8px}
.extra-sections p{color:var(--muted);font-size:15px;margin:0 0 10px}
.extra-sections ul{margin:0;padding-left:20px}
.extra-sections li{margin:7px 0;color:var(--muted);font-size:15px}
.serve-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:16px}

/* FAQ */
.recipe-faq{margin-top:20px}
.recipe-faq h4{font-family:"Cormorant Garamond",Georgia,serif;font-weight:600;font-size:26px;margin:0 0 10px;line-height:1.15}
.recipe-faq article{border-top:1px solid var(--line);padding:12px 0}
.recipe-faq article:first-child{border-top:0;padding-top:2px}
.recipe-faq h5{font-family:inherit;font-size:16px;font-weight:800;margin:0 0 4px;line-height:1.35}
.recipe-faq p{margin:0;color:var(--muted);font-size:15px}

/* What to serve with this dish - Pairings */
.recipe-pairs{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:20px 24px;margin:28px 0;box-shadow:var(--shadow)}
.recipe-pairs h3{margin-top:0;font-size:24px;color:var(--ink);border-bottom:1px solid var(--line);padding-bottom:8px}
.recipe-pairs ul{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;list-style:none;padding:0;margin:14px 0 0}
.recipe-pairs li{margin:0;background:var(--surface2);border:1px solid var(--line);border-radius:10px;padding:10px 14px}
.recipe-pairs a{color:var(--red);font-weight:700;text-decoration:none;font-size:15px}

/* E-E-A-T Verified Box */
.eeat-box{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--red);border-radius:14px;padding:16px 20px;margin:24px 0}
.eeat-box h4{margin:0 0 4px;color:var(--ink);font-size:18px;font-family:"Cormorant Garamond",Georgia,serif;font-weight:700}
.eeat-box p{margin:0;font-size:14.5px;color:var(--muted)}

/* Share & Action buttons */
.recipe-actions{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0 16px}
.btn{display:inline-block;text-decoration:none;border-radius:10px;padding:12px 22px;font-weight:700;font-size:15px;border:0;letter-spacing:.02em;cursor:pointer}
.btn-red{background:var(--red);color:#fff}
.btn-red:hover{background:var(--red-dark)}
.btn-ghost{background:var(--surface);color:var(--ink);border:1.5px solid var(--line)}
.btn-ghost:hover{border-color:var(--red)}
button.share-btn{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:10px 16px;font:inherit;color:var(--ink);font-weight:700;font-size:14px;cursor:pointer}
button.pin-btn{display:inline-flex;align-items:center;gap:6px;background:#e60023;color:#fff;border:0;padding:10px 18px;border-radius:24px;font-size:14px;font-weight:700;cursor:pointer;text-decoration:none}
.more-block{margin-top:26px;border-top:1px solid var(--line);padding-top:18px}
.more-block h3{font-size:26px;margin:0 0 12px;font-weight:600}
.more-links{display:flex;flex-wrap:wrap;gap:8px}
.more-links a{border:1.5px solid var(--line);background:var(--surface);border-radius:10px;padding:8px 14px;font-weight:700;font-size:14px;color:var(--ink);text-decoration:none}
.more-links a:hover{border-color:var(--red)}

.jump-btn{display:none}
.ad-slot{background:var(--surface);border:1px dashed var(--line);text-align:center;padding:14px;margin:24px 0;border-radius:10px;font-size:12px;color:var(--muted);letter-spacing:0.5px;text-transform:uppercase}

/* Rich 3-column Footer */
.site-footer{background:var(--header-bg);border-top:3px solid var(--accent);margin-top:52px;padding:40px 0 34px;color:var(--header-muted);font-size:14px;width:100%}
.site-footer .wrap{max-width:1180px;margin:0 auto;padding:0 18px}
.site-footer h2{font-size:32px;margin:0 0 8px;color:var(--header-ink);font-weight:600}
.site-footer h3{font-size:21px;margin:0 0 10px;color:var(--header-ink);font-family:"Cormorant Garamond",Georgia,serif;font-weight:600}
#footerLangH{font-size:16px;margin:18px 0 6px;font-family:inherit;color:var(--header-ink);font-weight:700}
.site-footer p{margin:0 0 10px;color:var(--header-muted)}
.site-footer a{color:var(--header-muted);text-decoration:none}
.site-footer a:hover{color:var(--header-ink);text-decoration:underline}
.footer-grid{display:grid;grid-template-columns:1.2fr .7fr .8fr;gap:28px}
.footer-col ul{list-style:none;margin:0;padding:0}
.footer-col li{margin:8px 0}
.footer-col a{color:var(--header-ink);text-decoration:none;font-weight:600}
.footer-col a:hover{text-decoration:underline}
.footer-social{margin-top:20px;font-size:14px;color:var(--header-muted)}
.footer-social a{color:var(--header-ink);font-weight:700}
.footer-copy{margin-top:28px;padding-top:18px;border-top:1px solid var(--header-line);font-size:13px;color:var(--header-muted)}

@media(max-width:860px){
  .two-col{grid-template-columns:1fr}
  .facts{grid-template-columns:repeat(2,1fr)}
  .serve-grid{grid-template-columns:1fr}
  .footer-grid{grid-template-columns:1fr}
  .top-links{display:none}
  .saved-btn{display:none}
}
@media(max-width:540px){
  .facts{grid-template-columns:1fr}
  .recipe-hero img{height:260px;max-width:100%}
}
'''.strip()

LANG_MENU_ITEMS = [
    ('en', 'English'),
    ('ru', 'Roman Urdu'),
    ('hi', 'हिन्दी (Hindi)'),
    ('ar', 'العربية (Arabic)'),
    ('fr', 'Français (French)'),
    ('es', 'Español (Spanish)'),
    ('zh', '中文 (Chinese)'),
    ('tr', 'Türkçe (Turkish)'),
    ('pt', 'Português'),
    ('bn', 'বাংলা (Bengali)'),
    ('ja', '日本語 (Japanese)'),
    ('de', 'Deutsch (German)'),
    ('rus', 'Русский (Russian)')
]

def render_site_header(current_lang='en', path='/'):
    """Generate dynamic header matching homepage structure with working language switcher for the current path."""
    options = []
    for l_code, l_label in LANG_MENU_ITEMS:
        # compute relative URL for this language
        if l_code == 'en':
            target_href = path
        else:
            prefix = LANG_PREFIX.get(l_code, l_code)
            target_href = '/' + prefix + (path if path != '/' else '')
        selected = ' selected' if l_code == current_lang else ''
        options.append('<option value="%s"%s>%s</option>' % (esc(target_href), selected, esc(l_label)))

    lang_select_html = (
        '<div class="lang-wrap">'
        '<span class="globe-icon">&#127760;</span>'
        '<select class="lang-select" onchange="if(this.value)location.href=this.value" aria-label="Select language">'
        + ''.join(options) +
        '</select></div>'
    )

    return (
        '<header class="topbar-modern">'
        '<div class="topbar-top">'
        '<div class="topbar-inner">'
        '<a class="brand" href="/">'
        '<img class="logo-img" src="/assets/asset-22f1c053.png" alt="Zaika Worlds" width="44" height="44">'
        'Zaika <span>Worlds</span></a>'
        + lang_select_html +
        '<nav class="top-links">'
        '<a href="/recipes">Recipes</a>'
        '<a href="/category/world-food">World Food</a>'
        '<a href="/trending">Trending</a>'
        '<a href="/faqs">FAQs</a>'
        '<a href="/about">About Us</a>'
        '<a href="/privacy">Privacy Policy</a>'
        '<a href="/contact">Contact Us</a>'
        '<div class="cat-dropdown">'
        '<button class="cat-btn" type="button" aria-haspopup="true">Categories &#x25BE;</button>'
        '<div class="cat-menu">'
        '<a href="/category/desi-dishes">&#x1F372; Desi Dishes</a>'
        '<a href="/category/bbq">&#x1F525; BBQ</a>'
        '<a href="/category/breakfast">&#x1F373; Breakfast</a>'
        '<a href="/category/street-food">&#x1F9BA; Street Food</a>'
        '<a href="/category/desserts">&#x1F36F; Desserts</a>'
        '<a href="/category/drinks">&#x1F375; Drinks</a>'
        '<a href="/category/world-food">&#x1F30D; World Food</a>'
        '</div></div>'
        '</nav>'
        '<button class="saved-btn" type="button" onclick="location.href=\'/#saved\'" aria-label="Saved recipes">'
        '&#x2665; Saved</button>'
        '</div></div>'
        '<div class="search-row">'
        '<div class="search-inner">'
        '<span class="search-icon">&#128269;</span>'
        '<input class="search-box" type="search" placeholder="Biryani, nihari, halwa&hellip; type anything" '
        'onkeydown="if(event.key===\'Enter\' && this.value.trim()) location.href=\'/recipes?q=\'+encodeURIComponent(this.value.trim())" '
        'aria-label="Search recipes">'
        '</div></div>'
        '</header>'
    )

SITE_FOOTER = ('''<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <h2 id="footerTitle">Zaika Worlds</h2>
        <p id="footerDesc">Zaika Worlds is a home cooking collection with big photos and step by step methods, from desi dishes to world food.</p>
        <p id="footerGuide">Every recipe on this page is a home cooking guide. It lists the ingredients first, then the cooking method in clear steps, with cooking time and servings.</p>
        <h3 id="footerLangH">Read in 13 languages</h3>
        <p id="footerLangP">English, Roman Urdu, हिन्दी, Español, Français, العربية, Português, Русский, 中文, 日本語, Deutsch, Türkçe, বাংলা. Use the language menu at the top to change the language.</p>
      </div>
      <nav class="footer-col footer-quick" aria-labelledby="footerQuickH">
        <h3 id="footerQuickH">Quick links</h3>
        <ul>
          <li><a href="/">Home</a></li>
          <li><a href="/recipes">Recipes</a></li>
          <li><a href="/category/world-food">World Food</a></li>
          <li><a href="/trending">Trending</a></li>
          <li><a href="/eid-recipes">Eid Recipes</a></li>
          <li><a href="/ramadan-recipes">Ramadan Recipes</a></li>
          <li><a href="/guides/dum-cooking">Dum Cooking Guide</a></li>
          <li><a href="/faqs">Cooking FAQs</a></li>
          <li><a href="/about">About Us</a></li>
          <li><a href="/privacy">Privacy Policy</a></li>
          <li><a href="/contact">Contact Us</a></li>
        </ul>
      </nav>
      <nav class="footer-col" aria-labelledby="footerCatH">
        <h3 id="footerCatH">Categories</h3>
        <ul id="footerCatList">
          <li><a href="/category/desi-dishes">Desi Dishes</a></li>
          <li><a href="/category/bbq">BBQ</a></li>
          <li><a href="/category/breakfast">Breakfast</a></li>
          <li><a href="/category/street-food">Street Food</a></li>
          <li><a href="/category/desserts">Desserts</a></li>
          <li><a href="/category/drinks">Drinks</a></li>
          <li><a href="/category/world-food">World Food</a></li>
        </ul>
      </nav>
    </div>
    <p class="footer-social">Follow Zaika Worlds: <a href="https://www.youtube.com/@ZaikaWorlds" target="_blank" rel="noopener">YouTube</a> · <a href="https://www.facebook.com/profile.php?id=1445260131997347" target="_blank" rel="noopener">Facebook</a> · <a href="https://www.pinterest.com/zaikaworlds26/" target="_blank" rel="noopener">Pinterest</a> · <a href="https://www.tiktok.com/@zaikaworlds" target="_blank" rel="noopener">TikTok</a></p>
    <p class="footer-copy" id="footerCopy">© 2026 Zaika Worlds</p>
  </div>
</footer>''')
# NOTE (2026-10-31, audit "5 pages have only one incoming internal
# link"): /about, /contact, /faqs, /privacy and /trending used to be
# linked only from the homepage footer, so the audit counted one
# incoming link each. They are now in SITE_FOOTER, which page_shell
# puts on every one of the 474 static pages, plus contextual links
# (recipe "More" paragraph, info-page cross-links). The --check
# thin-link guard below fails the build if any of the five ever
# drops below 10 incoming internal links again.


SHARE_JS = ('<script>\n'
            '/* Share buttons (2026-10-31, audit "3 external links are '
            'broken"): the WhatsApp share URL used to be a plain link to '
            'the WhatsApp share host, which audit crawlers follow; that '
            'host rate-limits bots with HTTP 429, so the audit flagged it '
            'as broken (real users get a normal redirect). The URL is '
            'therefore built ONLY on click, and the host is split across '
            'a string concatenation so no literal share URL appears in '
            'the HTML for a crawler to extract. The copy button puts the '
            'recipe URL on the clipboard instead of showing a bare-URL '
            'self-link (bare-URL text is also what audit tools flag as '
            'no/descriptive anchor text). */\n'
            'document.addEventListener("click",function(e){'
            'var pin=e.target.closest("button[data-pin]");'
            'if(pin){'
            'var u=encodeURIComponent(pin.getAttribute("data-pin-url"));'
            'var m=encodeURIComponent(pin.getAttribute("data-pin-media"));'
            'var d=encodeURIComponent(pin.getAttribute("data-pin-desc"));'
            'window.open("https://pinterest.com/pin/create/button/?url="+u+"&media="+m+"&description="+d,"_blank","width=750,height=600,noopener");'
            'return;}'
            'var b=e.target.closest("button[data-wa],button[data-copy]");'
            'if(!b)return;'
            'if(b.hasAttribute("data-wa")){'
            'window.open("https://wa"+".me/?text="+b.getAttribute("data-wa"),'
            '"_blank","noopener");}else{'
            'var u=b.getAttribute("data-copy");'
            'var done=function(){var t=b.textContent;'
            'b.textContent="Copied \\u2713";'
            'setTimeout(function(){b.textContent=t;},2000);};'
            'if(navigator.clipboard&&navigator.clipboard.writeText){'
            'navigator.clipboard.writeText(u).then(done,'
            'function(){fallbackCopy(u);done();});'
            '}else{fallbackCopy(u);done();}}});\n'
            'function fallbackCopy(t){var ta=document.createElement("textarea");'
            'ta.value=t;document.body.appendChild(ta);ta.select();'
            'try{document.execCommand("copy");}catch(err){}'
            'document.body.removeChild(ta);}\n'
            '</script>\n')


def page_shell(title, desc, url, og_img, og_alt, json_ld_blocks, body,
               og_type='website', article_dates=None, hreflang=None,
               html_lang='en', current_path='/', lang_code='en'):
    """Full static HTML page. title must already be capped at 60 chars.
    og_type is 'article' on recipe pages (with article:published_time /
    article:modified_time only when article_dates gives real dates) and
    'website' elsewhere. hreflang is [(hreflang, url)] for every language
    variant of the page + x-default."""
    assert len(title) <= 60, "title too long (%d): %r" % (len(title), title)
    ld = ''.join(
        '<script type="application/ld+json">%s</script>\n' % js_json(b)
        for b in json_ld_blocks)
    og_extra = ''
    if og_type == 'article' and article_dates:
        if article_dates.get('published'):
            og_extra += ('<meta property="article:published_time" '
                         'content="%s">\n'
                         % esc(article_dates['published']))
        if article_dates.get('modified'):
            og_extra += ('<meta property="article:modified_time" '
                         'content="%s">\n'
                         % esc(article_dates['modified']))
    alt_links = ''
    if hreflang:
        alt_links = ''.join(
            '<link rel="alternate" hreflang="%s" href="%s">\n'
            % (esc(code), esc(href)) for code, href in hreflang)
    head = ('<!DOCTYPE html>\n<html lang="%s">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,'
            ' initial-scale=1, viewport-fit=cover">\n'
            % html_lang)
    return (head +
            '<title>' + esc(title) + '</title>\n'
            '<meta name="description" content="' + esc(desc) + '">\n'
            '<meta name="robots" content="index, follow">\n'
            '<link rel="canonical" href="' + esc(url) + '">\n'
            + alt_links +
            '<meta property="og:type" content="' + esc(og_type) + '">\n'
            + og_extra +
            '<meta property="og:title" content="' + esc(title) + '">\n'
            '<meta property="og:description" content="' + esc(desc) + '">\n'
            '<meta property="og:url" content="' + esc(url) + '">\n'
            '<meta property="og:image" content="' + esc(og_img) + '">\n'
            '<meta property="og:image:alt" content="' + esc(og_alt) + '">\n'
            '<meta name="twitter:card" content="summary_large_image">\n'
            '<meta name="twitter:title" content="' + esc(title) + '">\n'
            '<meta name="twitter:description" content="' + esc(desc) + '">\n'
            '<meta name="twitter:image" content="' + esc(og_img) + '">\n'
            + ld +
            '<style>' + STATIC_CSS + '</style>\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500;1,600&family=Source+Sans+3:ital,wght@0,400;0,600;0,700;0,800;1,400&display=swap" rel="stylesheet">\n'
            '</head>\n<body>\n' + render_site_header(lang_code, current_path) + '\n<div class="wrap">\n'
            + body + '\n</div>\n' + SITE_FOOTER + '\n' + SHARE_JS
            + '</body>\n</html>\n')


def _as_datetime(d):
    """Date-only 'YYYY-MM-DD' -> 'YYYY-MM-DDT00:00:00+05:00' (midnight
    Asia/Karachi, where the videos were published); values that already
    carry a time/timezone pass through unchanged. The date itself is never
    altered — only the time precision Google requires for VideoObject
    uploadDate is added (Rich Results Test 2026-10-31 flagged date-only
    uploadDate as 'Invalid datetime value ... missing a timezone')."""
    if re.match(r'^\d{4}-\d{2}-\d{2}$', d or ''):
        return d + 'T00:00:00+05:00'
    return d


# Nutrition (GSC 'Missing field "nutrition"', 2026-10-31): per-serving
# estimates computed from the real ingredient lists (nutrition.json,
# USDA values). Order is the display order. Only fields present in the
# data are emitted — sodium is absent for 8 recipes (no salt listed)
# and is omitted there, never guessed.
_NUT_FIELDS = (('calories', 'Calories', 'calories'),
               ('proteinContent', 'Protein', 'g'),
               ('fatContent', 'Fat', 'g'),
               ('saturatedFatContent', 'Saturated fat', 'g'),
               ('carbohydrateContent', 'Carbs', 'g'),
               ('sugarContent', 'Sugar', 'g'),
               ('fiberContent', 'Fiber', 'g'),
               ('sodiumContent', 'Sodium', 'mg'))


def _fmt_num(v):
    f = float(v)
    return str(int(f)) if f == int(f) else ("%.1f" % f)


def nutrition_ld(nut):
    """NutritionInformation JSON-LD from the computed per-serving values.
    schema.org wants strings with units ('917 calories', '43.8 g')."""
    if not nut:
        return None
    out = {"@type": "NutritionInformation"}
    for key, _label, unit in _NUT_FIELDS:
        if key in nut:
            out[key] = "%s %s" % (_fmt_num(nut[key]), unit)
    return out


def nutrition_line(nut):
    """One visible line, '917 calories · Protein 43.8 g · …' — the
    calories value carries its own word, the rest take a label."""
    if not nut:
        return ''
    parts = []
    for key, label, unit in _NUT_FIELDS:
        if key not in nut:
            continue
        if key == 'calories':
            parts.append("%s calories" % _fmt_num(nut[key]))
        else:
            parts.append("%s %s %s" % (label, _fmt_num(nut[key]), unit))
    return ' · '.join(parts)


def recipe_json_ld(data, recipe, tx, url, lang='en', meta_desc=None,
                   video_date=None, article_date=None):
    """Recipe + BreadcrumbList + VideoObject + FAQPage JSON-LD. Ingredients
    are the split one-per-line list (issue G); totalTime comes from the
    recipe's real time (no invented prep/cook split); recipeYield is the
    recipe's servings. VideoObject only when this language's video exists;
    uploadDate only when a real publish date is recorded."""
    name = lang_name(recipe, data, lang)
    ing = split_ingredients(tx.get('ing') or [], lang)
    cuisine = data['country_adj'].get(recipe['country'], recipe['country'])
    ld = {"@context": "https://schema.org", "@type": "Recipe",
          "name": name,
          "image": [SITE + '/' + recipe['img']],
          "description": meta_desc or tx.get('desc') or DEF_DESC,
          "author": {"@type": "Organization", "name": "Zaika Worlds",
                     "url": SITE},
          "recipeYield": lang_servings(recipe, data, lang),
          "totalTime": "PT%dM" % (recipe['time'] or 60),
          "recipeIngredient": ing,
          "recipeInstructions": [{"@type": "HowToStep",
                                  "name": "Step %d" % (i + 1),
                                  "url": url + "#step-%d" % (i + 1),
                                  # GSC 'Either "image" or "video" should be
                                  # specified (in "recipeInstructions")'
                                  # (2026-10-31): every step carries the
                                  # recipe's own real photo — the same image
                                  # as the Recipe image. No per-step photo
                                  # exists and none is invented. This also
                                  # fixes recipes with no video yet (hummus).
                                  "image": [SITE + '/' + recipe['img']],
                                  "text": s}
                                 for i, s in
                                 enumerate(tx.get('steps') or [])],
          "recipeCategory": recipe['catLabel'],
          "recipeCuisine": cuisine,
          "keywords": "%s, %s recipe, %s" % (name, cuisine,
                                              recipe['catLabel'])}
    # GSC 'Missing field "nutrition"' (2026-10-31): per-serving values
    # computed from this recipe's real ingredients (nutrition.json);
    # only fields present in the data are emitted.
    _nut = (data.get('nutrition') or {}).get(recipe['id'])
    if _nut:
        ld["nutrition"] = nutrition_ld(_nut)
    # GSC 'Missing field "aggregateRating"' (2026-11-02): real visitor
    # ratings only, from ratings.json. A recipe with no votes has no
    # field at all (correct by design — never invented). ratingCount
    # (not reviewCount): these are star-only votes with no written
    # review. ratingValue is rounded to 1 decimal with a dot.
    _rat = (data.get('ratings') or {}).get(recipe['id'])
    if _rat and _rat.get('count', 0) > 0:
        _avg = round(_rat['sum'] / _rat['count'], 1)
        ld["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": _avg,
            "ratingCount": _rat['count'],
            "bestRating": 5, "worstRating": 1}
    if article_date:
        # Real publish date only (recipe_dates.json); never invented.
        ld["datePublished"] = article_date
    # Category crumb links the English category URL (the visible breadcrumb
    # does the same): language category pages do not exist (/hi/category/…
    # is a 404), so a language-prefixed item URL would be a dead link.
    cat_slug = data['cat_slug'].get(recipe['cat'], '')
    bld = {"@context": "https://schema.org", "@type": "BreadcrumbList",
           "itemListElement": [
               {"@type": "ListItem", "position": 1, "name": "Home",
                "item": lang_url('/', lang)},
               {"@type": "ListItem", "position": 2,
                "name": lang_cat_label(recipe, data, lang),
                "item": SITE + '/category/' + cat_slug},
               {"@type": "ListItem", "position": 3, "name": name,
                "item": url}]}
    blocks = [ld, bld]
    vid = (recipe.get('videos') or {}).get(lang)
    if vid:
        # Recipe "video" (GSC "Missing field 'video'", 2026-10-31): the
        # Recipe links the VideoObject by @id (page url + "#video") instead
        # of carrying a second copy. A standalone VideoObject alone does
        # not satisfy the Recipe's video field.
        ld["video"] = {"@id": url + "#video"}
        vld = {"@context": "https://schema.org", "@type": "VideoObject",
               "@id": url + "#video",
               "name": name,
               "author": {"@type": "Organization", "name": "Zaika Worlds",
                          "url": SITE},
               "description": meta_desc or tx.get('desc') or DEF_DESC,
               "thumbnailUrl": "https://i.ytimg.com/vi/%s/hqdefault.jpg"
                               % vid,
               "contentUrl": "https://www.youtube.com/watch?v=%s" % vid,
               "url": "https://www.youtube.com/watch?v=%s" % vid,
               "embedUrl": "https://www.youtube-nocookie.com/embed/%s" % vid,
               "duration": "PT1M"}
        if video_date:
            vld["uploadDate"] = _as_datetime(video_date)
        blocks.append(vld)
    faq = tx.get('faq') or []
    if faq:
        fld = {"@context": "https://schema.org", "@type": "FAQPage",
               "mainEntity": [{"@type": "Question", "name": q,
                               "acceptedAnswer": {"@type": "Answer",
                                                  "text": a}}
                              for q, a in faq]}
        blocks.append(fld)
    return blocks



RECIPE_PAIRINGS = {
    # ── Desi / South Asian cluster (from both XLSX files) ─────────────────
    'biryani':        [('nihari',        'Nalli Nihari'),
                       ('karahi',        'Chicken Karahi'),
                       ('gulabjamun',    'Warm Gulab Jamun'),
                       ('lassi',         'Sweet Mango Lassi')],
    'nihari':         [('biryani',       'Chicken Biryani'),
                       ('halwapuri',     'Halwa Puri Nashta'),
                       ('karahi',        'Chicken Karahi'),
                       ('kheer',         'Traditional Badami Kheer')],
    'karahi':         [('biryani',       'Chicken Biryani'),
                       ('daal',          'Daal Fry (Tadka Daal)'),
                       ('tikka',         'Chicken Tikka'),
                       ('lassi',         'Mango Lassi')],
    'haleem':         [('biryani',       'Chicken Biryani'),
                       ('chapli',        'Chapli Kabab'),
                       ('nihari',        'Nalli Nihari'),
                       ('gulabjamun',    'Gulab Jamun')],
    'chicken-korma':  [('kheer',         'Badami Kheer'),
                       ('aloo-paratha',  'Aloo Paratha'),
                       ('karahi',        'Chicken Karahi'),
                       ('biryani',       'Chicken Biryani')],
    'chapli':         [('tikka',         'Chicken Tikka'),
                       ('seekh-kebab',   'Seekh Kebab'),
                       ('daal',          'Daal Fry'),
                       ('lassi',         'Mango Lassi')],
    'tikka':          [('seekh-kebab',   'Seekh Kebab'),
                       ('biryani',       'Chicken Biryani'),
                       ('chapli',        'Chapli Kabab'),
                       ('karahi',        'Chicken Karahi')],
    'seekh-kebab':    [('tikka',         'Chicken Tikka'),
                       ('bunkebab',      'Bun Kebab'),
                       ('chapli',        'Chapli Kabab'),
                       ('lassi',         'Mango Lassi')],
    'daal':           [('biryani',       'Chicken Biryani'),
                       ('aloo-paratha',  'Aloo Paratha'),
                       ('karahi',        'Chicken Karahi'),
                       ('halwapuri',     'Halwa Puri')],
    'halwapuri':      [('aloo-paratha',  'Aloo Paratha'),
                       ('lassi',         'Mango Lassi'),
                       ('kheer',         'Traditional Kheer'),
                       ('nihari',        'Nalli Nihari')],
    'aloo-paratha':   [('daal',          'Daal Fry'),
                       ('lassi',         'Mango Lassi'),
                       ('halwapuri',     'Halwa Puri Nashta'),
                       ('tikka',         'Chicken Tikka')],
    'bunkebab':       [('samosa',        'Punjabi Samosa'),
                       ('tikka',         'Chicken Tikka'),
                       ('lassi',         'Mango Lassi'),
                       ('seekh-kebab',   'Seekh Kebab')],
    'samosa':         [('bunkebab',      'Bun Kebab'),
                       ('gulabjamun',    'Gulab Jamun'),
                       ('lassi',         'Mango Lassi'),
                       ('chapli',        'Chapli Kabab')],
    'gulabjamun':     [('gajarhalwa',    'Gajar Ka Halwa'),
                       ('kheer',         'Traditional Kheer'),
                       ('biryani',       'Chicken Biryani'),
                       ('lassi',         'Mango Lassi')],
    'gajarhalwa':     [('gulabjamun',    'Gulab Jamun'),
                       ('kheer',         'Badami Kheer'),
                       ('lassi',         'Mango Lassi'),
                       ('halwapuri',     'Halwa Puri')],
    'kheer':          [('gajarhalwa',    'Gajar Ka Halwa'),
                       ('gulabjamun',    'Gulab Jamun'),
                       ('biryani',       'Chicken Biryani'),
                       ('lassi',         'Mango Lassi')],
    'lassi':          [('biryani',       'Chicken Biryani'),
                       ('tikka',         'Chicken Tikka'),
                       ('samosa',        'Punjabi Samosa'),
                       ('halwapuri',     'Halwa Puri')],
    # Mutton / Karahi variants (from XLSX authority file)
    'mutton-karahi':  [('karahi',        'Chicken Karahi'),
                       ('nihari',        'Nalli Nihari'),
                       ('biryani',       'Chicken Biryani'),
                       ('daal',          'Daal Fry')],
    'white-karahi':   [('karahi',        'Chicken Karahi'),
                       ('mutton-karahi', 'Mutton Karahi'),
                       ('biryani',       'Chicken Biryani'),
                       ('tikka',         'Chicken Tikka')],
    'shinwari-karahi':  [('white-karahi', 'White Chicken Karahi'),
                         ('karahi',       'Chicken Karahi'),
                         ('chapli',       'Chapli Kabab'),
                         ('biryani',      'Chicken Biryani')],
    'mutton-biryani': [('biryani',       'Chicken Biryani'),
                       ('karahi',        'Chicken Karahi'),
                       ('nihari',        'Nalli Nihari'),
                       ('gulabjamun',    'Gulab Jamun')],
    'sindhi-biryani': [('biryani',       'Chicken Biryani'),
                       ('mutton-biryani','Mutton Biryani'),
                       ('daal',          'Daal Fry'),
                       ('lassi',         'Mango Lassi')],
    'hyderabadi-biryani': [('biryani',   'Chicken Biryani'),
                           ('mutton-biryani', 'Mutton Biryani'),
                           ('karahi',    'Chicken Karahi'),
                           ('gulabjamun','Gulab Jamun')],
    'kunna':          [('nihari',        'Nalli Nihari'),
                       ('karahi',        'Chicken Karahi'),
                       ('biryani',       'Chicken Biryani'),
                       ('daal',          'Daal Fry')],
    'yakhni-pulao':   [('biryani',       'Chicken Biryani'),
                       ('karahi',        'Chicken Karahi'),
                       ('daal',          'Daal Fry'),
                       ('kheer',         'Traditional Kheer')],
    # ── Middle Eastern / Mediterranean cluster ─────────────────────────────
    'kabuli-pulao':   [('chapli',        'Chapli Kabab'),
                       ('machboos',      'Arabian Machboos'),
                       ('hummus',        'Creamy Hummus'),
                       ('falafel',       'Crispy Falafel')],
    'machboos':       [('kabuli-pulao',  'Kabuli Pulao'),
                       ('hummus',        'Creamy Hummus'),
                       ('falafel',       'Crispy Falafel'),
                       ('dolma',         'Dolma')],
    'hummus':         [('falafel',       'Crispy Falafel'),
                       ('souvla',        'Cypriot Souvla'),
                       ('dolma',         'Dolma'),
                       ('moussaka',      'Greek Moussaka')],
    'falafel':        [('hummus',        'Creamy Hummus'),
                       ('moussaka',      'Greek Moussaka'),
                       ('dolma',         'Dolma'),
                       ('souvla',        'Cypriot Souvla')],
    'moussaka':       [('souvla',        'Cypriot Souvla'),
                       ('hummus',        'Creamy Hummus'),
                       ('dolma',         'Dolma'),
                       ('falafel',       'Crispy Falafel')],
    'souvla':         [('hummus',        'Creamy Hummus'),
                       ('moussaka',      'Greek Moussaka'),
                       ('falafel',       'Falafel'),
                       ('dolma',         'Dolma')],
    'dolma':          [('hummus',        'Creamy Hummus'),
                       ('plov',          'Azerbaijani Plov'),
                       ('falafel',       'Falafel'),
                       ('moussaka',      'Greek Moussaka')],
    'plov':           [('dolma',         'Dolma'),
                       ('kabuli-pulao',  'Kabuli Pulao'),
                       ('machboos',      'Arabian Machboos'),
                       ('hummus',        'Creamy Hummus')],
    'shawarma':       [('hummus',        'Creamy Hummus'),
                       ('falafel',       'Crispy Falafel'),
                       ('dolma',         'Dolma'),
                       ('kabuli-pulao',  'Kabuli Pulao')],
    # ── East / Southeast Asian cluster ─────────────────────────────────────
    'ramen':          [('dimsum',        'Dim Sum'),
                       ('sushi',         'Sushi Rolls'),
                       ('padthai',       'Pad Thai'),
                       ('pekingduck',    'Peking Duck')],
    'sushi':          [('ramen',         'Japanese Ramen'),
                       ('dimsum',        'Dim Sum'),
                       ('beefpho',       'Beef Pho'),
                       ('padthai',       'Pad Thai')],
    'padthai':        [('fish-amok',     'Fish Amok'),
                       ('dimsum',        'Dim Sum'),
                       ('ramen',         'Japanese Ramen'),
                       ('green-curry',   'Thai Green Curry')],
    'pekingduck':     [('dimsum',        'Dim Sum'),
                       ('padthai',       'Pad Thai'),
                       ('ramen',         'Japanese Ramen'),
                       ('sushi',         'Sushi Rolls')],
    'dimsum':         [('pekingduck',    'Peking Duck'),
                       ('ramen',         'Japanese Ramen'),
                       ('padthai',       'Pad Thai'),
                       ('sushi',         'Sushi Rolls')],
    'beefpho':        [('padthai',       'Pad Thai'),
                       ('dimsum',        'Dim Sum'),
                       ('fish-amok',     'Fish Amok'),
                       ('ramen',         'Japanese Ramen')],
    'fish-amok':      [('beefpho',       'Beef Pho'),
                       ('padthai',       'Pad Thai'),
                       ('ambuyat',       'Ambuyat'),
                       ('green-curry',   'Thai Green Curry')],
    'green-curry':    [('padthai',       'Pad Thai'),
                       ('fish-amok',     'Fish Amok'),
                       ('ramen',         'Japanese Ramen'),
                       ('massaman-curry','Massaman Curry')],
    'massaman-curry': [('green-curry',   'Thai Green Curry'),
                       ('padthai',       'Pad Thai'),
                       ('dimsum',        'Dim Sum'),
                       ('fish-amok',     'Fish Amok')],
    'ema-datshi':     [('ilish-bhapa',   'Ilish Bhapa'),
                       ('fish-amok',     'Fish Amok'),
                       ('plov',          'Azerbaijani Plov'),
                       ('padthai',       'Pad Thai')],
    'ilish-bhapa':    [('daal',          'Daal Fry'),
                       ('ema-datshi',    'Ema Datshi'),
                       ('biryani',       'Chicken Biryani'),
                       ('fish-amok',     'Fish Amok')],
    'ambuyat':        [('fish-amok',     'Fish Amok'),
                       ('beefpho',       'Beef Pho'),
                       ('padthai',       'Pad Thai'),
                       ('dimsum',        'Dim Sum')],
    'nasi-goreng':    [('padthai',       'Pad Thai'),
                       ('dimsum',        'Dim Sum'),
                       ('fish-amok',     'Fish Amok'),
                       ('ramen',         'Japanese Ramen')],
    'kung-pao':       [('dimsum',        'Dim Sum'),
                       ('pekingduck',    'Peking Duck'),
                       ('padthai',       'Pad Thai'),
                       ('ramen',         'Japanese Ramen')],
    'sweet-sour-chicken': [('dimsum',    'Dim Sum'),
                           ('kung-pao',  'Kung Pao Chicken'),
                           ('padthai',   'Pad Thai'),
                           ('ramen',     'Japanese Ramen')],
    'gyoza':          [('dimsum',        'Dim Sum'),
                       ('ramen',         'Japanese Ramen'),
                       ('sushi',         'Sushi Rolls'),
                       ('padthai',       'Pad Thai')],
    'chow-mein':      [('dimsum',        'Dim Sum'),
                       ('padthai',       'Pad Thai'),
                       ('ramen',         'Japanese Ramen'),
                       ('kung-pao',      'Kung Pao Chicken')],
    'tom-yum':        [('padthai',       'Pad Thai'),
                       ('green-curry',   'Thai Green Curry'),
                       ('fish-amok',     'Fish Amok'),
                       ('ramen',         'Japanese Ramen')],
    'katsu-curry':    [('ramen',         'Japanese Ramen'),
                       ('sushi',         'Sushi Rolls'),
                       ('dimsum',        'Dim Sum'),
                       ('gyoza',         'Gyoza Dumplings')],
    # ── European cluster ───────────────────────────────────────────────────
    'pizza':          [('carbonara',     'Spaghetti Carbonara'),
                       ('coqauvin',      'Coq au Vin'),
                       ('paella',        'Seafood Paella'),
                       ('lasagna',       'Lasagna Bolognese')],
    'carbonara':      [('pizza',         'Margherita Pizza'),
                       ('coqauvin',      'Coq au Vin'),
                       ('bouillabaisse', 'Bouillabaisse'),
                       ('lasagna',       'Lasagna Bolognese')],
    'lasagna':        [('pizza',         'Margherita Pizza'),
                       ('carbonara',     'Spaghetti Carbonara'),
                       ('coqauvin',      'Coq au Vin'),
                       ('bouillabaisse', 'Bouillabaisse')],
    'coqauvin':       [('bouillabaisse', 'Bouillabaisse'),
                       ('carbonara',     'Spaghetti Carbonara'),
                       ('paella',        'Seafood Paella'),
                       ('pizza',         'Margherita Pizza')],
    'bouillabaisse':  [('coqauvin',      'Coq au Vin'),
                       ('paella',        'Seafood Paella'),
                       ('carbonara',     'Spaghetti Carbonara'),
                       ('pizza',         'Margherita Pizza')],
    'paella':         [('bouillabaisse', 'Bouillabaisse'),
                       ('pizza',         'Margherita Pizza'),
                       ('feijoada',      'Brazilian Feijoada'),
                       ('coqauvin',      'Coq au Vin')],
    # ── Americas cluster ───────────────────────────────────────────────────
    'tacos':          [('pozole',        'Pozole Rojo'),
                       ('feijoada',      'Brazilian Feijoada'),
                       ('pizza',         'Margherita Pizza'),
                       ('guacamole',     'Guacamole')],
    'pozole':         [('tacos',         'Tacos al Pastor'),
                       ('feijoada',      'Brazilian Feijoada'),
                       ('meatpie',       'Aussie Meat Pie'),
                       ('guacamole',     'Guacamole')],
    'feijoada':       [('tacos',         'Tacos al Pastor'),
                       ('pozole',        'Pozole Rojo'),
                       ('bobotie',       'Bobotie'),
                       ('paella',        'Seafood Paella')],
    'poutine':        [('meatpie',       'Aussie Meat Pie'),
                       ('pizza',         'Margherita Pizza'),
                       ('tacos',         'Tacos al Pastor'),
                       ('carbonara',     'Spaghetti Carbonara')],
    'guacamole':      [('tacos',         'Tacos al Pastor'),
                       ('pozole',        'Pozole Rojo'),
                       ('feijoada',      'Brazilian Feijoada'),
                       ('pizza',         'Margherita Pizza')],
    'birria-tacos':   [('tacos',         'Tacos al Pastor'),
                       ('pozole',        'Pozole Rojo'),
                       ('guacamole',     'Guacamole & Chips'),
                       ('feijoada',      'Brazilian Feijoada')],
    'carne-asada':    [('tacos',         'Tacos al Pastor'),
                       ('birria-tacos',  'Birria Tacos'),
                       ('guacamole',     'Guacamole & Chips'),
                       ('pozole',        'Pozole Rojo')],
    'enchiladas':     [('tacos',         'Tacos al Pastor'),
                       ('carne-asada',   'Carne Asada'),
                       ('guacamole',     'Guacamole & Chips'),
                       ('pozole',        'Pozole Rojo')],
    # ── African cluster ────────────────────────────────────────────────────
    'bobotie':        [('meatpie',       'Aussie Meat Pie'),
                       ('feijoada',      'Brazilian Feijoada'),
                       ('plov',          'Azerbaijani Plov'),
                       ('dolma',         'Dolma')],
    'meatpie':        [('poutine',       'Canadian Poutine'),
                       ('bobotie',       'Bobotie'),
                       ('pizza',         'Margherita Pizza'),
                       ('tacos',         'Tacos al Pastor')],
    # ── Italian extras (from XLSX) ──────────────────────────────────────────
    'fettuccine-alfredo': [('carbonara', 'Spaghetti Carbonara'),
                           ('lasagna',   'Lasagna Bolognese'),
                           ('pizza',     'Margherita Pizza'),
                           ('coqauvin',  'Coq au Vin')],
    # ── Middle Eastern extras (from XLSX authority file) ───────────────────
    'kofta':          [('hummus',        'Creamy Hummus'),
                       ('falafel',       'Crispy Falafel'),
                       ('dolma',         'Dolma'),
                       ('shawarma',      'Chicken Shawarma')],
    'shish-taouk':    [('kofta',         'Lamb Kofta'),
                       ('hummus',        'Creamy Hummus'),
                       ('falafel',       'Crispy Falafel'),
                       ('shawarma',      'Chicken Shawarma')],
    'tabbouleh':      [('hummus',        'Creamy Hummus'),
                       ('falafel',       'Crispy Falafel'),
                       ('fattoush',      'Fattoush Salad'),
                       ('dolma',         'Dolma')],
    'fattoush':       [('tabbouleh',     'Tabbouleh'),
                       ('hummus',        'Creamy Hummus'),
                       ('falafel',       'Crispy Falafel'),
                       ('dolma',         'Dolma')],
    'mansaf':         [('kabuli-pulao',  'Kabuli Pulao'),
                       ('machboos',      'Arabian Machboos'),
                       ('hummus',        'Creamy Hummus'),
                       ('dolma',         'Dolma')],
    'baba-ganoush':   [('hummus',        'Creamy Hummus'),
                       ('falafel',       'Crispy Falafel'),
                       ('tabbouleh',     'Tabbouleh'),
                       ('dolma',         'Dolma')],
    'hummus-bil-lahme':[('hummus',       'Classic Hummus'),
                        ('kofta',        'Lamb Kofta'),
                        ('mansaf',       'Mansaf'),
                        ('shish-taouk',  'Shish Taouk')],
    'foul-mudammas':  [('hummus',        'Creamy Hummus'),
                       ('falafel',       'Crispy Falafel'),
                       ('tabbouleh',     'Tabbouleh'),
                       ('baba-ganoush',  'Baba Ganoush')],
    'mutabal':        [('baba-ganoush',  'Baba Ganoush'),
                       ('hummus',        'Creamy Hummus'),
                       ('tabbouleh',     'Tabbouleh'),
                       ('falafel',       'Crispy Falafel')],
    'doner-kebab':    [('shawarma',      'Chicken Shawarma'),
                       ('kofta',         'Lamb Kofta'),
                       ('hummus',        'Creamy Hummus'),
                       ('falafel',       'Crispy Falafel')],
    'tikka-masala':   [('karahi',        'Chicken Karahi'),
                       ('biryani',       'Chicken Biryani'),
                       ('butter-chicken','Butter Chicken'),
                       ('daal',          'Daal Fry')],
    'butter-chicken': [('tikka-masala',  'Chicken Tikka Masala'),
                       ('karahi',        'Chicken Karahi'),
                       ('biryani',       'Chicken Biryani'),
                       ('lassi',         'Mango Lassi')],
    'banh-mi':        [('beefpho',       'Beef Pho'),
                       ('padthai',       'Pad Thai'),
                       ('dimsum',        'Dim Sum'),
                       ('fish-amok',     'Fish Amok')],
    'pulao':          [('biryani',       'Chicken Biryani'),
                       ('karahi',        'Chicken Karahi'),
                       ('daal',          'Daal Fry'),
                       ('yakhni-pulao',  'Yakhni Pulao')],
}

def recipe_page(data, recipe, lang='en', dates=None):
    """Static recipe page matching the homepage recipeView structure exactly."""
    tx = r_text_lang(recipe, data, lang)
    name = lang_name(recipe, data, lang)
    path = '/recipe/' + recipe['id']
    url = lang_url(path, lang)
    if lang == 'en':
        title = recipe_title_en(recipe, data)
        desc = recipe_desc_en(recipe, tx)
    else:
        title = recipe_title_lang(recipe, data, lang)
        desc = recipe_desc_lang(recipe, data, lang)
    img_url = SITE + '/' + recipe['img']
    img_alt = lang_alt(recipe, data, lang)
    dims = data['img_dims'].get(recipe['img'], [])
    wh = (' width="%d" height="%d"' % (dims[0], dims[1]) if len(dims) == 2 else '')
    cat_slug = data['cat_slug'].get(recipe['cat'], '')
    ctry_slug = data['country_slug'].get(recipe['country'], '')
    home_url = lang_url('/', lang)
    cat_label = lang_cat_label(recipe, data, lang)
    minute = data['ui_min'].get(lang, 'min')
    dates = dates or {}
    article = (dates.get('article') or {}).get(recipe['id'], {})
    video_dates = (dates.get('video') or {}).get(recipe['id'], {})
    vid = (recipe.get('videos') or {}).get(lang)
    video_date = video_dates.get(lang) if isinstance(video_dates, dict) else None

    h = lambda key, default: ui_str(data, lang, key, default)

    # 1. Facts cards
    time_label = h('time', 'Time')
    serv_label = h('serv', 'Servings')
    diff_label = h('diff', 'Difficulty')
    cat_lbl = h('cat', 'Category')
    facts_html = (
        '<div class="facts" id="recipeFacts">\n'
        '  <div class="fact"><span>' + esc(time_label) + '</span><b>' + esc(recipe['time']) + ' ' + esc(minute) + '</b></div>\n'
        '  <div class="fact"><span>' + esc(serv_label) + '</span><b>' + esc(lang_servings(recipe, data, lang)) + '</b></div>\n'
        '  <div class="fact"><span>' + esc(diff_label) + '</span><b>' + esc(lang_diff(recipe, data, lang)) + '</b></div>\n'
        '  <div class="fact"><span>' + esc(cat_lbl) + '</span><b>' + esc(cat_label) + ' &middot; ' + esc(recipe['country']) + '</b></div>\n'
        '</div>\n'
    )

    # 2. Publish date
    pub = recipe.get('published') or article.get('published')
    pubdate_html = ''
    if pub:
        pubdate_html = ('<p class="pubdate">' + esc(h('publishedOn', 'Published on')) + ' ' + esc(fmt_date(pub)) + '</p>\n')

    # 3. Video frame with play button overlay
    if vid:
        video_html = (
            '<div class="video-area" id="videoArea">\n'
            '  <h2 id="videoHeading">' + esc(h('videoH', 'Recipe Video')) + '</h2>\n'
            '  <div class="video-frame">\n'
            '    <img src="' + esc(img_url) + '" alt="' + esc(img_alt) + '" loading="lazy" width="1792" height="1344">\n'
            '    <a class="video-play" href="https://youtu.be/' + esc(vid) + '" target="_blank" rel="noopener" aria-label="' + esc(h('videoPlay', 'Watch the recipe video')) + '">\n'
            '      <span class="play-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span>\n'
            '      <span class="play-text">' + esc(h('videoPlay', 'Watch the recipe video')) + '</span>\n'
            '    </a>\n'
            '  </div>\n'
            '</div>\n'
        )
    else:
        video_html = (
            '<div class="video-area" id="videoArea">\n'
            '  <h2 id="videoHeading">' + esc(h('videoH', 'Recipe Video')) + '</h2>\n'
            '  <p class="muted">' + esc(h('videoSoon', 'Video coming soon — this recipe is being filmed.')) + '</p>\n'
            '</div>\n'
        )

    # 4. Rating area
    rat = (data.get('ratings') or {}).get(recipe['id'])
    star_span = '<span class="star-shape" aria-hidden="true"></span>'
    stars_html = star_span * 5
    if rat and rat.get('count', 0) > 0:
        _avg = round(rat['sum'] / rat['count'], 1)
        r_text = fmt_rate_avg(data, lang, _avg, rat['count'])
    else:
        r_text = h('rateFirst', 'Be the first to rate this recipe')
    rating_html = (
        '<div class="rating-area" id="ratingArea">\n'
        '  <h2 id="ratingHeading">' + esc(h('rateH', 'Rate this recipe')) + '</h2>\n'
        '  <div class="stars" id="ratingStars" aria-label="Rate this recipe">' + stars_html + '</div>\n'
        '  <p class="rating-line">' + esc(r_text) + '</p>\n'
        '</div>\n'
    )

    # 5. Two-column: Ingredients & Method side-by-side
    split_ing = split_ingredients(tx.get('ing'), lang)
    ing_lis = ''.join('<li>' + esc(x) + '</li>' for x in split_ing)
    step_lis = ''.join('<li id="step-%d">' % (i + 1) + esc(x) + '</li>' for i, x in enumerate(tx.get('steps') or []))
    two_col_html = (
        '<div id="recipe-card"></div>\n'
        '<h2 id="detailsHeading">' + esc(h('detailsH', 'Ingredients and method')) + '</h2>\n'
        '<div class="two-col">\n'
        '  <div><h3 id="ingHeading">' + esc(h('ingH', 'Ingredients')) + '</h3><ul id="recipeIng">' + ing_lis + '</ul></div>\n'
        '  <div><h3 id="methodHeading">' + esc(h('methH', 'Method')) + '</h3><ol id="recipeSteps">' + step_lis + '</ol></div>\n'
        '</div>\n'
    )

    # 6. Nutrition block
    nut = (data.get('nutrition') or {}).get(recipe['id'])
    nut_html = ''
    if nut:
        nut_html = ('<div class="tip" id="nutritionBlock"><h3 id="nutritionHeading">' + esc(h('nutritionH', 'Nutrition (approx. per serving)')) + '</h3><p>' + esc(nutrition_line(nut)) + '</p></div>\n')

    # 7. Chef\'s Tip
    tip_html = ''
    if tx.get('tip'):
        tip_html = ('<div class="tip"><h3 id="tipHeading">' + esc(h('tipH', "Chef's tip")) + '</h3><span>' + esc(tx['tip']) + '</span></div>\n')

    # 8. Good to know sections
    good_sections = []
    serve_val = tx.get('serving') or ''
    store_val = tx.get('storage') or ''
    if serve_val or store_val:
        serve_block = ('<div><h3 id="servingHeading">' + esc(h('servingH', 'Serving')) + '</h3><p>' + esc(serve_val) + '</p></div>') if serve_val else ''
        store_block = ('<div><h3 id="storageHeading">' + esc(h('storageH', 'Storage and reheating')) + '</h3><p>' + esc(store_val) + '</p></div>') if store_val else ''
        good_sections.append('<div class="serve-grid">' + serve_block + store_block + '</div>')
    if tx.get('notes'):
        good_sections.append('<h3 id="notesHeading">' + esc(h('notesH', 'Ingredient notes')) + '</h3><ul>' + ''.join('<li>' + esc(n) + '</li>' for n in tx['notes']) + '</ul>')
    if tx.get('variations'):
        good_sections.append('<h3 id="varHeading">' + esc(h('varH', 'Variations')) + '</h3><ul>' + ''.join('<li>' + esc(n) + '</li>' for n in tx['variations']) + '</ul>')
    if tx.get('mistakes'):
        good_sections.append('<h3 id="mistakesHeading">' + esc(h('mistakesH', 'Common mistakes')) + '</h3><ul>' + ''.join('<li>' + esc(n) + '</li>' for n in tx['mistakes']) + '</ul>')
    if tx.get('faq'):
        faq_articles = ''.join('<article><h4>' + esc(q) + '</h4><p>' + esc(a) + '</p></article>' for q, a in tx['faq'])
        good_sections.append('<div class="recipe-faq"><h3 id="recipeFaqHeading">' + esc(ui_str(data, lang, 'recipeFaqH', 'Frequently asked questions')) + '</h3>' + faq_articles + '</div>')

    good_to_know_html = ''
    if good_sections:
        good_to_know_html = ('<h2 id="goodHeading">' + esc(h('goodHeading', 'Good to know')) + '</h2>\n<div class="extra-sections">\n' + '\n'.join(good_sections) + '\n</div>\n')

    # 9. Pairing block
    pairs = RECIPE_PAIRINGS.get(recipe['id'], [])
    pairs_html = ''
    if pairs:
        pairs_lis = ''.join('<li><a href="/recipe/%s">%s</a></li>' % (esc(sid), esc(stitle)) for sid, stitle in pairs)
        pairs_html = '<div class="recipe-pairs"><h2>What to Serve With This Dish</h2><ul>' + pairs_lis + '</ul></div>\n'

    # 10. E-E-A-T and Ads
    eeat_html = (
        '<div class="eeat-box"><h3>Verified by Zaika Worlds Kitchen</h3>'
        '<p>This recipe was tested and standardized by home cooking specialists to guarantee accurate ingredient ratios, reliable prep times, and authentic regional taste.</p></div>\n'
        '<div class="ad-slot" aria-hidden="true">&mdash; Advertisement &mdash;</div>\n'
    )

    # 11. Navigation links
    more_links = (
        '<div class="more-block"><h2>Explore more authentic recipes</h2>\n'
        '<div class="more-links">'
        '<a href="/category/' + esc(cat_slug) + '">More ' + esc(cat_label) + ' recipes</a>'
        '<a href="/country/' + esc(ctry_slug) + '">More ' + esc(recipe['country']) + ' recipes</a>'
        '<a href="/recipes">All recipes</a>'
        '<a href="/faqs">Cooking FAQs</a>'
        '<a href="/trending">Trending Recipes</a>'
        '</div></div>\n'
    )
    if recipe['id'] in ('biryani', 'karahi', 'nihari'):
        more_links = more_links.replace('Trending Recipes</a>',
                                        'Trending Recipes</a><a href="/guides/dum-cooking">Dum Cooking Guide</a>', 1)

    # 12. Share buttons
    wa_text = 'See this recipe: %s, Zaika Worlds: %s' % (name, url)
    wa_q = quote(wa_text)
    share_html = (
        '<div class="recipe-actions">'
        '<button type="button" class="btn btn-ghost share-btn" data-copy="' + esc(url) + '">Copy recipe link</button>'
        '<button type="button" class="btn btn-red share-btn" data-wa="' + esc(wa_q) + '">Share on WhatsApp</button>'
        '<button type="button" class="pin-btn" data-pin data-pin-url="' + esc(url) + '" data-pin-media="' + esc(img_url) + '" data-pin-desc="' + esc(name) + '">'
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="vertical-align:-2px"><path d="M12 0C5.373 0 0 5.372 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738.098.119.112.224.083.345-.09.375-.291 1.199-.334 1.357-.053.225-.172.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.627 0 12-5.373 12-12 0-6.628-5.373-12-12-12z"/></svg>'
        'Save Pin</button>'
        '</div>\n'
    )

    # Assemble complete body
    body = (
        '<div class="recipe-view"><div class="recipe-body">\n'
        '  <nav class="breadcrumb"><a href="' + esc(home_url) + '">Home</a> <span aria-hidden="true">&rsaquo;</span> '
        '  <a href="/category/' + esc(cat_slug) + '">' + esc(cat_label) + '</a> <span aria-hidden="true">&rsaquo;</span> '
        '  <span aria-current="page">' + esc(name) + '</span></nav>\n'
        '  <h1>' + esc(name) + '</h1>\n'
        '  <figure class="recipe-hero"><img class="hero" src="' + esc(img_url) + '" alt="' + esc(img_alt) + '"' + wh + ' loading="eager"></figure>\n'
        + facts_html
        + pubdate_html
        + '  <p class="intro">' + esc(tx.get('intro') or '') + '</p>\n'
        + video_html
        + rating_html
        + two_col_html
        + nut_html
        + tip_html
        + good_to_know_html
        + pairs_html
        + eeat_html
        + more_links
        + share_html
        + '</div></div>\n'
    )

    return page_shell(title, desc, url, img_url, img_alt,
                      recipe_json_ld(data, recipe, tx, url, lang, desc,
                                     video_date,
                                     article_date=article.get('published')),
                      body, og_type='article',
                      article_dates=article or None,
                      hreflang=hreflang_links(path),
                      html_lang=LANG_HREFLANG[lang],
                      current_path=path,
                      lang_code=lang)

def list_json_ld(li):
    cld = {"@context": "https://schema.org", "@type": "CollectionPage",
           "name": li['title'], "url": li['url'], "description": li['desc'],
           "isPartOf": {"@type": "WebSite", "name": "Zaika Worlds",
                        "url": SITE + "/"},
           "mainEntity": {"@type": "ItemList",
                          "numberOfItems": len(li['recipes']),
                          "itemListElement": [
                              {"@type": "ListItem", "position": i + 1,
                               "url": SITE + '/recipe/' + r['id'],
                               "name": r['name']}
                              for i, r in enumerate(li['recipes'])]}}
    bld = {"@context": "https://schema.org", "@type": "BreadcrumbList",
           "itemListElement": [
               {"@type": "ListItem", "position": 1, "name": "Home",
                "item": SITE + "/"},
               {"@type": "ListItem", "position": 2, "name": li['label'],
                "item": li['url']}]}
    return [cld, bld]


def list_page(data, li):
    title = cap_title(li['title'])
    cards = []
    for r in li['recipes']:
        wh = thumb_wh(r['img'], data['img_dims'])
        cards.append(
            '<div class="card"><a href="/recipe/%s">'
            '<img src="%s" alt="%s"%s loading="lazy" decoding="async"></a>'
            '<div><a href="/recipe/%s">%s</a>'
            '<p>%s &middot; %s &middot; %s</p></div></div>'
            % (esc(r['id']), esc(SITE + '/' + thumb_img(r['img'])),
               esc(r_text_en(r, data['extra']).get('alt') or ''), wh,
               esc(r['id']), esc(r['name']), esc(r['time']) + ' min',
               esc(r['servings']), esc(r['country'])))
    body = (
        '<nav class="crumb"><a href="/">Home</a> &rsaquo; '
        '<span>%s</span></nav>\n'
        '<h1>%s</h1>\n<p>%s</p>\n'
        '<a class="cta" href="/">Browse the interactive recipe finder '
        '&mdash; search, filter and switch language</a>\n'
        '%s\n'
        % (esc(li['label']), esc(li['title']), esc(li['intro']),
           '\n'.join(cards)))
    return page_shell(title, li['desc'], li['url'], li['img'], li['imgAlt'],
                      list_json_ld(li), body)


# Cross-links between the info pages (2026-10-31, audit "5 pages have
# only one incoming internal link"): each info page links the other two
# plus Cooking FAQs in its body, on top of the SITE_FOOTER links.
INFO_MORE = {
    'about': ('Questions? See <a href="/faqs">Cooking FAQs</a> or '
              '<a href="/contact">Contact Us</a>. Read our '
              '<a href="/privacy">Privacy Policy</a>.'),
    'privacy': ('Questions about the site? See <a href="/about">About Us</a>, '
                '<a href="/faqs">Cooking FAQs</a> or '
                '<a href="/contact">Contact Us</a>.'),
    'contact': ('Learn more <a href="/about">About Us</a>, read our '
                '<a href="/privacy">Privacy Policy</a> or browse '
                '<a href="/faqs">Cooking FAQs</a>.'),
}


def info_page(data, name):
    """about / privacy / contact, from INFO.en (English). Each page's meta
    description comes from its own intro (unique per page, never the
    shared homepage description)."""
    en = data['info']['en'][name]
    h1 = en['h1']
    title = cap_title(h1)
    url = SITE + '/' + name
    desc = fit_desc(en['intro'], '') or DEF_DESC
    if len(desc) < 140:
        # Pad with the first section's text (real page content only).
        extra = ''
        if name == 'about':
            extra = en.get('p1') or ''
        elif name == 'privacy':
            extra = (en.get('secP') or [''])[0]
        else:
            extra = en.get('notice') or ''
        if extra:
            desc = fit_desc(en['intro'] + ' ' + extra, '')
    if name == 'about':
        parts = ['<h1>%s</h1>\n<p>%s</p>\n' % (esc(h1), esc(en['intro']))]
        for h2k, pk in (('h2a', 'p1'), ('h2c', 'p3'), ('h2d', 'p4'),
                        ('h2e', 'p5'), ('h2f', 'p6')):
            parts.append('<h2>%s</h2>\n<p>%s</p>\n'
                         % (esc(en[h2k]), esc(en[pk])))
            if h2k == 'h2a':
                parts.append('<h3>%s</h3>\n<p>%s</p>\n<h3>%s</h3>\n<p>%s</p>\n'
                             % (esc(en['h3a1']), esc(en['p1b']),
                                esc(en['h3a2']), esc(en['p1c'])))
            if h2k == 'h2c':
                parts.append('<ul>\n%s\n</ul>\n'
                             % ''.join('<li>%s</li>' % esc(x)
                                       for x in en['howList']))
                parts.append('<h3>%s</h3>\n<p>%s</p>\n'
                             % (esc(en['h3c1']), esc(en['p3b'])))
            if h2k == 'h2d':
                parts.append('<h3>%s</h3>\n<p>%s</p>\n<h3>%s</h3>\n<p>%s</p>\n'
                             % (esc(en['h3d1']), esc(en['p4b']),
                                esc(en['h3d2']), esc(en['p4c'])))
            if h2k == 'h2e':
                parts.append('<ul>\n%s\n</ul>\n'
                             % ''.join('<li>%s</li>' % esc(x)
                                       for x in en['easyList']))
            if h2k == 'h2f':
                parts.append('<h3>%s</h3>\n<p>%s</p>\n'
                             % (esc(en['h3f1']), esc(en['p6b'])))
        parts.append('<p class="muted">%s</p>\n' % esc(en['note']))
        body_inner = ''.join(parts)
    elif name == 'privacy':
        parts = ['<h1>%s</h1>\n<p>%s</p>\n' % (esc(h1), esc(en['intro']))]
        for h, p in zip(en['secH'], en['secP']):
            parts.append('<h2>%s</h2>\n<p>%s</p>\n' % (esc(h), esc(p)))
        body_inner = ''.join(parts)
    else:  # contact
        body_inner = (
            '<h1>%s</h1>\n<p>%s</p>\n<p>%s</p>\n'
            '<p>Email: <a href="mailto:%s">%s</a></p>\n'
            '<p class="muted">%s</p>\n'
            % (esc(h1), esc(en['intro']), esc(en['notice']),
               CONTACT_EMAIL, CONTACT_EMAIL, esc(en['confirm'])))
    body = ('<nav class="crumb"><a href="/">Home</a> &rsaquo; '
            '<span>%s</span></nav>\n%s'
            '<a class="cta" href="/#%s">Open the interactive site</a>\n'
            '%s\n'
            % (esc(h1), body_inner, esc(name),
               '<p>' + INFO_MORE[name] + '</p>'))
    wld = {"@context": "https://schema.org", "@type": "WebPage",
           "name": title, "url": url, "description": desc,
           "isPartOf": {"@type": "WebSite", "name": "Zaika Worlds",
                        "url": SITE + "/"}}
    hub_img, hub_alt, _ = hub_og(data, '/' + name)
    return page_shell(title, desc, url, hub_img, hub_alt, [wld], body)


def make_list(title, desc, url, label, intro, recipes, img, img_alt):
    """A list_info-style dict for list_page(), for hand-made list pages
    (/recipes, /trending, hubs). desc must already be fitted 140-155."""
    return {'title': title, 'desc': desc, 'url': url, 'label': label,
            'intro': intro, 'recipes': recipes, 'img': img,
            'imgAlt': img_alt}


def new_list_pages(data):
    """The new list pages (issue B/O): /recipes, /trending, /eid-recipes,
    /ramadan-recipes. Returns {rel_path: html}."""
    by_id = {r['id']: r for r in data['recipes']}
    all_recipes = sorted(data['recipes'], key=lambda r: r['name'])
    first_img = all_recipes[0]['img']
    first_alt = r_text_en(all_recipes[0], data['extra']).get('alt') or ''
    pages = {}
    intro_all = ("All 46 Zaika Worlds recipes: Pakistani, Indian and world "
                 "food dishes with full ingredients, step by step methods, "
                 "cooking time and servings. Click any recipe to open the "
                 "full method and start cooking.")
    _hi, _ha, _ = hub_og(data, '/recipes')
    pages['recipes/index.html'] = list_page(data, make_list(
        'All Recipes', fit_desc(intro_all, ''),
        SITE + '/recipes', 'All Recipes', intro_all, all_recipes,
        _hi, _ha))
    # The 3 trending dishes are the UI trendCards (Chicken Biryani,
    # Beef Nihari, Gulab Jamun).
    trend_recipes = [by_id[i] for i in TREND_IDS]
    intro_trend = ui_str(data, 'en', 'trendP',
                         'If you are new here, start with these three.')
    _hi, _ha, _ = hub_og(data, '/trending')
    pages['trending/index.html'] = list_page(data, make_list(
        'Trending Recipes', fit_desc(intro_trend, ''),
        SITE + '/trending', 'Trending', intro_trend, trend_recipes,
        _hi, _ha))
    for slug, hub in HUBS.items():
        hub_recipes = [by_id[i] for i in hub['recipes']]
        _hi, _ha, _ = hub_og(data, '/' + slug)
        pages['%s/index.html' % slug] = list_page(data, make_list(
            hub['title'],
            fit_desc(hub['intro'], ''), SITE + '/' + slug,
            hub['title'], hub['intro'], hub_recipes,
            _hi, _ha))
    return pages


def faq_page(data):
    """The /faqs page (issue B/P): the same 10 cooking Q&As as the
    homepage FAQ, with FAQPage JSON-LD. All Q&As are verbatim from the
    recipes' EXTRA faq data (plus the one site-usage question, also
    verbatim from the site's own UI)."""
    entries = home_faq_entries(data)
    intro = ("Cooking questions answered from the recipes themselves: "
             "biryani, nihari, karahi, samosa, gulab jamun and more. "
             "Every answer comes from a real recipe on Zaika Worlds, "
             "with the full method on the recipe page.")
    parts = ['<nav class="crumb"><a href="/">Home</a> &rsaquo; '
             '<span>FAQs</span></nav>\n',
             '<h1>Cooking FAQs</h1>\n<p>%s</p>\n' % esc(intro)]
    for q, a in entries:
        parts.append('<h2>%s</h2>\n<p>%s</p>\n' % (esc(q), esc(a)))
    parts.append('<p><a href="/recipes">Browse all recipes</a></p>\n')
    fld = {"@context": "https://schema.org", "@type": "FAQPage",
           "mainEntity": [{"@type": "Question", "name": q,
                           "acceptedAnswer": {"@type": "Answer", "text": a}}
                          for q, a in entries]}
    wld = {"@context": "https://schema.org", "@type": "WebPage",
           "name": "Cooking FAQs | Zaika Worlds", "url": SITE + "/faqs",
           "description": fit_desc(intro, ''),
           "isPartOf": {"@type": "WebSite", "name": "Zaika Worlds",
                        "url": SITE + "/"}}
    hub_img, hub_alt, _ = hub_og(data, '/faqs')
    return page_shell('Cooking FAQs | Zaika Worlds', fit_desc(intro, ''),
                      SITE + '/faqs', hub_img, hub_alt, [wld, fld],
                      ''.join(parts))


def guide_page(data):
    """The /guides/dum-cooking page (issue O): one short technique guide
    from real tips/notes/steps in the biryani, karahi and nihari data,
    attributed to the recipes they come from."""
    intro = ("How to cook on dum: seal the lid, keep the heat low and let "
             "the steam finish the dish. Every tip below comes from the "
             "biryani, karahi and nihari recipes on Zaika Worlds, with "
             "the full method on each recipe page.")
    parts = ['<nav class="crumb"><a href="/">Home</a> &rsaquo; '
             '<span>Guides</span> &rsaquo; <span>Dum cooking</span></nav>\n',
             '<h1>Dum Cooking: Seal the Lid, Keep the Heat Low</h1>\n'
             '<p>%s</p>\n' % esc(intro)]
    for heading, paras in dum_guide_sections(data):
        parts.append('<h2>%s</h2>\n' % esc(heading))
        for p in paras:
            parts.append('<p>%s</p>\n' % esc(p))
    parts.append('<p><a href="/recipe/biryani">Chicken Biryani recipe</a>'
                 ' &middot; <a href="/recipe/karahi">Chicken Karahi '
                 'recipe</a> &middot; <a href="/recipe/nihari">Beef Nihari '
                 'recipe</a></p>\n')
    wld = {"@context": "https://schema.org", "@type": "WebPage",
           "name": "Dum Cooking Guide | Zaika Worlds",
           "url": SITE + "/guides/dum-cooking",
           "description": fit_desc(intro, ''),
           "isPartOf": {"@type": "WebSite", "name": "Zaika Worlds",
                        "url": SITE + "/"}}
    hub_img, hub_alt, _ = hub_og(data, '/guides/dum-cooking')
    return page_shell('Dum Cooking Guide | Zaika Worlds',
                      fit_desc(intro, ''), SITE + '/guides/dum-cooking',
                      hub_img, hub_alt, [wld], ''.join(parts))


def language_home_page(data, lang):
    """Static homepage for a language (issue N): the translated hero
    title + hero sub-text, a static grid of all 46 recipes linking to
    the language recipe pages, and hreflang for every variant. The
    English homepage is the slim index.html; this is for the 12
    non-English languages only."""
    prefix = LANG_PREFIX[lang]
    url = lang_url('/', lang)
    ht = re.sub(r'</?em>', '', ui_str(data, lang, 'heroTitle', ''))
    title = cap_title(ht + ' | Zaika Worlds')
    desc = fit_desc(ui_str(data, lang, 'heroSub', ''), '')
    cards = []
    for r in sorted(data['recipes'], key=lambda x: lang_name(x, data, lang)):
        wh = thumb_wh(r['img'], data['img_dims'])
        cards.append(
            '<div class="card"><a href="%s">'
            '<img src="%s" alt="%s"%s loading="lazy" decoding="async"></a>'
            '<div><a href="%s">%s</a>'
            '<p>%s %s &middot; %s &middot; %s</p></div></div>'
            % (esc(lang_url('/recipe/' + r['id'], lang)),
               esc(SITE + '/' + thumb_img(r['img'])),
               esc(lang_alt(r, data, lang)), wh,
               esc(lang_url('/recipe/' + r['id'], lang)),
               esc(lang_name(r, data, lang)),
               esc(r['time']), esc(data['ui_min'].get(lang, 'min')),
               esc(lang_servings(r, data, lang)),
               esc(r['country'])))
    body = ('<h1>%s</h1>\n<p>%s</p>\n'
            '<a class="cta" href="%s">%s</a>\n%s\n'
            % (esc(ht), esc(ui_str(data, lang, 'heroSub', '')),
               esc('/?lang=' + lang),
               esc(ui_cta(data, lang)),
               '\n'.join(cards)))
    wld = {"@context": "https://schema.org", "@type": "WebPage",
           "name": title, "url": url, "description": desc,
           "isPartOf": {"@type": "WebSite", "name": "Zaika Worlds",
                        "url": SITE + "/"}}
    return page_shell(title, desc, url, DEF_IMG, DEF_ALT, [wld], body,
                      hreflang=hreflang_links('/'),
                      html_lang=LANG_HREFLANG[lang],
                      current_path='/',
                      lang_code=lang)


def write_static_pages(data):
    """Write all static pages. Returns {path: bytes}. English recipe
    pages at /recipe/<slug>; language recipe pages at
    /<prefix>/recipe/<slug> and language homepages at /<prefix>/ (all 12
    non-English languages — their data is complete, 46/46)."""
    out = {}
    dates = load_recipe_dates()

    def w(rel, text):
        path = os.path.join(ROOT, rel)
        write(path, text)
        out[rel] = len(text.encode('utf-8'))

    for r in data['recipes']:
        w('recipe/%s/index.html' % r['id'],
          recipe_page(data, r, 'en', dates))
        for lang in LANGS[1:]:
            prefix = LANG_PREFIX[lang]
            w('%s/recipe/%s/index.html' % (prefix, r['id']),
              recipe_page(data, r, lang, dates))
    for lang in LANGS[1:]:
        w('%s/index.html' % LANG_PREFIX[lang],
          language_home_page(data, lang))
    for slug in sorted(data['cat_by_slug']):
        li = list_info(data, 'category', slug)
        w('category/%s/index.html' % slug, list_page(data, li))
    for slug in sorted(data['country_by_slug']):
        li = list_info(data, 'country', slug)
        w('country/%s/index.html' % slug, list_page(data, li))
    for name in ('about', 'privacy', 'contact'):
        w('%s/index.html' % name, info_page(data, name))
    for rel, html in new_list_pages(data).items():
        w(rel, html)
    w('faqs/index.html', faq_page(data))
    w('guides/dum-cooking/index.html', guide_page(data))
    return out


# ---------------------------------------------------------------------------
# H1 fix (exactly one <h1> per served page in raw HTML) + heading promotion
# ---------------------------------------------------------------------------

H1_HTML = {
    '<h1 id="aboutH1">About Us</h1>':
        '<h2 class="view-h1" id="aboutH1">About Us</h2>',
    '<h1 id="privacyH1">Privacy Policy</h1>':
        '<h2 class="view-h1" id="privacyH1">Privacy Policy</h2>',
    '<h1 id="contactH1">Contact Us</h1>':
        '<h2 class="view-h1" id="contactH1">Contact Us</h2>',
    '<h1 id="notFoundH1" tabindex="-1">Recipe not found</h1>':
        '<h2 class="view-h1" id="notFoundH1" tabindex="-1">'
        'Recipe not found</h2>',
    '<h1 id="listH1" tabindex="-1"></h1>':
        '<h2 class="view-h1" id="listH1" tabindex="-1"></h2>',
}

CSS_FIX = [
    ('.info-view h1{', '.info-view h1,.info-view h2.view-h1{'),
    ('.hero h1{', '.hero h1,.hero h2.view-h1{'),
    ('.hero h1 em{', '.hero h1 em,.hero h2.view-h1 em{'),
    ('.recipe-view h1{', '.recipe-view h1,.recipe-view h2.view-h1{'),
]
# list/notFound headings have no specific rule today (UA default h1 2em);
# give the demoted h2 the same size so the 404/list views look identical.
LIST_H1_CSS = ('#listView h2.view-h1,#notFoundView h2.view-h1'
               '{font-size:2em;margin:.67em 0}')

PROMOTION_JS = (
    'var _VIEW_H1={home:"heroTitle",about:"aboutH1",privacy:"privacyH1",'
    'contact:"contactH1",list:"listH1",notfound:"notFoundH1",'
    'recipe:"recipeTitle"};\n'
    'function _swapHeading(id,tag){var el=document.getElementById(id);'
    'if(!el||el.tagName.toLowerCase()===tag)return;'
    'var n=document.createElement(tag);'
    'for(var i=0;i<el.attributes.length;i++)'
    '{n.setAttribute(el.attributes[i].name,el.attributes[i].value);}'
    'while(el.firstChild)n.appendChild(el.firstChild);'
    'el.parentNode.replaceChild(n,el);}\n'
    'function promoteH1(view){var keep=_VIEW_H1[view];'
    'for(var v in _VIEW_H1){var id=_VIEW_H1[v];if(!id)continue;'
    'var el=document.getElementById(id);if(!el)continue;'
    'if(id===keep){_swapHeading(id,"h1");}else{_swapHeading(id,"h2");}}}\n')


def apply_h1_fix(html):
    """Demote the 5 non-hero <h1> to <h2 class="view-h1"> + CSS. Idempotent."""
    out = html
    for old, new in H1_HTML.items():
        if old in out:
            out = out.replace(old, new)
        elif new not in out:
            raise JSError("H1 fix anchor missing (already changed?): %r"
                          % old[:60])
    for old, new in CSS_FIX:
        if old in out:
            out = out.replace(old, new, 1)
        elif new not in out:
            raise JSError("CSS fix anchor missing: %r" % old)
    if LIST_H1_CSS not in out:
        anchor = ('.recipe-view h1,.recipe-view h2.view-h1{'
                  'font-size:clamp(34px,4.6vw,50px);margin:0 0 12px;'
                  'font-weight:600}')
        if anchor not in out:
            raise JSError("CSS anchor for list H1 rule missing")
        out = out.replace(anchor, anchor + LIST_H1_CSS, 1)
    return out


def apply_promotion(html):
    """Insert promoteH1() and call it at the top of showView(). Idempotent."""
    out = html
    if 'function promoteH1' not in out:
        anchor = 'function showView(name){'
        if anchor not in out:
            raise JSError("showView anchor missing")
        out = out.replace(anchor, PROMOTION_JS + anchor, 1)
    hook_old = 'function showView(name){\n  CURRENT_VIEW=name;'
    hook_new = ('function showView(name){\n  promoteH1(name);\n'
                '  CURRENT_VIEW=name;')
    if hook_old in out:
        out = out.replace(hook_old, hook_new, 1)
    elif hook_new not in out:
        raise JSError("showView hook anchor missing")
    return out


# ---------------------------------------------------------------------------
# Slim SPA shell
# ---------------------------------------------------------------------------

SETLANG_SYNC = 'function setLang(l){LANG=l;applyLang();}'
SETLANG_ASYNC = ('function setLang(l){if(l===LANG){applyLang();return;}'
                 'LANG=l;_ensureLangData(l).then(function(){applyLang();})'
                 '.catch(function(){applyLang();});}')

LOADER_JS = """/* ZAIKA_SLIM_BUILD: the big data blocks live in data/*.js (generated
   by build_site.py from index.html). English loads first; other languages
   load on demand when the language menu changes. */
function _loadScript(src){return new Promise(function(res,rej){var s=document.createElement("script");s.src=cleanPath(src);s.onload=function(){res();};s.onerror=function(){rej(new Error("failed to load "+src));};document.head.appendChild(s);});}
var _loadedLangs={};
function _mergeExtraLang(lang,obj){for(var id in obj){if(!EXTRA[id])EXTRA[id]={};EXTRA[id][lang]=obj[id];}}
function _mergeLangData(lang,obj){for(var id in obj){if(!LANG_DATA[id])LANG_DATA[id]={};LANG_DATA[id][lang]=obj[id];}}
var _loadedExtra={};
function _ensureExtra(lang){
  if(_loadedExtra[lang])return Promise.resolve();
  _loadedExtra[lang]=true;
  return _loadScript("data/extra-"+lang+".js").then(function(){var g=window["ZAIKA_EXTRA_"+lang.toUpperCase()];if(g)_mergeExtraLang(lang,g);});
}
var _loadedLangNew=false;
function _ensureLangNew(){
  if(_loadedLangNew)return Promise.resolve();
  _loadedLangNew=true;
  return _loadScript("data/lang-new.js").then(function(){try{_mergeLangNew();}catch(e){if(window.console&&console.error)console.error(e);}});
}
function _ensureLangData(lang){
  if(lang==="en"||_loadedLangs[lang])return Promise.resolve();
  _loadedLangs[lang]=true;
  var jobs=[_ensureExtra(lang),_loadScript("data/ui-"+lang+".js").then(function(){var u=window["ZAIKA_UI_"+lang.toUpperCase()];var inf=window["ZAIKA_INFO_"+lang.toUpperCase()];if(u)UI[lang]=u;if(inf)INFO[lang]=inf;})];
  if(lang==="hi"||lang==="ru"){jobs.push(_loadScript("data/lang-data-"+lang+".js").then(function(){var g=window["ZAIKA_LANGDATA_"+lang.toUpperCase()];if(g)_mergeLangData(lang,g);}));}
  return _ensureLangNew().then(function(){return Promise.all(jobs);});
}
(function _initZaika(){
  Promise.all([_loadScript("data/recipes.js"),_loadScript("data/ui-en.js")]).then(function(){return _ensureLangData(LANG);}).then(function(){applyLang();applyRoute();}).catch(function(e){if(window.console&&console.error)console.error(e);if(RECIPES&&RECIPES.length){applyLang();applyRoute();}else{document.body.innerHTML="<p style='font-family:sans-serif;padding:40px'>Zaika Worlds could not load its recipe data. Please refresh the page.</p>";}});
})();
"""

# The LANG_NEW merge, verbatim from index.html except: wrapped in a function
# (it used to run at script load and read RECIPES.length, which is null
# until data/recipes.js loads), an early return if the data is missing, and
# a defensive LANG_DATA[_id] creation (in the fat file LANG_DATA[_id]
# always exists because hi/ru are inline; in the slim file hi/ru load
# lazily, so the entry may not exist yet).
MERGE_LANG_NEW_JS = """function _mergeLangNew(){
  if(!LANG_NEW_RAW||!LANG_NEW_RAW2||!LANG_NEW_RAW3||!RECIPES)return;
  var LANG_NEW_ALL={};
  [LANG_NEW_RAW,LANG_NEW_RAW2,LANG_NEW_RAW3].forEach(function(_src){for(var _k in _src){var _t=LANG_NEW_ALL[_k]||(LANG_NEW_ALL[_k]={});for(var _l in _src[_k]){_t[_l]=_src[_k][_l];}}});
  for(var _id in LANG_NEW_ALL){var _e=LANG_NEW_ALL[_id];var _base=null;for(var _bi=0;_bi<RECIPES.length;_bi++){if(RECIPES[_bi].id===_id){_base=RECIPES[_bi];break;}}var _cat=_e.cat||(_base?_base.cat:"desi");var _di=_e.diff;if(_di===undefined&&_base){_di={Easy:0,Medium:1,Hard:2}[_base.diff];if(_di===undefined)_di=1;}var _sv=_e.serv;if(_sv===undefined&&_base)_sv=parseInt(_base.servings,10)||4;if(!LANG_DATA[_id])LANG_DATA[_id]={};for(var _l in _e){if(_l==="cat"||_l==="diff"||_l==="serv")continue;var _a=_e[_l];LANG_DATA[_id][_l]={name:_a[0],catLabel:_CL[_l][_cat],diff:_DF[_l][_di],servings:_sv+" "+_SV[_l],desc:_a[1],alt:_a[2]};}}
}
"""


def _stmt_span(src, anchor, opener):
    """Span of one `var X = <literal>;` statement (whole statement incl. ';').

    The span starts at the anchor (the `var ...` keyword), not at the
    literal, so the replacement fully replaces the statement.
    """
    i = src.find(anchor)
    if i < 0:
        raise JSError("anchor not found: %r" % anchor)
    raw, start, end = find_literal(src, anchor, opener)
    semi = src.find(';', end)
    if semi < 0:
        raise JSError("no ';' after %r" % anchor)
    return i, semi + 1


def thumb_img(img):
    """600px thumbnail path for a recipe photo (PageSpeed 2026-10-31:
    cards display at most ~563px wide, so the 1792px originals were
    ~5x oversized. Thumbs live in assets/thumbs/<base>-600.webp and are
    generated from the same unique AI photo."""
    return img.replace('assets/', 'assets/thumbs/').replace('.webp', '-600.webp')


def thumb_wh(img, img_dims):
    """width/height attrs for the 600px thumbnail of img (kills CLS)."""
    dims = img_dims.get(img, [])
    if len(dims) == 2 and dims[0]:
        return ' width="600" height="%d"' % round(600 * dims[1] / dims[0])
    return ''


def static_grid_html(data):
    """The homepage recipe grid as static HTML (issue M): all 46 recipe
    cards in the same <article class="pin"> markup the SPA's cardHtml()
    produces, so the homepage shows real content in raw HTML without JS.
    The SPA's render() replaces this grid on load, so filters keep
    working. Links point at the static /recipe/<slug> pages."""
    cards = []
    for r in sorted(data['recipes'], key=lambda x: x['name']):
        tx = r_text_en(r, data['extra'])
        wh = thumb_wh(r['img'], data['img_dims'])
        badge = r['country'] if r['cat'] == 'world' else r['catLabel']
        veg = '🥬 Veg' if r['veg'] == 'veg' else '🍖 Non-Veg'
        cards.append(
            '<article class="pin">'
            '<div class="pin-img %s"><a class="img-open" href="/recipe/%s" '
            'data-open="%s" aria-label="Open recipe: %s">'
            '<img src="/%s" alt="%s" loading="lazy" decoding="async"%s></a>'
            '<span class="cat-badge">%s</span></div>'
            '<a class="pin-body" href="/recipe/%s" data-open="%s">'
            '<h3>%s</h3><p>%s</p>'
            '<span class="meta"><span><span aria-hidden="true">⏱</span> '
            '<b>%s min</b></span><span><span aria-hidden="true">👥</span> '
            '<b>%s</b></span><span><span aria-hidden="true">📊</span> '
            '<b>%s</b></span><span>%s</span><span>%s</span></span>'
            '</a></article>'
            % (esc(r['shape']), esc(r['id']), esc(r['id']),
               esc(r['name']), esc(thumb_img(r['img'])), esc(tx.get('alt') or ''),
               wh, esc(badge), esc(r['id']), esc(r['id']),
               esc(r['name']), esc(tx.get('desc') or ''),
               esc(r['time']), esc(r['servings']), esc(r['diff']),
               esc(veg), esc(r['country'])))
    return ''.join(cards)


def homepage_faq_json_ld(data):
    """FAQPage JSON-LD for the homepage FAQ (issue P): the same 10
    cooking Q&As as the HTML articles and the /faqs page."""
    entries = home_faq_entries(data, 'en')
    fld = {"@context": "https://schema.org", "@type": "FAQPage",
           "mainEntity": [{"@type": "Question", "name": q,
                           "acceptedAnswer": {"@type": "Answer", "text": a}}
                          for q, a in entries]}
    return ('<script type="application/ld+json">%s</script>\n'
            % js_json(fld))


def build_slim(src, data):
    """Return the slim index.html (data externalised, H1 fixed, loader)."""
    out = src
    # 1. H1 fix + heading promotion (idempotent; also applied to the source
    #    by --source-fix, so this is usually a no-op here).
    out = apply_h1_fix(out)
    out = apply_promotion(out)
    # 2. Async language switching (slim only — the fat source keeps the
    #    synchronous setLang, since its data is inline).
    if SETLANG_SYNC in out:
        out = out.replace(SETLANG_SYNC, SETLANG_ASYNC, 1)
    elif SETLANG_ASYNC not in out:
        raise JSError("setLang anchor missing")

    # 3. Replace data statements with empty declarations / deletions.
    #    Compute spans on the ORIGINAL text, then rebuild. (Spans must not
    #    overlap; data statements are disjoint.)
    spans = []  # (start, end, replacement)

    def add(anchor, opener, repl):
        s, e = _stmt_span(out, anchor, opener)
        spans.append((s, e, repl))

    add('var RECIPES=[', '[', 'var RECIPES=null;')
    add('var EXTRA={', '{', 'var EXTRA={};')
    add('var LANG_DATA={', '{', 'var LANG_DATA={};')
    add('var LANG_NEW_RAW=', '{', 'var LANG_NEW_RAW=null;')
    add('var LANG_NEW_RAW2=', '{', 'var LANG_NEW_RAW2=null;')
    add('var LANG_NEW_RAW3=', '{', 'var LANG_NEW_RAW3=null;')
    add('var UI={', '{', 'var UI={};')
    add('var INFO={', '{', 'var INFO={};')
    add('var EXTRA_NEW={', '{', '')
    # LANG_NEW merge (forEach + for loop) -> _mergeLangNew() function.
    # Span: from `var LANG_NEW_ALL={};` to the end of the for loop.
    _ln_i = out.find('var LANG_NEW_ALL={};')
    if _ln_i < 0:
        raise JSError("LANG_NEW_ALL merge anchor missing")
    _for_i = out.find('for(var _id in LANG_NEW_ALL)', _ln_i)
    if _for_i < 0:
        raise JSError("LANG_NEW_ALL for-loop anchor missing")
    _brace = out.find('{', _for_i)
    _, _for_end = raw_braced(out, _brace)
    spans.append((_ln_i, _for_end, MERGE_LANG_NEW_JS))
    # UI.<lang> assignments (10) — delete.
    for m in re.finditer(r'(?<=[\n;])UI\.([a-z]+)\s*=\s*\{', out):
        j = out.find('{', m.start())
        _, e2 = raw_braced(out, j)
        semi = out.find(';', e2)
        spans.append((m.start(), semi + 1, ''))
    # UI patch statements (UI.en/ru/hi.<key>=...;) — delete; they now live
    # in the per-language UI data files. Re-scan on the current text (the
    # H1 fix above shifted offsets, so the spans from extract_all are stale).
    _patch_n = 0
    for m in re.finditer(r'(?<![\w.])UI\.(en|ru|hi)\.([A-Za-z0-9_]+)\s*=',
                         out):
        _, v_end = parse_js_literal(out, m.end())
        semi = out.find(';', v_end)
        spans.append((m.start(), semi + 1, ''))
        _patch_n += 1
    if _patch_n != 81:
        raise JSError("expected 81 UI patch statements, found %d" % _patch_n)
    # EXTRA_NEW per-recipe assignments + whole-language literals — delete.
    # NOTE (2026-11-04): the regex must match BOTH dot notation
    # (EXTRA_NEW.es.chapli=[...]) AND bracket notation
    # (EXTRA_NEW.es["seekh-kebab"]=[...]). The 10 new recipes added
    # 2026-11-03/04 use bracket notation for hyphenated ids; the old
    # dot-only regex left those 20 assignments in the slim output while
    # the `var EXTRA_NEW={...}` declaration was deleted, so the slim
    # page threw "EXTRA_NEW is not defined", RECIPES stayed null, and
    # every homepage recipe click did nothing. Mirror the extraction
    # regex (line 1533), which already handles both forms.
    for m in re.finditer(r'(?<=[\n;])EXTRA_NEW\.([a-z]+)(?:\.([a-z0-9_-]+)|\["([a-z0-9_-]+)"\])\s*=\s*\[', out):
        # The regex match ends on the array '[' itself, so use m.end()-1:
        # out.find('[', m.start()) would land on the '[' inside
        # ["chicken-korma"] for bracket notation, and raw_braced would
        # then stop at the id's ']' — leaving the array tail behind as
        # a syntax error (2026-11-04: this broke the slim build).
        j = m.end() - 1
        _, e2 = raw_braced(out, j)
        semi = out.find(';', e2)
        spans.append((m.start(), semi + 1, ''))
    for m in re.finditer(r'(?<=[\n;])EXTRA_NEW\.([a-z]+)\s*=\s*\{', out):
        j = out.find('{', m.start())
        _, e2 = raw_braced(out, j)
        semi = out.find(';', e2)
        spans.append((m.start(), semi + 1, ''))
    # Tail: merge loop + applyLang()/applyRoute() -> loader.
    tail_i = out.find('for(var _L in EXTRA_NEW)')
    if tail_i < 0:
        raise JSError("merge-loop tail anchor missing")
    tail_j = out.find('</script>', tail_i)
    if tail_j < 0:
        raise JSError("closing </script> after merge loop missing")
    spans.append((tail_i, tail_j, LOADER_JS))

    spans.sort()
    for (s1, e1, _), (s2, e2, _) in zip(spans, spans[1:]):
        if s2 < e1:
            raise JSError("overlapping replacement spans at %d / %d"
                          % (s1, s2))
    parts = []
    pos = 0
    for s, e, repl in spans:
        parts.append(out[pos:s])
        parts.append(repl)
        pos = e
    parts.append(out[pos:])
    out = ''.join(parts)

    # 4. Build marker (guards extract_all against re-running on slim output).
    out = out.replace('<html lang="en">',
                      '<html lang="en">\n<!-- ' + SLIM_MARKER + ' -->', 1)
    # 5. Static recipe grid (issue M): inject the 36 cards into the
    #    homepage grid placeholder so the raw HTML shows real content
    #    without JS. The SPA's render() replaces this on load.
    grid_anchor = '<div class="masonry" id="grid"><!-- cards injected by JS --></div>'
    if grid_anchor not in out:
        raise JSError("homepage grid anchor missing")
    out = out.replace(grid_anchor,
                      '<div class="masonry" id="grid">'
                      + static_grid_html(data) + '</div>', 1)
    # 6. Homepage FAQPage JSON-LD (issue P): inject before </head>.
    if '</head>' not in out:
        raise JSError("closing </head> missing")
    out = out.replace('</head>', homepage_faq_json_ld(data) + '</head>', 1)
    # 7. Hreflang for the English homepage (Screaming Frog "Missing
    #    reciprocal link", 2026-10-31): the 12 language homepages link
    #    hreflang="en" to /, but / carried no hreflang at all, so none
    #    of them had a return link. The fat source keeps no hreflang
    #    in <head>; the slim homepage gets the full set here, built by
    #    the same hreflang_links('/') the language homepages use, so
    #    every return link matches exactly.
    hl = ''.join('<link rel="alternate" hreflang="%s" href="%s">\n'
                 % (code, href) for code, href in hreflang_links('/'))
    out = out.replace('</head>', hl + '</head>', 1)
    return out


# ---------------------------------------------------------------------------
# vercel.json: build command + trailing-slash rewrites
# ---------------------------------------------------------------------------

def update_vercel():
    path = os.path.join(ROOT, 'vercel.json')
    with open(path, encoding='utf-8') as f:
        cfg = json.load(f)
    changed = []
    if cfg.get('buildCommand') != 'python3 build_site.py':
        cfg['buildCommand'] = 'python3 build_site.py'
        changed.append('buildCommand=python3 build_site.py')
    # The build generates files in place (repo root). Without this, Vercel
    # looks for a "public" output directory after the build and fails with
    # STATIC_BUILD_NO_OUT_DIR.
    if cfg.get('outputDirectory') != '.':
        cfg['outputDirectory'] = '.'
        changed.append('outputDirectory=.')
    # Edge caching for HTML pages (Screaming Frog "Slow page", 2026-10-31):
    # Vercel's default is "max-age=0, must-revalidate", so every page view
    # revalidates with origin and TTFB spikes over 1s on cold fetches
    # (Ramen was flagged at 1,067ms while the other recipes were under 1s).
    # Browsers cache 60s, the edge caches 1h with stale-while-revalidate
    # for a day; deploys purge the edge cache, so new content still goes
    # live immediately. The /assets/ rule below comes later and wins for
    # fingerprinted assets, which keep immutable 1-year caching.
    headers = cfg.setdefault('headers', [])
    cache_rule = None
    for r in headers:
        if r.get('source') == '/(.*)':
            cache_rule = r
            break
    if cache_rule is None:
        cache_rule = {'source': '/(.*)', 'headers': []}
        headers.insert(0, cache_rule)
        changed.append('headers: added /(.*) rule')
    cheaders = cache_rule.setdefault('headers', [])
    want_cc = ('public, max-age=60, s-maxage=3600, '
               'stale-while-revalidate=86400')
    have_cc = [h for h in cheaders if h.get('key') == 'Cache-Control']
    if not have_cc:
        cheaders.append({'key': 'Cache-Control', 'value': want_cc})
        changed.append('headers: HTML edge-cache Cache-Control added')
    elif have_cc[0].get('value') != want_cc:
        have_cc[0]['value'] = want_cc
        changed.append('headers: HTML edge-cache Cache-Control updated')
    rewrites = cfg.setdefault('rewrites', [])
    have = {(r.get('source'), r.get('destination')) for r in rewrites}
    for src_pat in ('/recipe/:slug/', '/category/:slug/', '/country/:slug/'):
        pair = (src_pat, '/index.html')
        if pair not in have:
            rewrites.insert(0, {'source': src_pat,
                                'destination': '/index.html'})
            changed.append('rewrite %s -> /index.html' % src_pat)
    if changed:
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(cfg, f, indent=2)
            f.write('\n')
    return changed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _read_index():
    path = os.path.join(ROOT, 'index.html')
    with open(path, encoding='utf-8') as f:
        return f.read(), path


def _print_summary(fat_bytes, slim_bytes, data_files, static_pages):
    print('index.html (source, fat): %d bytes' % fat_bytes)
    print('index.html (slim build):  %d bytes' % slim_bytes)
    print('data files: %d (%d bytes total)'
          % (len(data_files), sum(data_files.values())))
    print('static pages: %d (%d bytes total)'
          % (len(static_pages), sum(static_pages.values())))


def generate_sitemap(data):
    """Regenerate sitemap.xml from the same source of truth as the static
    pages (issue Q): every route the build writes gets a <loc>, so the
    sitemap cannot go stale. No <lastmod>: no per-page modification date
    is recorded for these pages, and inventing one would be a fake date.
    Returns the URL count."""
    urls = generate_sitemap_urls(data)
    body = '\n'.join('  <url>\n    <loc>%s</loc>\n  </url>' % u
                      for u in urls)
    text = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!-- Sitemap for Zaika Worlds, https://www.zaikaworlds.com/ -->\n'
            '<!-- Generated by build_site.py from the same source of truth '
            'as the static pages; do not hand-edit. -->\n'
            '<!-- Clean URLs: home, /recipe/<slug>, /category/<slug>, '
            '/country/<slug>, /about, /privacy, /contact, /recipes, '
            '/trending, /faqs, hubs, guides, and /<lang>/recipe/<slug> '
            'language pages. -->\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + body + '\n</urlset>\n')
    write(os.path.join(ROOT, 'sitemap.xml'), text)
    return len(urls)


def build_feed(recipes):
    """Regenerate feed.xml (Pinterest RSS) from RECIPES so it can never go
    stale: every recipe in the site gets one <item>, in RECIPES order.
    Title = name, description = intro (NOT desc), enclosure length = the
    image file's size in bytes. The output matches the committed feed.xml
    byte-for-byte except lastBuildDate (the current build time), so a
    diff of a regenerated feed shows only that one line. Returns the
    item count."""
    now = email.utils.formatdate(usegmt=True)
    items = []
    for r in recipes:
        img = r['img']
        size = os.path.getsize(os.path.join(ROOT, img))
        items.append(
            '    <item>\n'
            '      <title>%s</title>\n'
            '      <link>%s/recipe/%s</link>\n'
            '      <guid isPermaLink="true">%s/recipe/%s</guid>\n'
            '      <description>%s</description>\n'
            '      <enclosure url="%s/%s" type="image/webp" length="%d" />\n'
            '      <media:content url="%s/%s" type="image/webp" '
            'medium="image" />\n'
            '    </item>' % (esc(r['name']), SITE, r['id'], SITE, r['id'],
                             esc(r['intro']), SITE, img, size, SITE, img))
    head = (
        "<?xml version='1.0' encoding='utf-8'?>\n"
        '<rss xmlns:media="http://search.yahoo.com/mrss/" version="2.0">\n'
        '  <channel>\n'
        '    <title>Zaika Worlds</title>\n'
        '    <link>%s/</link>\n'
        '    <description>%s</description>\n'
        '    <language>en</language>\n'
        '    <lastBuildDate>%s</lastBuildDate>\n'
        % (SITE, esc(DEF_DESC), now))
    text = head + '\n'.join(items) + '\n  </channel>\n</rss>'
    write(os.path.join(ROOT, 'feed.xml'), text)
    return len(items)


def webp_dims(path):
    """Width/height of a WebP file, stdlib only (VP8 / VP8L / VP8X)."""
    with open(path, 'rb') as f:
        head = f.read(30)
    if head[:4] != b'RIFF' or head[8:12] != b'WEBP':
        raise ValueError('%s: not a WebP' % path)
    kind = head[12:16]
    if kind == b'VP8X':
        return (int.from_bytes(head[24:27], 'little') + 1,
                int.from_bytes(head[27:30], 'little') + 1)
    if kind == b'VP8L':
        v = int.from_bytes(head[21:25], 'little')
        return ((v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1)
    if kind == b'VP8 ':
        return (int.from_bytes(head[26:28], 'little') & 0x3FFF,
                int.from_bytes(head[28:30], 'little') & 0x3FFF)
    raise ValueError('%s: unknown WebP chunk %r' % (path, kind))


def _lum(hexs):
    """Relative luminance of a #rrggbb colour (WCAG)."""
    hexs = hexs.lstrip('#')
    rgb = [int(hexs[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    rgb = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
           for c in rgb]
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def _contrast(fg, bg):
    l1, l2 = _lum(fg), _lum(bg)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


def validate_build(data):
    """Full build validation (issue Q + future-proofing): generates every
    static page in memory and FAILS on regressions, so a bad recipe or a
    broken generator cannot reach production. Called by --check. Checks:
    no raw Python lists; titles <=60; English recipe descriptions
    140-155 and unique; every description <=155; canonical + og:image +
    og:type on every page; exactly one H1; JSON-LD parses with required
    Recipe fields; split ingredients have no qualifier orphans; TREND_IDS
    match the UI trendCards; sitemap URLs match the pages built."""
    problems = []
    dates = load_recipe_dates()
    if not os.path.exists(os.path.join(ROOT, 'recipe_dates.json')):
        problems.append('recipe_dates.json missing from the repo root '
                        '(tools/ is vercelignored — the file must live at '
                        'the root or all article/video dates are silently '
                        'dropped from the production build)')
    if not os.path.exists(os.path.join(ROOT, 'nutrition.json')):
        problems.append('nutrition.json missing from the repo root '
                        '(tools/ is vercelignored — the file must live at '
                        'the root or the Recipe nutrition field is silently '
                        'dropped from the production build)')
    for r in data['recipes']:
        vids = r.get('videos') or {}
        for lang in LANGS:
            if vids.get(lang):
                vd = (dates.get('video') or {}).get(r['id'], {})
                if not (isinstance(vd, dict) and vd.get(lang)):
                    problems.append('%s: video %s has no uploadDate in '
                                    'recipe_dates.json' % (r['id'], lang))
        if r['id'] not in (dates.get('article') or {}):
            problems.append('%s: no article date in recipe_dates.json'
                            % r['id'])
    # PageSpeed (2026-10-31): IMG_DIMS must be the real file dimensions
    # (stale dims caused CLS) and every recipe photo must have a 600px
    # thumbnail in assets/thumbs/ (cards display at most ~563px wide).
    for r in data['recipes']:
        img = r['img']
        path = os.path.join(ROOT, img)
        try:
            real = webp_dims(path)
        except Exception as e:
            problems.append('%s: cannot read image dims: %s' % (img, e))
            continue
        want = data['img_dims'].get(img, [])
        if list(real) != list(want):
            problems.append('%s: IMG_DIMS %r != real dims %r (stale dims '
                            'cause layout shift)' % (img, want, list(real)))
        thumb = thumb_img(img)
        tpath = os.path.join(ROOT, thumb)
        if not os.path.exists(tpath):
            problems.append('%s: missing thumbnail %s (cards must use the '
                            '600px thumb, not the full photo)' % (img, thumb))
        else:
            try:
                td = webp_dims(tpath)
            except Exception as e:
                problems.append('%s: cannot read thumbnail dims: %s'
                                % (thumb, e))
                td = None
            if td and td != (600, round(600 * real[1] / real[0])):
                problems.append('%s: thumbnail dims %r, expected 600x%d'
                                % (thumb, td, round(600 * real[1] / real[0])))
    pages = {}  # rel path -> html

    def add(rel, html):
        pages[rel] = html

    for r in data['recipes']:
        add('recipe/%s/index.html' % r['id'],
            recipe_page(data, r, 'en', dates))
        for lang in LANGS[1:]:
            add('%s/recipe/%s/index.html' % (LANG_PREFIX[lang], r['id']),
                recipe_page(data, r, lang, dates))
    for lang in LANGS[1:]:
        add('%s/index.html' % LANG_PREFIX[lang],
            language_home_page(data, lang))
    for slug in sorted(data['cat_by_slug']):
        li = list_info(data, 'category', slug)
        add('category/%s/index.html' % slug, list_page(data, li))
    for slug in sorted(data['country_by_slug']):
        li = list_info(data, 'country', slug)
        add('country/%s/index.html' % slug, list_page(data, li))
    for name in ('about', 'privacy', 'contact'):
        add('%s/index.html' % name, info_page(data, name))
    for rel, html in new_list_pages(data).items():
        add(rel, html)
    add('faqs/index.html', faq_page(data))
    add('guides/dum-cooking/index.html', guide_page(data))

    def _anchor_problems(rel, html):
        """Anchor-text / alt / wa.me guards (Ahrefs audit 2026-10-31).
        Every <a> must have visible text, a non-empty img alt, or an
        aria-label; no img may have an empty alt; and no literal wa.me
        URL may appear anywhere (WhatsApp 429s crawlers, so a plain
        wa.me href is flagged as a broken external link — the share
        URL is built on click instead, see SHARE_JS)."""
        out = []
        if 'wa.me' in html:
            out.append('%s: literal wa.me URL in HTML (must be built on '
                       'click only)' % rel)
        if 'alt=""' in html:
            out.append('%s: empty img alt="" in HTML' % rel)
        for attrs, inner in re.findall(r'<a\b([^>]*)>(.*?)</a>', html,
                                       re.S | re.I):
            text = htmlmod.unescape(re.sub(r'<[^>]+>', '', inner)).strip()
            if text:
                continue
            if any(a.strip() for a in re.findall(r'alt="([^"]*)"', inner)):
                continue
            lab = re.search(r'aria-label="([^"]*)"', attrs)
            if lab and lab.group(1).strip():
                continue
            out.append('%s: <a %s> with no anchor text, img alt or '
                       'aria-label' % (rel, attrs.strip()[:80]))
        return out

    en_recipe_descs = {}
    for rel, html in sorted(pages.items()):
        lang = 'en'
        if '/recipe/' in rel and not rel.startswith('recipe/'):
            lang = rel.split('/')[0]
            # map the URL prefix back to the internal language code
            lang = next((c for c, p in LANG_PREFIX.items() if p == lang),
                        'en')
        if "['" in html:
            problems.append('%s: raw Python list in HTML' % rel)
        t = re.search(r'<title>(.*?)</title>', html)
        title = htmlmod.unescape(t.group(1)) if t else ''
        if not title:
            problems.append('%s: no <title>' % rel)
        elif len(title) > 60:
            problems.append('%s: title %d chars: %r'
                            % (rel, len(title), title))
        d = re.search(r'<meta name="description" content="([^"]*)"', html)
        desc = htmlmod.unescape(d.group(1)) if d else ''
        if not desc:
            problems.append('%s: no meta description' % rel)
        elif len(desc) > 155:
            problems.append('%s: description %d chars' % (rel, len(desc)))
        if '<link rel="canonical"' not in html:
            problems.append('%s: no canonical' % rel)
        if 'og:image' not in html or 'og:image" content=""' in html:
            problems.append('%s: no og:image' % rel)
        if '/recipe/' in rel and 'og:type" content="article"' not in html:
            problems.append('%s: og:type is not article' % rel)
        if html.count('<h1') != 1:
            problems.append('%s: %d <h1, expected 1'
                            % (rel, html.count('<h1')))
        levels = [int(m.group(1)) for m in
                  re.finditer(r'<h([1-6])\b', html)]
        for a, b in zip(levels, levels[1:]):
            if b > a + 1:
                problems.append('%s: heading order skips h%d -> h%d '
                                '(PageSpeed accessibility)' % (rel, a, b))
                break
        problems.extend(_anchor_problems(rel, html))
        quals = ING_QUALIFIERS.get(lang, set())
        _rv = None
        _vo = None
        for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                            html, re.S):
            try:
                obj = json.loads(b)
            except Exception as e:
                problems.append('%s: JSON-LD does not parse: %s' % (rel, e))
                continue
            if obj.get('@type') == 'BreadcrumbList':
                for el in obj.get('itemListElement') or []:
                    if not el.get('item'):
                        problems.append('%s: BreadcrumbList itemListElement '
                                        'position %s missing item'
                                        % (rel, el.get('position')))
            if obj.get('@type') == 'Recipe':
                _rv = (obj.get('video') or {}).get('@id')
                if not (obj.get('author') or {}).get('url'):
                    problems.append('%s: Recipe author missing url' % rel)
                for f in ('name', 'image', 'description',
                          'recipeIngredient', 'recipeInstructions',
                          'totalTime', 'recipeYield', 'datePublished',
                          'recipeCategory', 'recipeCuisine', 'keywords'):
                    if not obj.get(f):
                        problems.append('%s: Recipe JSON-LD missing %s'
                                        % (rel, f))
                for i, st in enumerate(obj.get('recipeInstructions') or []):
                    if not st.get('name') or not st.get('url'):
                        problems.append('%s: HowToStep %d missing name/url'
                                        % (rel, i + 1))
                    elif ('id="step-%d"' % (i + 1)) not in html:
                        problems.append('%s: HowToStep url anchor step-%d '
                                        'has no matching <li id> on the page'
                                        % (rel, i + 1))
                    if not st.get('image') and not st.get('video'):
                        problems.append('%s: HowToStep %d has neither image '
                                        'nor video' % (rel, i + 1))
                for ing in obj.get('recipeIngredient') or []:
                    if ing.strip().lower() in quals:
                        problems.append('%s: qualifier orphan in '
                                        'ingredients: %r' % (rel, ing))
                # Nutrition (GSC 'Missing field "nutrition"', 2026-10-31):
                # the Recipe block must carry the computed per-serving
                # values, matching nutrition.json field for field, and
                # the visible line must be on the page. (English rels are
                # 'recipe/<id>/index.html' — no leading slash — so split
                # on 'recipe/', not '/recipe/'.)
                _rid = rel.split('recipe/')[1].split('/')[0]
                _exp = (data.get('nutrition') or {}).get(_rid)
                if not _exp:
                    problems.append('%s: recipe %s has no nutrition data'
                                    % (rel, _rid))
                else:
                    _nld = obj.get('nutrition') or {}
                    if _nld.get('@type') != 'NutritionInformation':
                        problems.append('%s: Recipe nutrition missing '
                                        '@type NutritionInformation' % rel)
                    _units = {k: u for k, _l, u in _NUT_FIELDS}
                    for _k, _v in _exp.items():
                        _want = "%s %s" % (_fmt_num(_v), _units[_k])
                        if _nld.get(_k) != _want:
                            problems.append('%s: Recipe nutrition %s is %r, '
                                            'expected %r'
                                            % (rel, _k, _nld.get(_k), _want))
                    for _k in _nld:
                        if _k != '@type' and _k not in _exp:
                            problems.append('%s: Recipe nutrition has '
                                            'uncomputed field %s' % (rel, _k))
                if 'Nutrition (approx. per serving)' not in html:
                    problems.append('%s: visible nutrition line missing'
                                    % rel)
                # Ratings (GSC 'Missing field "aggregateRating"',
                # 2026-11-02): an emitted aggregateRating must match
                # ratings.json exactly (value, count, best/worst), and
                # the visible rating line must show the same numbers.
                # No ratings -> no aggregateRating at all.
                _rat = (data.get('ratings') or {}).get(_rid)
                _ar = obj.get('aggregateRating')
                if _rat and _rat.get('count', 0) > 0:
                    _avg = round(_rat['sum'] / _rat['count'], 1)
                    if not _ar:
                        problems.append('%s: recipe %s has %d ratings but '
                                        'no aggregateRating'
                                        % (rel, _rid, _rat['count']))
                    else:
                        if _ar.get('@type') != 'AggregateRating':
                            problems.append('%s: aggregateRating @type is %r'
                                            % (rel, _ar.get('@type')))
                        if _ar.get('ratingValue') != _avg:
                            problems.append('%s: aggregateRating ratingValue '
                                            '%r, expected %r'
                                            % (rel, _ar.get('ratingValue'),
                                               _avg))
                        if _ar.get('ratingCount') != _rat['count']:
                            problems.append('%s: aggregateRating ratingCount '
                                            '%r, expected %r'
                                            % (rel, _ar.get('ratingCount'),
                                               _rat['count']))
                        if (_ar.get('bestRating') != 5
                                or _ar.get('worstRating') != 1):
                            problems.append('%s: aggregateRating best/worst '
                                            'is %r/%r, expected 5/1'
                                            % (rel, _ar.get('bestRating'),
                                               _ar.get('worstRating')))
                    _m = re.search(r'<p class="rating-line">(.*?)</p>',
                                   html, re.S)
                    if not _m:
                        problems.append('%s: visible rating line missing'
                                        % rel)
                    else:
                        _line = htmlmod.unescape(
                            re.sub(r'<[^>]+>', '', _m.group(1)))
                        if ('%.1f' % _avg) not in _line:
                            problems.append('%s: visible rating line %r '
                                            'does not show average %.1f'
                                            % (rel, _line, _avg))
                        if str(_rat['count']) not in _line:
                            problems.append('%s: visible rating line %r '
                                            'does not show count %d'
                                            % (rel, _line, _rat['count']))
                else:
                    if _ar:
                        problems.append('%s: aggregateRating present but '
                                        'recipe %s has no ratings in '
                                        'ratings.json' % (rel, _rid))
                    if '<p class="rating-line">' not in html:
                        problems.append('%s: visible rating line missing'
                                        % rel)
            if obj.get('@type') == 'VideoObject':
                _vo = obj.get('@id')
                if not (obj.get('author') or {}).get('name'):
                    problems.append('%s: VideoObject missing author' % rel)
                if not (obj.get('author') or {}).get('url'):
                    problems.append('%s: VideoObject author missing url'
                                    % rel)
                _ud = obj.get('uploadDate')
                if _ud and not re.match(
                        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$',
                        _ud):
                    problems.append('%s: VideoObject uploadDate %r is not '
                                    'a full datetime with timezone' % (rel, _ud))
                if not obj.get('url'):
                    problems.append('%s: VideoObject missing url' % rel)
        if _vo and _rv != _vo:
            problems.append('%s: Recipe video @id %r does not match '
                            'VideoObject @id %r' % (rel, _rv, _vo))
        if _rv and not _vo:
            problems.append('%s: Recipe video @id %r has no VideoObject '
                            'on the page' % (rel, _rv))
        if '/recipe/' in rel:
            _rid = rel.split('/recipe/')[1].split('/')[0]
            _pub = ((dates.get('article') or {}).get(_rid, {})
                    .get('published'))
            if _pub:
                _want_pub = ('<p class="pubdate">%s %s</p>'
                             % (esc(ui_str(data, lang, 'publishedOn',
                                          'Published on')),
                                esc(fmt_date(_pub))))
                if _want_pub not in html:
                    problems.append('%s: missing visible publish date %r'
                                    % (rel, _want_pub))
        if rel.startswith('recipe/'):
            if not (140 <= len(desc) <= 155):
                problems.append('%s: English recipe description %d chars '
                                '(want 140-155)' % (rel, len(desc)))
            en_recipe_descs.setdefault(desc, []).append(rel)
    for desc, rels in en_recipe_descs.items():
        if len(rels) > 1:
            problems.append('duplicate English recipe description %r: %s'
                            % (desc[:50], rels))
    # TREND_IDS must still be the UI trendCards.
    ui_trend = []
    m = re.search(r'trendCards:\[\[', data['ui_raw']['en'])
    if m:
        try:
            val, _ = parse_js_literal(data['ui_raw']['en'],
                                      data['ui_raw']['en'].find('[', m.start()))
            ui_trend = [pair[0] for pair in val]
        except Exception:
            pass
    by_id = {r['id']: r for r in data['recipes']}
    if ui_trend and [by_id[i]['name'] for i in TREND_IDS] != ui_trend:
        problems.append('TREND_IDS %r do not match UI trendCards %r'
                        % (TREND_IDS, ui_trend))
    # Sitemap must list exactly the pages built (+ the homepage).
    def norm(u):
        return u.rstrip('/') or '/'
    want = {norm('https://www.zaikaworlds.com/')}
    for rel in pages:
        d = rel[:-len('/index.html')] if rel.endswith('/index.html') else rel
        want.add(norm('https://www.zaikaworlds.com/' + d))
    got = {norm(u) for u in generate_sitemap_urls(data)}
    if got != want:
        problems.append('sitemap mismatch: %d extra, %d missing'
                        % (len(got - want), len(want - got)))
    # Edge-cache rule must be present in vercel.json (Screaming Frog
    # "Slow page", 2026-10-31): without it HTML serves max-age=0 and
    # every fetch revalidates with origin, so cold fetches spike over 1s.
    try:
        with open(os.path.join(ROOT, 'vercel.json'), encoding='utf-8') as f:
            vcfg = json.load(f)
    except Exception as e:
        problems.append('vercel.json unreadable: %s' % e)
        vcfg = {}
    hdrs = vcfg.get('headers') or []

    def _has_cc(rule, needle):
        return any(h.get('key') == 'Cache-Control'
                   and needle in (h.get('value') or '')
                   for h in rule.get('headers') or [])
    if not any(r.get('source') == '/(.*)' and _has_cc(r, 's-maxage')
               for r in hdrs):
        problems.append('vercel.json: no HTML edge-cache Cache-Control '
                        '(s-maxage) on the /(.*) rule')
    if not any(r.get('source') == '/assets/(.*)' and _has_cc(r, 'immutable')
               for r in hdrs):
        problems.append('vercel.json: /assets/ immutable Cache-Control missing')
    # Hreflang reciprocity + orphan check (Screaming Frog "Missing
    # reciprocal link" + "Orphan page", 2026-10-31). The slim homepage
    # is part of the graph: it is the only page the static set does
    # not otherwise build. Every hreflang alternate must be a built
    # page and must link back to the source URL; every built page
    # except the homepage seed must have an incoming internal link.
    n_pages = len(pages)
    slim_html = build_slim(open(os.path.join(ROOT, 'index.html'),
                                encoding='utf-8').read(), data)
    pages['index.html'] = slim_html
    problems.extend(_anchor_problems('index.html', slim_html))
    # PageSpeed (2026-10-31) slim-homepage guards.
    # (a) Card images must be 600px thumbs; the only full-size recipe
    # photos allowed in <img> tags are the LCP hero (1200w variant) and
    # the recipeImg/videoThumbImg placeholders (swapped by JS at runtime).
    for m in re.finditer(r'<img([^>]*)>', slim_html):
        _tag = m.group(1)
        _sm = re.search(r'src="([^"]+)"', _tag)
        if not _sm:
            continue
        s = _sm.group(1)
        if (s.startswith('/assets/') and s.endswith('.webp')
                and '/thumbs/' not in s
                and 'hero-49347f9b-1200.webp' not in s
                and 'id="recipeImg"' not in _tag
                and 'id="videoThumbImg"' not in _tag):
            problems.append('index.html: full-size photo in <img>: %s '
                            '(cards must use the 600px thumb)' % s)
    # (b) Init must load only recipes.js + ui-en.js; extra-en.js and
    # lang-new.js are lazy (on recipe open / language switch).
    if ('Promise.all([_loadScript("data/recipes.js"),'
            '_loadScript("data/ui-en.js")])') not in slim_html:
        problems.append('index.html: slim init must load only recipes.js '
                        '+ ui-en.js (extra-en.js / lang-new.js are lazy)')
    # (c) extra-en.js must be the mergeable ZAIKA_EXTRA_EN format, or
    # _ensureExtra would wipe other languages when it loads.
    try:
        with open(os.path.join(ROOT, 'data', 'extra-en.js'),
                  encoding='utf-8') as f:
            _ee = f.read(40)
        if not _ee.startswith('var ZAIKA_EXTRA_EN='):
            problems.append('data/extra-en.js: must start with '
                            'var ZAIKA_EXTRA_EN= (mergeable format)')
    except Exception as e:
        problems.append('data/extra-en.js unreadable: %s' % e)
    # (d) Contrast: the fixed pairs in the light theme must pass WCAG
    # AA (4.5 normal text, 3.0 large text). The footer links must not
    # be red-on-dark (the old .site-footer p a rule).
    _css = re.search(r'<style[^>]*>(.*?)</style>', slim_html, re.S)
    if _css:
        _root = re.search(r':root\{([^}]*?)\}', _css.group(1), re.S)
        _vars = dict(re.findall(r'--([a-z0-9-]+):(#[0-9a-fA-F]{6})',
                                _root.group(1))) if _root else {}
        _pairs = [('muted', 'surface2', 4.5, 'fact label'),
                  ('muted', 'surface', 4.5, 'muted on surface'),
                  ('muted', 'bg', 4.5, 'muted on bg'),
                  ('red', 'surface', 4.5, 'red links on surface'),
                  ('red', 'bg', 4.5, 'red links on bg'),
                  ('header-ink', 'header-bg', 4.5, 'footer links'),
                  ('accent', 'header-bg', 3.0, 'wordmark (large text)')]
        for fg, bg, need, why in _pairs:
            if fg in _vars and bg in _vars:
                _r = _contrast(_vars[fg], _vars[bg])
                if _r < need:
                    problems.append('contrast: %s on %s is %.2f, need %.1f '
                                    '(%s)' % (fg, bg, _r, need, why))
        # white text on the deep backgrounds used for skip-link and the
        # pressed Save button (light theme uses --red-dark / --red).
        for bg, why in (('red-dark', 'skip-link'),
                         ('red', 'pressed Save button')):
            if bg in _vars and _contrast('#ffffff', _vars[bg]) < 4.5:
                problems.append('contrast: white on --%s is %.2f, need 4.5 '
                                '(%s)' % (bg, _contrast('#ffffff',
                                                        _vars[bg]), why))
        if '.site-footer p a' in _css.group(1):
            problems.append('contrast: .site-footer p a must not be styled '
                            'red (red on the dark footer fails WCAG)')
    # SPA recipe view must carry the visible publish date (issue #15).
    if 'recipePubDate' not in slim_html or 'publishedOn' not in slim_html:
        problems.append('index.html: recipe view has no publish-date '
                        'element (recipePubDate / publishedOn)')
    # og:image uniqueness for hub pages (audit issue #6): no two
    # distinct non-recipe pages may share an og:image; language
    # variants of one page share it by design, so canonicalise by
    # stripping a leading language prefix. Recipe pages are keyed by
    # recipe and must use that recipe's own photo.
    def _canon(rel):
        # Inline canonical path (do NOT use _path_of/_norm: they are
        # defined below this block in validate_build).
        if rel == 'index.html':
            p = '/'
        elif rel.endswith('/index.html'):
            p = '/' + rel[:-len('/index.html')]
        else:
            p = '/' + rel
        p = p.rstrip('/') or '/'
        for _pfx in LANG_PREFIX.values():
            if p.startswith('/' + _pfx + '/'):
                return (p[len(_pfx) + 1:]).rstrip('/') or '/'
            if p == '/' + _pfx:
                return '/'
        return p
    _og_by_path = {}
    for rel, html in sorted(pages.items()):
        _m = re.search(r'<meta[^>]*property="og:image" content="([^"]*)"',
                       html)
        if not _m:
            continue
        _cp = _canon(rel)
        if _cp.startswith('/recipe/'):
            continue
        if _cp in _og_by_path and _og_by_path[_cp] != _m.group(1):
            problems.append('%s: language variant og:image %s != %s'
                            % (rel, _m.group(1), _og_by_path[_cp]))
        _og_by_path.setdefault(_cp, _m.group(1))
    _seen_og = {}
    for _cp, _img in sorted(_og_by_path.items()):
        if _img in _seen_og:
            problems.append('og:image %s shared by %s and %s (hub pages '
                            'must each have a distinct photo)'
                            % (_img, _seen_og[_img], _cp))
        else:
            _seen_og[_img] = _cp
    for _cp, _img in sorted(_og_by_path.items()):
        if _cp in HUB_OG:
            _want = hub_og(data, _cp)[0]
            if _img != _want:
                problems.append('%s: og:image %s != assigned %s'
                                % (_cp, _img, _want))
    for rel, html in sorted(pages.items()):
        _cp = _canon(rel)
        if _cp.startswith('/recipe/'):
            _rid = _cp[len('/recipe/'):]
            _r = next((x for x in data['recipes'] if x['id'] == _rid),
                      None)
            if _r:
                _m = re.search(
                    r'<meta[^>]*property="og:image" content="([^"]*)"', html)
                if _m and _m.group(1) != SITE + '/' + _r['img']:
                    problems.append('%s: og:image %s != recipe photo %s'
                                    % (rel, _m.group(1), _r['img']))
    _slim_og = re.search(
        r'<meta[^>]*property="og:image" content="([^"]*)"', slim_html)
    if not _slim_og:
        problems.append('index.html: no og:image (the slim homepage must '
                        'carry the homepage assignment statically)')
    elif _slim_og.group(1) != hub_og(data, '/')[0]:
        problems.append('index.html: og:image %s != homepage assignment %s'
                        % (_slim_og.group(1), hub_og(data, '/')[0]))

    def _path_of(rel):
        if rel == 'index.html':
            return '/'
        return '/' + (rel[:-len('/index.html')]
                      if rel.endswith('/index.html') else rel)

    def _norm(u):
        return u.rstrip('/') or '/'

    path_to_rel = {_norm(_path_of(rel)): rel for rel in pages}
    hl_re = re.compile(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">')
    link_re = re.compile(r'<a [^>]*href="([^"]*)"')
    incoming = {rel: 0 for rel in pages}
    for rel, html in sorted(pages.items()):
        src_path = _norm(_path_of(rel))
        for code, href in hl_re.findall(html):
            if code == 'x-default':
                continue
            if not href.startswith(SITE):
                problems.append('%s: hreflang %s points outside the site: %s'
                                % (rel, code, href))
                continue
            tgt = _norm(href[len(SITE):])
            if tgt not in path_to_rel:
                problems.append('%s: hreflang %s points at %s, not a built page'
                                % (rel, code, href))
                continue
            back = hl_re.findall(pages[path_to_rel[tgt]])
            if src_path not in [_norm(h[len(SITE):]) for _, h in back
                                if h.startswith(SITE)]:
                problems.append('%s: hreflang %s -> %s has no return link'
                                % (rel, code, href))
        for href in link_re.findall(html):
            href = href.split('#')[0].split('?')[0]
            if href.startswith(SITE):
                href = href[len(SITE):]
            if not href.startswith('/'):
                continue
            tgt = _norm(href)
            if tgt in path_to_rel and path_to_rel[tgt] != rel:
                incoming[path_to_rel[tgt]] += 1
    for rel, n in sorted(incoming.items()):
        if rel != 'index.html' and n == 0:
            problems.append('%s: orphan page, no incoming internal link' % rel)
    # Thin-link guard (Ahrefs audit 2026-10-31, "5 pages have only one
    # incoming internal link"): the hub pages must be linked from many
    # pages, not just the homepage. SITE_FOOTER links all five from
    # every static page, so each should have ~460 incoming links.
    for rel in ('about/index.html', 'contact/index.html', 'faqs/index.html',
                'privacy/index.html', 'trending/index.html'):
        if incoming.get(rel, 0) < 10:
            problems.append('%s: only %d incoming internal links '
                            '(want >= 10)' % (rel, incoming.get(rel, 0)))
    # Video-gap guard (GSC 'Missing field "video"', 2026-11-02): a recipe
    # with no videos map (or missing languages) has no "video" in its
    # Recipe JSON-LD, so GSC flags every crawled page of that recipe.
    # This is a WARNING, not a failure: a new recipe goes live before
    # its videos are uploaded, so a hard fail would block the daily
    # new-recipe pipeline. The daily run must finish the previous
    # recipe's videos + embed first; this warning lists what is still
    # open so it can never slip through unnoticed again.
    _gaps = []
    for r in data['recipes']:
        _vids = r.get('videos') or {}
        _missing = [lang for lang in LANGS if not _vids.get(lang)]
        if _missing:
            _gaps.append('%s: no video in %d/13 languages (%s)'
                         % (r['id'], len(_missing), ','.join(_missing)))
    if _gaps:
        print('VIDEO GAP WARNING: %d recipe(s) have no video in some '
              'languages — GSC "Missing field \'video\'" will persist '
              'for these pages:' % len(_gaps), file=sys.stderr)
        for _g in _gaps:
            print('  - %s' % _g, file=sys.stderr)
    # Feed-sync guard (Pinterest RSS, 2026-11-08): feed.xml was stale
    # since 1 Nov (46 items) because no build step generated it, so the
    # 13 recipes added 7 Nov never reached Pinterest. build_feed() now
    # regenerates it on every full build; this is a WARNING, not a
    # failure, so a stale feed never blocks a deploy, but it can never
    # slip through unnoticed again.
    _feed_path = os.path.join(ROOT, 'feed.xml')
    _feed_warn = None
    if not os.path.exists(_feed_path):
        _feed_warn = ('feed.xml missing (build_feed() regenerates it on '
                      'the next full build)')
    else:
        _feed_src = open(_feed_path, encoding='utf-8').read()
        _feed_n = _feed_src.count('<item>')
        _feed_missing = [r['id'] for r in data['recipes']
                         if ('/recipe/%s</link>' % r['id']) not in _feed_src]
        if _feed_n != len(data['recipes']) or _feed_missing:
            _feed_warn = ('feed.xml has %d <item> for %d recipes%s'
                          % (_feed_n, len(data['recipes']),
                             (', missing: ' + ','.join(_feed_missing))
                             if _feed_missing else ''))
    if _feed_warn:
        print('FEED SYNC WARNING: %s' % _feed_warn, file=sys.stderr)
    return problems, n_pages



def generate_sitemap_urls(data):
    """The sitemap URLs (shared by generate_sitemap and validate_build)."""
    urls = ['/']
    for r in data['recipes']:
        urls.append('/recipe/' + r['id'])
    for lang in LANGS[1:]:
        urls.append('/' + LANG_PREFIX[lang] + '/')
        for r in data['recipes']:
            urls.append('/%s/recipe/%s' % (LANG_PREFIX[lang], r['id']))
    for slug in sorted(data['cat_by_slug']):
        urls.append('/category/' + slug)
    for slug in sorted(data['country_by_slug']):
        urls.append('/country/' + slug)
    for name in ('about', 'privacy', 'contact', 'recipes', 'trending',
                 'faqs', 'eid-recipes', 'ramadan-recipes'):
        urls.append('/' + name)
    urls.append('/guides/dum-cooking')
    return [SITE + u for u in urls]


def main(argv):
    mode = argv[1] if len(argv) > 1 else 'build'
    src, index_path = _read_index()

    if mode == '--source-fix':
        # Apply only the H1/CSS/promotion fix to the fat source, in place.
        out = apply_h1_fix(src)
        out = apply_promotion(out)
        if out == src:
            print('H1 fix already applied; no change.')
        else:
            write(index_path, out)
            print('Applied H1 fix + heading promotion to index.html '
                  '(%d -> %d bytes).'
                  % (len(src.encode('utf-8')), len(out.encode('utf-8'))))
        print('H1 count in index.html: %d' % out.count('<h1'))
        return 0

    data = extract_all(src)
    fat_bytes = len(src.encode('utf-8'))
    print('Parsed: %d recipes, %d categories, %d countries; '
          'UI langs %d, INFO langs %d'
          % (len(data['recipes']), len(data['cat_by_slug']),
             len(data['country_by_slug']), len(data['ui_raw']),
             len(data['info'])))

    if mode == '--check':
        problems, n_pages = validate_build(data)
        if problems:
            print('check FAILED: %d problem(s):' % len(problems),
                  file=sys.stderr)
            for p in problems[:30]:
                print('  - %s' % p, file=sys.stderr)
            return 1
        print('check OK: all data blocks parse and validate; '
              'index.html %d bytes; %d static pages validated.'
              % (fat_bytes, n_pages))
        return 0

    if mode != 'build':
        print('usage: build_site.py [--check | --source-fix]', file=sys.stderr)
        return 2

    data_files = write_data_files(data)
    static_pages = write_static_pages(data)
    sitemap_count = generate_sitemap(data)
    try:
        feed_count = build_feed(data['recipes'])
    except Exception as e:
        # The feed is secondary: a feed failure must never fail the
        # whole build (the site is more important than the feed).
        print('WARNING: feed.xml not regenerated: %s' % e, file=sys.stderr)
        feed_count = 0
    slim = build_slim(src, data)
    slim_bytes = len(slim.encode('utf-8'))
    if slim_bytes >= 500 * 1024:
        raise JSError('slim index.html is %d bytes, over the 500KB target'
                      % slim_bytes)
    if slim.count('<h1') != 1:
        raise JSError('slim index.html has %d <h1, expected 1'
                      % slim.count('<h1'))
    write(index_path, slim)
    vercel_changes = update_vercel()
    _print_summary(fat_bytes, slim_bytes, data_files, static_pages)
    print('vercel.json: %s'
          % ('; '.join(vercel_changes) if vercel_changes else 'no change'))
    print('static pages: %d recipes, %d categories, %d countries, '
          '3 info pages, %d sitemap URLs, %d feed items'
          % (len(data['recipes']), len(data['cat_by_slug']),
             len(data['country_by_slug']), sitemap_count, feed_count))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv))
    except JSError as e:
        print('build_site.py: ERROR: %s' % e, file=sys.stderr)
        sys.exit(1)
