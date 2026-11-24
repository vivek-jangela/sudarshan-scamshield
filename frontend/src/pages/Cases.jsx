import { useEffect, useState } from "react";
import * as api from "../api.js";
import { Badge } from "../components/Result.jsx";
export default function Cases() {
  const [q, setQ] = useState(""), [l, setL] = useState(""), [rows, setRows] = useState([]), [err, setErr] = useState("");
  useEffect(() => { api.listCases(q, l).then(setRows).catch(e => setErr(e.message)); }, [q, l]);
  return (
    <>
      <h1>Case register</h1><p className="lede">Searchable history of every analysed item.</p>
      <div className="card">
        <div className="grid2">
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search domain, phone, UPI, package, text…" />
          <select value={l} onChange={e => setL(e.target.value)}><option value="">All risk levels</option><option>High</option><option>Medium</option><option>Low</option></select>
        </div>
        {err && <div className="note">{err}</div>}
        {rows.length === 0 && !err ? <div className="empty">No cases found.</div> : (
          <table><thead><tr><th>#</th><th>Date</th><th>Type</th><th>Title</th><th>Verdict</th><th>Risk</th></tr></thead>
            <tbody>{rows.map(r => (
              <tr key={r.id} className="go" onClick={() => (location.hash = `#/case/${r.id}`)}>
                <td>{r.id}</td><td>{String(r.created_at || "").slice(0, 16)}</td><td>{r.kind}</td><td>{r.title}</td><td>{String(r.verdict || "").replace(/_/g, " ")}</td><td><Badge level={r.level} /></td>
              </tr>))}</tbody></table>
        )}
      </div>
    </>
  );
}
