import { useState } from "react";
import { ask } from "../api.js";
// Floating LLM / agent assistant. Wired to POST /api/assistant; works as soon as that endpoint exists.
export default function Assistant({ open, setOpen, caseId }) {
  const [msgs, setMsgs] = useState([{ me: false, t: "Ask about a case, an identifier or a scam pattern. Answers will cite case records." }]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const send = async e => {
    e.preventDefault(); if (!q.trim() || busy) return;
    const question = q; setQ(""); setBusy(true); setMsgs(m => [...m, { me: true, t: question }]);
    try { const r = await ask(question, caseId); setMsgs(m => [...m, { me: false, t: r.answer + (r.sources?.length ? "\n\nSources: " + r.sources.join(", ") : "") }]); }
    catch (err) { setMsgs(m => [...m, { me: false, t: "Assistant not available yet: " + err.message }]); }
    setBusy(false);
  };
  return (
    <>
      <button className="btn ask" onClick={() => setOpen(!open)}>{open ? "Close" : "Ask AI"}</button>
      {open && (
        <div className="panel">
          <header><span>Investigation assistant</span>{caseId && <small>Case #{caseId}</small>}</header>
          <div className="msgs">{msgs.map((m, i) => <div key={i} className={"msg" + (m.me ? " me" : "")}>{m.t}</div>)}</div>
          <form onSubmit={send}><input value={q} onChange={e => setQ(e.target.value)} placeholder="Ask a question…" /><button className="btn sm" disabled={busy}>Send</button></form>
        </div>
      )}
    </>
  );
}
