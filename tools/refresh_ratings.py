#!/usr/bin/env python3
"""Refresh ratings.json from the Vercel KV (Upstash Redis) store.

The repo snapshot ratings.json is the durable record of real visitor
ratings; the daily new-recipe run calls this before building, so a new
deploy carries fresh aggregates into the static pages' JSON-LD and into
data/recipes.js (see rating-feature-design.md).

Merge rule — never regress: for each recipe, count and sum are the max
of the KV value and the snapshot value. If KV lost a key (idle expiry)
or a write was torn, the snapshot preserves the higher real value.
Only recipes with count > 0 are kept. `avg` is derived (round(sum /
count, 1)); `updated` is the refresh date (Asia/Karachi) when the
numbers moved, otherwise the previous date. Nothing here invents a
rating: every number comes from a real vote stored in KV.

Credentials come from the environment: KV_REST_API_URL /
KV_REST_API_TOKEN (native Vercel KV) or UPSTASH_REDIS_REST_URL /
UPSTASH_REDIS_REST_TOKEN (Upstash Marketplace integration). With no
credentials the refresh is skipped (exit 0) so the daily build is never
blocked; a KV failure also keeps the existing snapshot (exit 0). Only
a corrupt snapshot file is a hard error (exit 1).
"""
import json
import os
import sys
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP_PATH = os.path.join(ROOT, 'ratings.json')


def kv_env():
    url = (os.environ.get('KV_REST_API_URL')
           or os.environ.get('UPSTASH_REDIS_REST_URL') or '')
    token = (os.environ.get('KV_REST_API_TOKEN')
             or os.environ.get('UPSTASH_REDIS_REST_TOKEN') or '')
    return url.rstrip('/'), token


def kv_post(url, token, path, body, timeout=10):
    req = urllib.request.Request(
        url + path,
        data=json.dumps(body).encode('utf-8'),
        headers={'Authorization': 'Bearer ' + token,
                 'Content-Type': 'application/json'},
        method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        out = json.load(resp)
    if out.get('error'):
        raise RuntimeError('KV error: %s' % out['error'])
    return out['result']


def fetch_live(url, token):
    """All rating aggregates from KV: {rid: {'count': n, 'sum': n}}."""
    ids = []
    cursor = '0'
    for _ in range(10):
        cursor, keys = kv_post(url, token, '',
                               ['SCAN', cursor, 'MATCH', 'rating:*:count',
                                'COUNT', '100'])
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
        vals = kv_post(url, token, '/pipeline', cmds)
        for i, rid in enumerate(ids):
            live[rid] = {'count': int(vals[i * 2 + 1] or 0),
                         'sum': int(vals[i * 2] or 0)}
    return live


def main():
    url, token = kv_env()
    if not url or not token:
        print('ratings refresh skipped: no KV credentials in environment '
              '(KV_REST_API_URL/KV_REST_API_TOKEN or '
              'UPSTASH_REDIS_REST_URL/UPSTASH_REDIS_REST_TOKEN)')
        return 0
    snap = {}
    if os.path.exists(SNAP_PATH):
        with open(SNAP_PATH, encoding='utf-8') as f:
            snap = json.load(f) or {}
    if not isinstance(snap, dict):
        print('ratings.json is not an object; refusing to overwrite',
              file=sys.stderr)
        return 1
    try:
        live = fetch_live(url, token)
    except Exception as e:
        print('ratings refresh failed (%s); keeping existing snapshot' % e,
              file=sys.stderr)
        return 0
    today = datetime.now(ZoneInfo('Asia/Karachi')).date().isoformat()
    for rid, vals in live.items():
        old = snap.get(rid) or {}
        count = max(int(vals.get('count') or 0), int(old.get('count') or 0))
        total = max(int(vals.get('sum') or 0), int(old.get('sum') or 0))
        if count <= 0:
            continue
        entry = {'count': count, 'sum': total,
                 'avg': round(total / count, 1),
                 'updated': (today if (count != int(old.get('count') or 0)
                                       or total != int(old.get('sum') or 0))
                             else old.get('updated') or today)}
        snap[rid] = entry
    # Defensive: only well-formed entries with real votes are kept.
    snap = {k: v for k, v in snap.items()
            if isinstance(v, dict) and v.get('count', 0) > 0}
    tmp = SNAP_PATH + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(snap, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')
    os.replace(tmp, SNAP_PATH)
    print('ratings.json refreshed: %d recipe(s) with ratings'
          % len(snap))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
