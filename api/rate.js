// POST /api/rate — record one anonymous star vote for a recipe.
// Storage: Vercel KV (Upstash Redis) via its REST API. Zero dependencies:
// plain fetch to the REST endpoint, env vars auto-injected by Vercel when
// the store is connected. Supports both env-var names: the native Vercel
// KV integration uses KV_REST_API_URL / KV_REST_API_TOKEN, the Upstash
// Marketplace integration uses UPSTASH_REDIS_REST_URL /
// UPSTASH_REDIS_REST_TOKEN.
// Keys (see ~/workspace/food-blog-videos/rating-feature-design.md):
//   rating:<id>:sum         total of the star values
//   rating:<id>:count       number of votes
//   rated:<id>:<ipHash>     one vote per IP per recipe (permanent marker)
//   rl:<ipHash>:<YYYYMMDD>  votes by this IP today (cap 20/day, TTL 24h)
// The IP is SHA-256 hashed with RATING_SALT; raw IPs are never stored.
'use strict';

const crypto = require('crypto');

const MAX_STARS = 5;
const DAILY_CAP = 20;
const ID_RE = /^[a-z0-9-]{1,64}$/;

function kvConfig() {
  const url = process.env.KV_REST_API_URL
    || process.env.UPSTASH_REDIS_REST_URL || '';
  const token = process.env.KV_REST_API_TOKEN
    || process.env.UPSTASH_REDIS_REST_TOKEN || '';
  return { url: url.replace(/\/$/, ''), token };
}

// One REST command: body ["GET","key"] -> result. Throws on any failure.
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

// Pipeline: body [["INCR","k"],["EXPIRE","k","86400"]] -> [results].
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

function clientIp(req) {
  const xff = req.headers['x-forwarded-for'];
  if (xff) return String(xff).split(',')[0].trim();
  if (req.headers['x-real-ip']) return String(req.headers['x-real-ip']).trim();
  return null;
}

function send(res, status, obj) {
  res.status(status);
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Cache-Control', 'no-store');
  res.end(JSON.stringify(obj));
}

async function aggregate(cfg, id) {
  const r = await kvPipeline(cfg, [['GET', 'rating:' + id + ':sum'],
                                   ['GET', 'rating:' + id + ':count']]);
  const sum = parseInt(r[0] || '0', 10) || 0;
  const count = parseInt(r[1] || '0', 10) || 0;
  return { count, avg: count > 0 ? Math.round(sum / count * 10) / 10 : null };
}

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return send(res, 405, { error: 'method_not_allowed' });
  }
  let body = req.body;
  if (typeof body === 'string') {
    try { body = JSON.parse(body); } catch (e) {
      return send(res, 400, { error: 'invalid' });
    }
  }
  if (!body || typeof body !== 'object') {
    return send(res, 400, { error: 'invalid' });
  }
  const id = body.recipe;
  const stars = body.stars;
  if (typeof id !== 'string' || !ID_RE.test(id)
      || !Number.isInteger(stars) || stars < 1 || stars > MAX_STARS) {
    return send(res, 400, { error: 'invalid' });
  }
  const cfg = kvConfig();
  if (!cfg.url || !cfg.token) return send(res, 503, { error: 'unavailable' });
  const ip = clientIp(req);
  if (!ip) return send(res, 503, { error: 'unavailable' });
  const ipHash = crypto.createHash('sha256')
    .update(ip + (process.env.RATING_SALT || '')).digest('hex');
  const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const dedupeKey = 'rated:' + id + ':' + ipHash;
  const rlKey = 'rl:' + ipHash + ':' + today;
  try {
    // Daily cap first (cheap GET).
    const used = await kvCmd(cfg, ['GET', rlKey]);
    if (used !== null && parseInt(used, 10) >= DAILY_CAP) {
      return send(res, 429, { error: 'rate_limited' });
    }
    // Atomic claim: SET NX succeeds only for the first vote from this IP.
    const claimed = await kvCmd(cfg, ['SET', dedupeKey, '1', 'NX']);
    if (claimed === null) {
      const agg = await aggregate(cfg, id);
      return send(res, 409, Object.assign({ error: 'already_rated' }, agg));
    }
    const r = await kvPipeline(cfg, [
      ['INCRBY', 'rating:' + id + ':sum', stars],
      ['INCR', 'rating:' + id + ':count'],
      ['INCR', rlKey],
      ['EXPIRE', rlKey, '86400'],
    ]);
    const count = parseInt(r[1], 10);
    const sum = parseInt(r[0], 10);
    return send(res, 200, { count,
                            avg: Math.round(sum / count * 10) / 10,
                            yourVote: stars });
  } catch (e) {
    return send(res, 503, { error: 'unavailable' });
  }
};
