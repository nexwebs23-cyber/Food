#!/usr/bin/env python3
"""build_site.py — Build the Zaika Worlds site from index.html (source of truth).

What it does
------------
1. Parses the big data blocks out of index.html (RECIPES, EXTRA, LANG_DATA, UI,
   INFO, EXTRA_NEW) and writes them as lazily-loaded files under data/:
     data/recipes.js        RECIPES (all 32, English base + video ids)
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
     recipe/<slug>/index.html   x32
     category/<slug>/index.html x7
     country/<slug>/index.html  x16
     about/index.html, privacy/index.html, contact/index.html
   Filesystem beats Vercel rewrites, so a direct visit to /recipe/<slug>
   serves the static page; SPA navigation (pushState) still works.
3. Rewrites index.html in place into a slim SPA shell (~160KB instead of
   ~3.1MB): the data blocks become empty declarations, an async loader pulls
   data/*.js (English first, other languages on demand), the six raw <h1>
   elements become one <h1> plus runtime heading promotion, and the tail
   merge loop is replaced by the loader init.

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

import json
import os
import re
import sys

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
CONTACT_EMAIL = "info.allcalctool@gmail.com"


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

    # EXTRA_NEW: per-language arrays -> normalized 10-key objects.
    # Initial literal holds es/fr (4 recipes each); es/fr/ar/pt add 28-32
    # per-recipe assignments; bn/de/ja/rus/tr/zh are whole-language literals.
    en_raw = {}
    init_raw, _, _ = find_literal(src, 'var EXTRA_NEW={')
    for lang in ('es', 'fr'):
        i = init_raw.find(lang + ':{')
        if i < 0:
            raise JSError("EXTRA_NEW.%s not found in initial literal" % lang)
        raw, _ = raw_braced(init_raw, init_raw.find('{', i))
        sub, _ = parse_js_literal(raw)
        en_raw[lang] = sub
    for m in re.finditer(r'EXTRA_NEW\.([a-z]+)\.([a-z0-9_-]+)\s*=\s*\[', src):
        lang, rid = m.group(1), m.group(2)
        raw, _ = raw_braced(src, src.find('[', m.start()))
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
        'ui_patches': ui_patches,
        'extra_new': extra_new,
        'lang_new_raw': lang_new_raw, 'lang_new_raw2': lang_new_raw2,
        'lang_new_raw3': lang_new_raw3,
        'cat_by_slug': cat_by_slug, 'cat_title': cat_title,
        'list_lead': list_lead, 'country_by_slug': country_by_slug,
        'country_adj': country_adj, 'cat_slug': cat_slug,
        'country_slug': country_slug,
    }
    validate(data)
    return data


def validate(data):
    """Sanity checks: counts, coverage, required fields. Fail loudly."""
    recipes = data['recipes']
    if len(recipes) != 32:
        raise JSError("expected 32 recipes, got %d" % len(recipes))
    ids = [r['id'] for r in recipes]
    if len(set(ids)) != 32:
        raise JSError("duplicate recipe ids")
    for r in recipes:
        for k in ('id', 'name', 'country', 'cat', 'catLabel', 'time',
                  'servings', 'img', 'desc', 'intro', 'ing', 'steps', 'tip'):
            if k not in r:
                raise JSError("recipe %s missing %r" % (r.get('id'), k))
        if not r['ing'] or not r['steps']:
            raise JSError("recipe %s has empty ing/steps" % r['id'])
    for lang in EXTRA_OBJ_LANGS:
        have = {rid for rid, d in data['extra'].items() if lang in d}
        if have != set(ids):
            raise JSError("EXTRA.%s covers %d/32 recipes" % (lang, len(have)))
    for lang in EXTRA_NEW_LANGS:
        have = set(data['extra_new'].get(lang, {}))
        if have != set(ids):
            raise JSError("EXTRA_NEW.%s covers %d/32 recipes"
                          % (lang, len(have)))
    for lang in LANGS:
        if lang not in data['ui_raw']:
            raise JSError("UI.%s missing" % lang)
        if lang not in data['info']:
            raise JSError("INFO.%s missing" % lang)
    # UI patches: en/ru/hi each gain the same 26 keys after the literal.
    for lang in ('en', 'ru', 'hi'):
        keys = set(data['ui_patches'].get(lang, {}))
        if len(keys) != 26:
            raise JSError("UI.%s patches: %d keys, expected 26"
                          % (lang, len(keys)))
    if set(data['ui_patches']) != {'en', 'ru', 'hi'}:
        raise JSError("UI patches cover %s, expected en/ru/hi"
                      % sorted(data['ui_patches']))
    for lang in LANG_DATA_LANGS:
        have = {rid for rid, d in data['lang_data'].items() if lang in d}
        if have != set(ids):
            raise JSError("LANG_DATA.%s covers %d/32 recipes"
                          % (lang, len(have)))
    # LANG_NEW_RAW* cover the other 10 languages (short-form name/desc/alt).
    expect = {'LANG_NEW_RAW': {'es', 'fr', 'ar'},
              'LANG_NEW_RAW2': {'pt', 'rus', 'zh'},
              'LANG_NEW_RAW3': {'bn', 'de', 'ja', 'tr'}}
    for key, langs in expect.items():
        raw = data[key.lower()]
        if set(raw) != set(ids):
            raise JSError("%s covers %d/32 recipes" % (key, len(raw)))
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
    if len(data['cat_by_slug']) != 7 or len(data['country_by_slug']) != 16:
        raise JSError("expected 7 categories / 16 countries, got %d / %d"
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


def list_info(data, kind, slug):
    """Mirror listInfo() for English: label/title/desc/intro/recipes/img."""
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
    desc = ('%d %s with full ingredients and step by step methods'
            % (n, t))
    if n <= 7:
        desc += ': ' + names
    elif kind == 'category':
        desc += ' from 14 countries'
    desc += '.'
    parts = [lead]
    if n == 1:
        parts.append('The recipe on this page is ' + names + '.')
    elif n <= 7:
        parts.append('Recipes on this page: ' + names + '.')
    parts.append('Each recipe lists full ingredients, a step by step method, '
                 'cooking time and servings.')
    first = rs[0]
    ftx = r_text_en(first, data['extra'])
    return {'kind': kind, 'slug': slug, 'label': label, 'title': title,
            'desc': desc, 'intro': ' '.join(parts), 'recipes': rs,
            'img': SITE + '/' + first['img'],
            'imgAlt': ftx.get('alt') or first['name'],
            'url': SITE + '/' + kind + '/' + slug}


# ---------------------------------------------------------------------------
# Data files (data/*.js)
# ---------------------------------------------------------------------------

def write_data_files(data):
    """Write the lazily-loaded data files. Returns {path: bytes}."""
    out = {}

    def w(rel, text):
        path = os.path.join(ROOT, 'data', rel)
        write(path, text)
        out[rel] = len(text.encode('utf-8'))

    # Core (English) — loaded by the SPA on every visit.
    w('recipes.js', 'var RECIPES=' + js_json(data['recipes']) + ';\n')
    extra_en = {rid: {'en': d['en']} for rid, d in data['extra'].items()
                if 'en' in d}
    w('extra-en.js', 'var EXTRA=' + js_json(extra_en) + ';\n')
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
        w('extra-%s.js' % lang,
          'var ZAIKA_EXTRA_' + lang.upper() + '=' + js_json(obj) + ';\n')

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
        w('lang-data-%s.js' % lang,
          'var ZAIKA_LANGDATA_' + lang.upper() + '=' + js_json(obj) + ';\n')

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

STATIC_CSS = """
body{font-family:Georgia,'Times New Roman',serif;color:#241f1a;background:#fdf8ef;margin:0;line-height:1.6}
.wrap{max-width:760px;margin:0 auto;padding:0 18px 48px}
header.site{border-bottom:3px solid #b3402a;padding:18px 0 12px}
header.site a.brand{font-size:28px;font-weight:700;color:#1f1b16;text-decoration:none}
header.site a.brand span{color:#b3402a}
nav.crumb{font-size:14px;color:#6b5f52;margin:16px 0 6px}
nav.crumb a{color:#b3402a}
h1{font-size:34px;line-height:1.15;margin:8px 0 12px}
h2{font-size:24px;margin:28px 0 8px}
h3{font-size:19px;margin:20px 0 6px}
p{margin:0 0 12px}
ul,ol{margin:0 0 16px;padding-left:24px}
li{margin:0 0 6px}
img.hero{width:100%;height:auto;border-radius:10px;display:block;margin:12px 0}
.facts{color:#6b5f52;font-size:15px;margin:0 0 12px}
.cta{display:block;background:#b3402a;color:#fff;text-align:center;padding:12px 16px;border-radius:8px;text-decoration:none;font-weight:700;margin:20px 0}
.cta:hover{background:#93331f}
.card{display:flex;gap:14px;align-items:flex-start;border:1px solid #e5d9c5;border-radius:10px;padding:12px;margin:0 0 14px;background:#fff}
.card img{width:120px;height:auto;border-radius:8px;flex:none}
.card a{color:#1f1b16;text-decoration:none;font-weight:700;font-size:18px}
.card p{color:#6b5f52;font-size:14px;margin:4px 0 0}
footer.site{border-top:1px solid #e5d9c5;margin-top:36px;padding-top:14px;font-size:14px;color:#6b5f52}
footer.site a{color:#b3402a}
.muted{color:#6b5f52;font-size:14px}
""".strip()

SITE_HEADER = ('<header class="site"><a class="brand" href="/">Zaika '
               '<span>Worlds</span></a></header>')
SITE_FOOTER = ('<footer class="site">Zaika Worlds — home food recipes and '
               'world food recipes, in 13 languages. '
               '<a href="https://www.youtube.com/@ZaikaWorlds">YouTube</a> · '
               '<a href="https://www.facebook.com/profile.php?id='
               '1445260131997347">Facebook</a> · '
               '<a href="https://www.pinterest.com/zaikaworlds26/">'
               'Pinterest</a></footer>')


def page_shell(title, desc, url, og_img, og_alt, json_ld_blocks, body):
    """Full static HTML page. title must already be capped at 60 chars."""
    assert len(title) <= 60, "title too long (%d): %r" % (len(title), title)
    ld = ''.join(
        '<script type="application/ld+json">%s</script>\n' % js_json(b)
        for b in json_ld_blocks)
    return ('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,'
            ' initial-scale=1">\n'
            '<title>' + esc(title) + '</title>\n'
            '<meta name="description" content="' + esc(desc) + '">\n'
            '<meta name="robots" content="index, follow">\n'
            '<link rel="canonical" href="' + esc(url) + '">\n'
            '<meta property="og:type" content="website">\n'
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
            '</head>\n<body>\n<div class="wrap">\n' + SITE_HEADER + '\n'
            + body + '\n' + SITE_FOOTER + '\n</div>\n</body>\n</html>\n')


def recipe_json_ld(recipe, tx, url):
    """Mirror setRouteMeta() kind='recipe' (English text)."""
    ld = {"@context": "https://schema.org", "@type": "Recipe",
          "name": recipe['name'],
          "image": [SITE + '/' + recipe['img']],
          "description": tx.get('desc') or DEF_DESC,
          "author": {"@type": "Organization", "name": "Zaika Worlds"},
          "recipeYield": recipe['servings'],
          "totalTime": "PT%dM" % (recipe['time'] or 60),
          "recipeIngredient": tx.get('ing') or [],
          "recipeInstructions": [{"@type": "HowToStep", "text": s}
                                 for s in (tx.get('steps') or [])]}
    bld = {"@context": "https://schema.org", "@type": "BreadcrumbList",
           "itemListElement": [
               {"@type": "ListItem", "position": 1, "name": "Home",
                "item": SITE + "/"},
               {"@type": "ListItem", "position": 2,
                "name": recipe['catLabel']},
               {"@type": "ListItem", "position": 3, "name": recipe['name'],
                "item": url}]}
    return [ld, bld]


def recipe_page(data, recipe):
    tx = r_text_en(recipe, data['extra'])
    url = SITE + '/recipe/' + recipe['id']
    title = cap_title(recipe['name'])
    desc = tx.get('desc') or DEF_DESC
    img_url = SITE + '/' + recipe['img']
    dims = data['img_dims'].get(recipe['img'], [])
    wh = (' width="%d" height="%d"' % (dims[0], dims[1])
          if len(dims) == 2 else '')
    cat_slug = data['cat_slug'].get(recipe['cat'], '')
    ctry_slug = data['country_slug'].get(recipe['country'], '')

    def section(heading, items, tag):
        if not items:
            return ''
        lis = ''.join('<li>%s</li>' % esc(x) for x in items)
        return '<h2>%s</h2>\n<%s>\n%s\n</%s>\n' % (esc(heading), tag, lis, tag)

    def para(heading, text):
        if not text:
            return ''
        return '<h2>%s</h2>\n<p>%s</p>\n' % (esc(heading), esc(text))

    def faq_block(faq):
        if not faq:
            return ''
        out = ['<h2>Frequently asked questions</h2>']
        for q, a in faq:
            out.append('<h3>%s</h3>\n<p>%s</p>' % (esc(q), esc(a)))
        return '\n'.join(out) + '\n'

    video = ''
    vid = (recipe.get('videos') or {}).get('en')
    if vid:
        video = ('<p><a href="https://youtu.be/%s">Watch the recipe video '
                 'on YouTube</a></p>\n' % esc(vid))
    else:
        video = ('<p class="muted">Video coming soon — this recipe is being '
                 'filmed, so check back soon to watch every step.</p>\n')

    body = (
        '<nav class="crumb"><a href="/">Home</a> &rsaquo; '
        '<a href="/category/%s">%s</a> &rsaquo; '
        '<span>%s</span></nav>\n'
        '<h1>%s</h1>\n'
        '<p class="facts">%s &middot; %s &middot; %s &middot; %s</p>\n'
        '<img class="hero" src="%s" alt="%s"%s loading="eager">\n'
        '<p>%s</p>\n'
        '<a class="cta" href="/#recipe/%s">Open the interactive recipe '
        '&mdash; switch language, watch the video, save it</a>\n'
        '%s%s%s%s%s%s%s%s%s%s'
        '<h2>More</h2>\n'
        '<p><a href="/category/%s">More %s recipes</a> &middot; '
        '<a href="/country/%s">More %s recipes</a> &middot; '
        '<a href="/">All recipes</a></p>\n'
        % (esc(cat_slug), esc(recipe['catLabel']), esc(recipe['name']),
           esc(recipe['name']), esc(recipe['time']) + ' min',
           esc(recipe['servings']), esc(recipe['catLabel']),
           esc(recipe['country']), esc(img_url), esc(tx.get('alt') or ''),
           wh, esc(tx.get('intro') or ''), esc(recipe['id']),
           video,
           section('Ingredients', tx.get('ing'), 'ul'),
           section('Method', tx.get('steps'), 'ol'),
           para('Tip', tx.get('tip')),
           para('Serving', tx.get('serving')),
           para('Storage', tx.get('storage')),
           para('Notes', tx.get('notes')),
           para('Variations', tx.get('variations')),
           para('Common mistakes', tx.get('mistakes')),
           faq_block(tx.get('faq')),
           esc(cat_slug), esc(recipe['catLabel']),
           esc(ctry_slug), esc(recipe['country'])))
    return page_shell(title, desc, url, img_url, tx.get('alt') or '',
                      recipe_json_ld(recipe, tx, url), body)


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
        dims = data['img_dims'].get(r['img'], [])
        wh = (' width="%d" height="%d"' % (dims[0], dims[1])
              if len(dims) == 2 else '')
        cards.append(
            '<div class="card"><a href="/recipe/%s">'
            '<img src="%s" alt="%s"%s loading="lazy"></a>'
            '<div><a href="/recipe/%s">%s</a>'
            '<p>%s &middot; %s &middot; %s</p></div></div>'
            % (esc(r['id']), esc(SITE + '/' + r['img']),
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


def info_page(data, name):
    """about / privacy / contact, from INFO.en (English)."""
    en = data['info']['en'][name]
    h1 = en['h1']
    title = cap_title(h1)
    url = SITE + '/' + name
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
            % (esc(h1), body_inner, esc(name)))
    wld = {"@context": "https://schema.org", "@type": "WebPage",
           "name": title, "url": url, "description": DEF_DESC,
           "isPartOf": {"@type": "WebSite", "name": "Zaika Worlds",
                        "url": SITE + "/"}}
    return page_shell(title, DEF_DESC, url, DEF_IMG, DEF_ALT, [wld], body)


def write_static_pages(data):
    """Write all static pages. Returns {path: bytes}."""
    out = {}

    def w(rel, text):
        path = os.path.join(ROOT, rel)
        write(path, text)
        out[rel] = len(text.encode('utf-8'))

    for r in data['recipes']:
        w('recipe/%s/index.html' % r['id'], recipe_page(data, r))
    for slug in sorted(data['cat_by_slug']):
        li = list_info(data, 'category', slug)
        w('category/%s/index.html' % slug, list_page(data, li))
    for slug in sorted(data['country_by_slug']):
        li = list_info(data, 'country', slug)
        w('country/%s/index.html' % slug, list_page(data, li))
    for name in ('about', 'privacy', 'contact'):
        w('%s/index.html' % name, info_page(data, name))
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
function _ensureLangData(lang){
  if(lang==="en"||_loadedLangs[lang])return Promise.resolve();
  _loadedLangs[lang]=true;
  var jobs=[_loadScript("data/extra-"+lang+".js").then(function(){var g=window["ZAIKA_EXTRA_"+lang.toUpperCase()];if(g)_mergeExtraLang(lang,g);}),_loadScript("data/ui-"+lang+".js").then(function(){var u=window["ZAIKA_UI_"+lang.toUpperCase()];var inf=window["ZAIKA_INFO_"+lang.toUpperCase()];if(u)UI[lang]=u;if(inf)INFO[lang]=inf;})];
  if(lang==="hi"||lang==="ru"){jobs.push(_loadScript("data/lang-data-"+lang+".js").then(function(){var g=window["ZAIKA_LANGDATA_"+lang.toUpperCase()];if(g)_mergeLangData(lang,g);}));}
  return Promise.all(jobs);
}
(function _initZaika(){
  Promise.all([_loadScript("data/recipes.js"),_loadScript("data/extra-en.js"),_loadScript("data/ui-en.js"),_loadScript("data/lang-new.js")]).then(function(){try{_mergeLangNew();}catch(e){if(window.console&&console.error)console.error(e);}return _ensureLangData(LANG);}).then(function(){applyLang();applyRoute();}).catch(function(e){if(window.console&&console.error)console.error(e);if(RECIPES&&RECIPES.length){applyLang();applyRoute();}else{document.body.innerHTML="<p style='font-family:sans-serif;padding:40px'>Zaika Worlds could not load its recipe data. Please refresh the page.</p>";}});
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
    if _patch_n != 78:
        raise JSError("expected 78 UI patch statements, found %d" % _patch_n)
    # EXTRA_NEW per-recipe assignments + whole-language literals — delete.
    for m in re.finditer(r'(?<=[\n;])EXTRA_NEW\.([a-z]+)\.([a-z0-9_-]+)\s*=\s*\[', out):
        j = out.find('[', m.start())
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
        print('check OK: all data blocks parse and validate; '
              'index.html %d bytes.' % fat_bytes)
        return 0

    if mode != 'build':
        print('usage: build_site.py [--check | --source-fix]', file=sys.stderr)
        return 2

    data_files = write_data_files(data)
    static_pages = write_static_pages(data)
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
          '3 info pages' % (len(data['recipes']), len(data['cat_by_slug']),
                            len(data['country_by_slug'])))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv))
    except JSError as e:
        print('build_site.py: ERROR: %s' % e, file=sys.stderr)
        sys.exit(1)
