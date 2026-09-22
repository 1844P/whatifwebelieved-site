// Vercel serverless function: /api/rag/search -> JATS RAG service.
//
// Bridges the Cloudflare Worker -> Vercel -> local JATS RAG tunnel.
// Cloudflare Workers cannot call *.trycloudflare.com quick tunnels directly
// (they return HTTP 530), so the Worker instead calls this stable endpoint on
// the site host (https://whatifwebelieved.vercel.app/api/rag) and it proxies
// to the tunneled rag-service.
//
// Env vars (Vercel > Project > Settings > Environment Variables):
//   RAG_TUNNEL_URL    base URL of the tunneled rag-service, e.g.
//                     https://xxxx.trycloudflare.com  (no trailing slash)
//   RAG_TUNNEL_TOKEN  optional shared secret forwarded as the x-rag-token header

export default async function handler(req, res) {
  const cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, x-rag-token, Authorization',
  };

  if (req.method === 'OPTIONS') {
    res.writeHead(204, cors).end();
    return;
  }

  const tunnel = String(process.env.RAG_TUNNEL_URL || '')
    .trim()
    .replace(/\/+$/, '');
  if (!tunnel) {
    res
      .writeHead(502, { ...cors, 'Content-Type': 'application/json' })
      .end(JSON.stringify({ error: 'RAG_TUNNEL_URL not configured on Vercel' }));
    return;
  }

  const target = tunnel + '/search';
  const timeoutMs = Number(process.env.RAG_PROXY_TIMEOUT_MS || 28000);

  try {
    let upstream;
    if (req.method === 'GET') {
      const url = new URL(req.url, 'http://x');
      const q = encodeURIComponent(url.searchParams.get('q') || '');
      const k = url.searchParams.get('k') || '6';
      const ms = url.searchParams.get('min_score') || '';
      const query = '?q=' + q + '&k=' + k + (ms ? '&min_score=' + ms : '');
      upstream = await fetch(target + query, {
        signal: AbortSignal.timeout(timeoutMs),
      });
    } else {
      const token = String(process.env.RAG_TUNNEL_TOKEN || '').trim();
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['x-rag-token'] = token;
      upstream = await fetch(target, {
        method: 'POST',
        headers,
        body: JSON.stringify(req.body || {}),
        signal: AbortSignal.timeout(timeoutMs),
      });
    }

    const text = await upstream.text();
    const ct = upstream.headers.get('content-type') || 'application/json';
    res.writeHead(upstream.status, { ...cors, 'Content-Type': ct }).end(text);
  } catch (e) {
    res
      .writeHead(502, { ...cors, 'Content-Type': 'application/json' })
      .end(
        JSON.stringify({
          error: 'rag proxy: ' + (e && e.message ? e.message : String(e)),
        })
      );
  }
}