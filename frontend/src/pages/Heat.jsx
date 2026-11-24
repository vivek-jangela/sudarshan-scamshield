import { useEffect, useState } from "react";
import * as api from "../api.js";
export default function Heat() {
  const [t, setT] = useState(""), [h, setH] = useState([]), [err, setErr] = useState("");
  useEffect(() => { api.heatlist(t).then(setH).catch(e => setErr(e.message)); }, [t]);
  return (
    <>
      <h1>Heat-list</h1><p className="lede">Most frequently reported domains, numbers, apps and payment identifiers (Medium and High cases only). Values reported twice or more feed the blacklist.</p>
      <div className="card">
        <select value={t} onChange={e => setT(e.target.value)} style={{ maxWidth: 240 }}>
          <option value="">All types</option>{["domain", "phone", "upi", "package", "crypto", "email", "ip", "bank_account", "cert"].map(x => <option key={x}>{x}</option>)}
        </select>
        {err && <div className="note err">{err}</div>}
        {h.length === 0 && !err ? <div className="empty">Nothing reported yet.</div> : (
          <table><thead><tr><th>Type</th><th>Identifier</th><th>Reports</th></tr></thead>
            <tbody>{h.map((x, i) => <tr key={i}><td>{x.type}</td><td><code>{x.value}</code></td><td><b>{x.reports}</b></td></tr>)}</tbody></table>
        )}
      </div>
    </>
  );
}
