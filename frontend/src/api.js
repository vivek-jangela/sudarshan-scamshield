// The ONLY file that talks to the FastAPI backend (app/main.py). Pages never call fetch directly.
// Every function returns data in the UI shape below, so backend or model changes stay inside this file.
//   Result: { case_id, kind, score, level, verdict, advice, indicators[], identifiers{type:[values]}, info }
const parse = (v, d) => { if (typeof v !== "string") return v ?? d; try { return JSON.parse(v); } catch { return d; } };
async function http(path, opts) {
  let r;
  try { r = await fetch(path, opts); } catch { throw new Error("Cannot reach the backend. Start it with: uvicorn app.main:app --reload"); }
  if (!r.ok) { const d = await r.json().catch(() => ({})); throw new Error(d.detail || r.statusText); }
  return r.json();
}
const post = (path, body) => http(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
const form = (path, fields) => { const f = new FormData(); Object.entries(fields).forEach(([k, v]) => f.append(k, v)); return http(path, { method: "POST", body: f }); };
const toIds = x => Array.isArray(x) ? x.reduce((o, i) => ((o[i.type] ||= []).push(i.value), o), {}) : (parse(x, {}) || {});
const norm = d => ({ ...d, case_id: d.case_id ?? d.id, indicators: parse(d.indicators, []), identifiers: toIds(d.identifiers), info: parse(d.info, {}) });

export const analyzeMessage = (text, reporter = "citizen", channel = "sms") => post("/api/analyze/message", { text, reporter, channel }).then(norm);
export const analyzeUrl = (url, reporter = "citizen") => post("/api/analyze/url", { url, reporter }).then(norm);
export const analyzeSite = (v, reporter = "citizen") => post("/api/analyze/website", v.trim().startsWith("<") ? { html: v, reporter } : { url: v, reporter }).then(norm);
export const analyzeApk = (file, reporter = "officer") => form("/api/analyze/apk", { file, reporter }).then(norm);
export const analyzeStore = link => form("/api/analyze/store-link", { link }).then(norm);
export const precheck = url => http("/api/check?url=" + encodeURIComponent(url));          // {level, score, reasons[], advice, case_id}
export const listCases = (q = "", level = "", kind = "") => http(`/api/cases?q=${encodeURIComponent(q)}&level=${level}&kind=${kind}`);
export const getCase = id => http("/api/cases/" + id).then(norm);
export const caseLinks = id => http(`/api/cases/${id}/links`);                                // {linked_cases[], edges[]}
export const caseSimilar = id => http(`/api/cases/${id}/similar`);
export const reportUrl = (id, fmt = "html") => `/api/cases/${id}/report?format=${fmt}`;
export const heatlist = (type = "") => http("/api/heatlist?type=" + type);                   // [{type, value, reports}]
export const graph = () => http("/api/graph");                                                // [{type, value, cases[]}]
// LLM / agentic assistant: add POST /api/assistant {question, case_id?} -> {answer, sources[]} when the model is ready.
export const ask = (question, case_id) => post("/api/assistant", { question, case_id });
