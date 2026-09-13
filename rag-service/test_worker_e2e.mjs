/**
 * End-to-end test of the RAG-augmented Cloudflare Worker.
 *
 * The worker module only uses fetch/Request/Response, so we import it directly,
 * point RAG_URL at the locally running retrieval service (real retrieval, real
 * embeddings) and stub only the LLM providers so no API quota is spent.
 *
 * Run:  node test_worker_e2e.mjs      (rag_service.py must be listening on 8088)
 */
import { fileURLToPath, pathToFileURL } from 'node:url';

// Resolve ../worker.js relative to this file (override with WORKER_JS=...)
const WORKER_PATH = process.env.WORKER_JS || fileURLToPath(new URL('../worker.js', import.meta.url));
const worker = (await import(pathToFileURL(WORKER_PATH).href)).default;
console.log('worker module: ' + WORKER_PATH);

const RAG_URL = 'http://127.0.0.1:8088';
const REAL_FETCH = globalThis.fetch;

let captured = [];
let failures = 0;

function ok(label, cond, detail) {
  console.log((cond ? 'PASS  ' : 'FAIL  ') + label + (detail ? '   -> ' + detail : ''));
  if (!cond) failures++;
}
const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

globalThis.fetch = async (url, init) => {
  const u = String(url);
  if (u.startsWith(RAG_URL)) return REAL_FETCH(url, init);          // real retrieval
  if (u.includes('generativelanguage.googleapis.com')) {
    captured.push({ provider: 'gemini', body: JSON.parse(init.body) });
    return json({ candidates: [{ content: { parts: [{ text: 'STUB-GEMINI-ANSWER' }] } }] });
  }
  if (u.includes('openrouter.ai')) {
    captured.push({ provider: 'openrouter', body: JSON.parse(init.body) });
    return json({ choices: [{ message: { content: 'STUB-OPENROUTER-ANSWER' } }] });
  }
  throw new Error('unexpected fetch: ' + u);
};

const call = (body, env) =>
  worker.fetch(new Request('https://worker.test/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }), env);

const KEY = { GEMINI_API_KEY: 'test-key' };
const sysText = (c) => c.body.systemInstruction.parts[0].text;

// ---------------------------------------------------------------- 1. RAG on
console.log('\n[1] RAG enabled');
captured = [];
let res = await call({ message: 'What does the journal say about the investigative judgment and the heavenly sanctuary?' },
  { ...KEY, RAG_URL });
let data = await res.json();
ok('HTTP 200', res.status === 200, 'status ' + res.status);
ok('answer returned', data.text === 'STUB-GEMINI-ANSWER', data.text);
ok('grounding block injected', sysText(captured[0]).includes('=== RETRIEVED PASSAGES'), 'len=' + sysText(captured[0]).length);
ok('grounding block closed', sysText(captured[0]).includes('=== END RETRIEVED PASSAGES ==='));
ok('base system prompt preserved', sysText(captured[0]).includes('HALLUCINATION MITIGATION PROTOCOL'));
ok('sources returned', Array.isArray(data.sources) && data.sources.length > 0, JSON.stringify(data.sources?.[0]));
ok('source has citation', !!(data.sources?.[0]?.citation), data.sources?.[0]?.citation);
ok('rag meta reports usage', data.rag?.used === true && data.rag.passages > 0, JSON.stringify(data.rag));
console.log('      top source: ' + data.sources[0].citation + '  (' + data.sources[0].source + ')');
console.log('      system prompt grew by ' + (sysText(captured[0]).length - sysText(captured[0]).indexOf('=== RETRIEVED')).toString() + ' chars of grounding');

// ------------------------------------------------------------ 2. RAG absent
console.log('\n[2] RAG disabled (no RAG_URL) - legacy behaviour');
captured = [];
res = await call({ message: 'What does the journal say about the investigative judgment?' }, { ...KEY });
data = await res.json();
ok('HTTP 200', res.status === 200);
ok('no grounding block', !sysText(captured[0]).includes('RETRIEVED PASSAGES'));
ok('no sources', Array.isArray(data.sources) && data.sources.length === 0);
ok('rag.used false', data.rag?.used === false, JSON.stringify(data.rag));

// ------------------------------------------------------- 3. RAG service down
console.log('\n[3] RAG service unreachable - degrades gracefully');
captured = [];
res = await call({ message: 'Sanctuary doctrine in the JATS corpus' },
  { ...KEY, RAG_URL: 'http://127.0.0.1:59999' });
data = await res.json();
ok('request still succeeds', res.status === 200 && data.text === 'STUB-GEMINI-ANSWER', data.text);
ok('no grounding block', !sysText(captured[0]).includes('RETRIEVED PASSAGES'));
ok('error surfaced in rag meta', !!data.rag?.error, data.rag?.error);

// ------------------------------------------------------------ 4. per-request opt-out
console.log('\n[4] per-request opt-out (useRag:false)');
captured = [];
res = await call({ message: 'Investigative judgment', useRag: false }, { ...KEY, RAG_URL });
data = await res.json();
ok('no grounding block', !sysText(captured[0]).includes('RETRIEVED PASSAGES'));
ok('no sources', data.sources.length === 0);

// --------------------------------------------- 5. global kill switch
console.log('\n[5] RAG_DISABLED kill switch');
captured = [];
res = await call({ message: 'Investigative judgment' }, { ...KEY, RAG_URL, RAG_DISABLED: 'true' });
data = await res.json();
ok('no grounding block', !sysText(captured[0]).includes('RETRIEVED PASSAGES'));

// ------------------------------------------------- 6. follow-up uses history
console.log('\n[6] short follow-up pulls context from history');
captured = [];
res = await call({
  message: 'Tell me more.',
  history: [{ user: 'What does the JATS say about the sanctuary doctrine?', assistant: 'A long answer.' }],
}, { ...KEY, RAG_URL });
data = await res.json();
ok('retrieval query merged with previous turn',
  typeof data.rag.query === 'string' && data.rag.query.includes('sanctuary'), data.rag.query);

// ------------------------------------------------------------ 7. essay mode
console.log('\n[7] essay mode response shape');
captured = [];
res = await call({ message: 'The investigative judgment in Adventist thought', essayMode: true }, { ...KEY, RAG_URL });
data = await res.json();
ok('essay field present', typeof data.essay === 'string' && data.essay === 'STUB-GEMINI-ANSWER', data.essay);
ok('summary text present', typeof data.text === 'string' && data.text.includes('download bar'));
ok('sources still returned', data.sources.length > 0, String(data.sources.length));
ok('grounding injected in essay mode', sysText(captured[0]).includes('RETRIEVED PASSAGES'));

// ----------------------------------------------------------- 8. sermon mode
console.log('\n[8] sermon mode response shape');
captured = [];
res = await call({ message: 'A sermon on the Sabbath', sermonMode: true, sermonFormat: 'topical' }, { ...KEY, RAG_URL });
data = await res.json();
ok('essay field carries full sermon', data.essay === 'STUB-GEMINI-ANSWER');
ok('sources returned', data.sources.length > 0);
ok('grounding injected in sermon mode', sysText(captured[0]).includes('RETRIEVED PASSAGES'));

// ------------------------------------------------------ 9. openrouter fallback
console.log('\n[9] OpenRouter fallback path carries grounding');
captured = [];
res = await call({ message: 'Sanctuary doctrine' }, { OPENROUTER_API_KEY: 'or-key', RAG_URL });
data = await res.json();
ok('openrouter used', data.provider === 'openrouter', data.provider);
ok('grounding in openrouter system message',
  captured[0].body.messages[0].role === 'system' && captured[0].body.messages[0].content.includes('RETRIEVED PASSAGES'));

console.log('\n' + (failures === 0 ? 'ALL CHECKS PASSED' : failures + ' CHECK(S) FAILED'));
process.exit(failures === 0 ? 0 : 1);
