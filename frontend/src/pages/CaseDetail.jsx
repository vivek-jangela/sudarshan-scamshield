import { useEffect, useState } from "react";
import * as api from "../api.js";
import Result, { Badge } from "../components/Result.jsx";
export default function CaseDetail({ id, onAsk }) {
  const [c, setC] = useState(null), [links, setLinks] = useState({ linked_cases: [], edges: [] }), [sim, setSim] = useState([]), [err, setErr] = useState("");
  useEffect(() => {
    setC(null); onAsk(id, false);
    Promise.all([api.getCase(id), api.caseLinks(id), api.caseSimilar(id)]).then(([a, b, s]) => { setC(a); setLinks(b); setSim(s); }).catch(e => setErr(e.message));
  }, [id]);
  if (err) return <div className="note err">{err}</div>;
  if (!c) return <p className="pulse">Loading case…</p>;
  return (
    <>
      <p><a href="#/cases">← Case register</a></p>
      <h1>Case #{c.case_id}</h1>
      <div className="meta"><span>Type <b>{c.kind}</b></span><span>Channel <b>{c.channel || "-"}</b></span><span>Source <b>{c.source || "-"}</b></span><span>Reported by <b>{c.reporter || "-"}</b></span><span>Status <b>{c.status || "new"}</b></span><span>Logged <b>{String(c.created_at || "").slice(0, 16)}</b></span></div>
      <Result c={c} onAsk={cid => onAsk(cid, true)} />
      <div className="card"><h3>Evidence snapshot</h3>
        <pre className="snap">{c.content || "(no content stored)"}</pre>
        <small>SHA-256 integrity hash: <code>{c.evidence_sha256 || "n/a"}</code></small>
      </div>
      <div className="grid2">
        <div className="card"><h3>Linked cases (shared identifiers)</h3>
          {links.linked_cases.length === 0 && <div className="empty">None found.</div>}
          {links.linked_cases.map(n => (
            <div className="ind" key={n.id}><a href={`#/case/${n.id}`}>#{n.id} {n.title}</a> <Badge level={n.level} /><br />
              <small>via {links.edges.filter(e => e.case_id === n.id).map(e => `${e.shared_type}: ${e.shared_value}`).join(", ")}</small></div>))}
        </div>
        <div className="card"><h3>Similar content (repeat campaign)</h3>
          {sim.length === 0 && <div className="empty">None found.</div>}
          {sim.map((s, i) => <div className="ind" key={i}><a href={`#/case/${s.id ?? s.case_id}`}>#{s.id ?? s.case_id} {s.title}</a> <small>{s.similarity != null ? `similarity ${s.similarity}` : ""}</small></div>)}
        </div>
      </div>
    </>
  );
}
