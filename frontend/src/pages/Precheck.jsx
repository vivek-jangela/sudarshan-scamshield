import { useState } from "react";
import * as api from "../api.js";
const SAMPLE = ["http://sbi-kyc-update.top/login", "http://indiapost-redeliver.xyz/pay", "https://www.amazon.in/"];
export default function Precheck() {
  const [u, setU] = useState(""), [r, setR] = useState(null), [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  const go = async url => { setBusy(true); setErr(""); try { setR({ url, ...(await api.precheck(url)) }); } catch (e) { setErr(e.message); } setBusy(false); };
  const safeHref = /^https?:\/\//i.test(u) ? u : "http://" + u;
  return (
    <>
      <h1>Link safety check</h1>
      <p className="lede">This is the instant warning a citizen sees before opening a link received on WhatsApp, SMS or email. The same <code>/api/check</code> service will power the browser extension and the chat bot.</p>
      <div className="card rule" style={{ maxWidth: 760 }}>
        <label>Paste the link you received</label>
        <input value={u} onChange={e => setU(e.target.value)} placeholder="http://…" />
        <p className="row"><button className="btn" disabled={!u || busy} onClick={() => go(u)}>{busy ? "Checking…" : "Check before opening"}</button>
          <small>Try:</small>{SAMPLE.map(s => <button key={s} className="link" onClick={() => { setU(s); go(s); }}>{s}</button>)}</p>
      </div>
      {err && <div className="note err">{err}</div>}
      {r && (
        <div className="interstitial">
          <div className={`ibox ${r.level}`}>
            <div className="big">{r.level === "High" ? "⛔" : r.level === "Medium" ? "⚠️" : "✅"}</div>
            <h2>{r.level === "High" ? "Dangerous link blocked" : r.level === "Medium" ? "Suspicious link" : "No strong scam signals"}</h2>
            <code>{r.url}</code>
            <ul>{(r.reasons || []).map((x, i) => <li key={i}>{x}</li>)}</ul>
            <p>{r.advice}</p>
            <div className="row" style={{ justifyContent: "center" }}>
              <button className="btn" onClick={() => setR(null)}>Go back to safety</button>
              {r.level !== "High" && <a className="btn alt" href={safeHref} target="_blank" rel="noopener noreferrer">Open anyway</a>}
              <a className="btn alt" href={`#/case/${r.case_id}`}>View case #{r.case_id}</a>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
