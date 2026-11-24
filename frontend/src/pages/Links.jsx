import { useEffect, useState } from "react";
import * as api from "../api.js";
export default function Links() {
  const [g, setG] = useState([]), [err, setErr] = useState("");
  useEffect(() => { api.graph().then(setG).catch(e => setErr(e.message)); }, []);
  return (
    <>
      <h1>Linked identifiers</h1>
      <p className="lede">The same phone, UPI ID, domain or app reused across messages, apps and websites points to one operator.</p>
      {err && <div className="note">{err}</div>}
      {g.length === 0 && !err && <div className="card empty">No shared identifiers yet.</div>}
      {g.map((x, i) => (
        <div className="card" key={i}>
          <b>{x.type}</b> <code>{x.value}</code> <span className="pulse">appears in {x.cases.length} cases</span>
          <div className="row" style={{ marginTop: 8 }}>{x.cases.map(c => <a key={c} className="btn sm alt" href={`#/case/${c}`}>Case #{c}</a>)}</div>
        </div>
      ))}
    </>
  );
}
