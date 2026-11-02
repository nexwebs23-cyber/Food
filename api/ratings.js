// GET /api/ratings — read real visitor-rating aggregates from Vercel KV
// (Upstash Redis) via its REST API. Zero dependencies; env vars as in
// api/rate.js (KV_REST_API_URL / KV_REST_API_TOKEN or
// UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN).
//   GET /api/ratings?recipe=<id>  -> {recipe, count, avg}
//   GET /api/ratings?all=1        -> {ratings: {<id>: {count, avg}}}
// avg is null when a recipe has no votes yet.
'use strict';

const ID_RE = /^[a-z0-9-]{1,64}$/;

function kvConfig() {
  const url = process.env.KV_REST_API_URL
    || process.env.UPSTASH_REDIS_REST_URL || '';
  const token = process.env.KV_REST_API_TOKEN
    || process.env.UPSTASH_REDIS_REST_TOKEN || '';
  return { url: url.replace(/\/$/, ''), token };
}

async function kvCmd(cfg, cmd) {
  const res = await fetch(cfg.url, {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + cfg.token,
               'Content-Type': 'application/json' },
    body: JSON.stringify(cmd),
  });
  if (!res.ok) throw new Error('kv_http_' + res.status);
  const j = await res.json();
  if (j.error) throw new Error('kv_error_' + j.error);
  return j.result;
}

async function kvPipeline(cfg, cmds) {
  const res = await fetch(cfg.url + '/pipeline', {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + cfg.token,
               'Content-Type': 'application/json' },
    body: JSON.stringify(cmds),
  });
  if (!res.ok) throw new Error('kv_http_' + res.status);
  const j = await res.json();
  if (j.error) throw new Error('kv_error_' + j.error);
  return j.result;
}

function send(res, status, obj) {
  res.status(status);
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Cache-Control', 'no-store');
  res.end(JSON.stringify(obj));
}

function avgOf(sum, count) {
  return count > 0 ? Math.round(sum / count * 10) / 10 : null;
}

module.exports = async (req, res) => {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return send(res, 405, { error: 'method_not_allowed' });
  }
  const cfg = kvConfig();
  if (!cfg.url || !cfg.token) return send(res, 503, { error: 'unavailable' });
  try {
    if (req.query && req.query.all === '1') {
      // SCAN for rating:*:count keys, then fetch sum+count per recipe.
      const ids = [];
      let cursor = '0';
      let guard = 0;
      do {
        const r = await kvCmd(cfg, ['SCAN', cursor, 'MATCH',
                                    'rating:*:count', 'COUNT', '100']);
        cursor = r[0];
        for (const k of r[1] || []) {
          const m = /^rating:(.+):count$/.exec(k);
          if (m && ID_RE.test(m[1])) ids.push(m[1]);
        }
        guard++;
      } while (cursor !== '0' && guard < 10);
      const out = {};
      if (ids.length) {
        const cmds = [];
        for (const id of ids) {
          cmds.push(['GET', 'rating:' + id + ':sum']);
          cmds.push(['GET', 'rating:' + id + ':count']);
        }
        const vals = await kvPipeline(cfg, cmds);
        ids.forEach((id, i) => {
          const sum = parseInt(vals[i * 2] || '0', 10) || 0;
          const count = parseInt(vals[i * 2 + 1] || '0', 10) || 0;
          out[id] = { count, avg: avgOf(sum, count) };
        });
      }
      return send(res, 200, { ratings: out });
    }
    const id = req.query && req.query.recipe;
    if (typeof id !== 'string' || !ID_RE.test(id)) {
      return send(res, 400, { error: 'invalid' });
    }
    const vals = await kvPipeline(cfg, [['GET', 'rating:' + id + ':sum'],
                                        ['GET', 'rating:' + id + ':count']]);
    const sum = parseInt(vals[0] || '0', 10) || 0;
    const count = parseInt(vals[1] || '0', 10) || 0;
    return send(res, 200, { recipe: id, count, avg: avgOf(sum, count) });
  } catch (e) {
    return send(res, 503, { error: 'unavailable' });
  }
};
