import { useState } from "react";
import * as api from "../api.js";
import Result from "../components/Result.jsx";
const TYPES = { message: "Message", url: "Link", website: "Website", apk: "Android app" };
const HINT = { message: "Paste the SMS / WhatsApp / email text here…", url: "Paste the link here…", website: "Paste the website address or saved page HTML…", apk: "Paste a Play Store link, or upload an APK below…" };

export default function Check({ onAsk }) {
  const [ch, setCh] = useState("sms"), [t, setT] = useState("message"), [v, setV] = useState(""), [file, setFile] = useState(null);
  const [res, setRes] = useState(null), [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  const run = async () => {
    setBusy(true); setErr("");
    try {
      setRes(t === "message" ? await api.analyzeMessage(v, "citizen", ch) : t === "url" ? await api.analyzeUrl(v) : t === "website" ? await api.analyzeSite(v) : file ? await api.analyzeApk(file) : await api.analyzeStore(v));
    } catch (e) { setErr(e.message); setRes(null); }
    setBusy(false);
  };
  return (
    <>
      <section className="hero plain">
        <div>
          <h1>Got a suspicious message, link or app? <em>Check it before you act.</em></h1>
          <p className="lede">SUDARSHAN explains why something looks like phishing, a fake loan or investment app, or a Ponzi or betting site, and files the evidence for the police.</p>
          <div className="card rule">
            <div className="chips">{Object.entries(TYPES).map(([k, n]) => <button key={k} className={"chip" + (k === t ? " on" : "")} onClick={() => setT(k)}>{n}</button>)}</div>
            {t === "message" && <><label>Where did you receive it?</label><select value={ch} onChange={e => setCh(e.target.value)}><option value="sms">SMS</option><option value="whatsapp">WhatsApp</option><option value="email">Email</option><option value="social">Social media</option></select></>}
            <textarea value={v} onChange={e => setV(e.target.value)} placeholder={HINT[t]} />
            {t === "apk" && <><label>APK file (safe test sample)</label><input type="file" accept=".apk" onChange={e => setFile(e.target.files[0])} /></>}
            <p className="row"><button className="btn" onClick={run} disabled={busy}>{busy ? "Analysing…" : "Analyse"}</button></p>
          </div>
        </div>
        <aside className="card">
          <h3>If you already lost money</h3><p>Call <b>1930</b> at once and report on cybercrime.gov.in. Never share OTP, PIN or CVV.</p>
          <h3>Officers</h3><p>Every check becomes a case with identifiers and an evidence hash in the <a href="#/cases">case register</a>.</p>
        </aside>
      </section>
      {err && <div className="note">{err}</div>}
      {res && <Result c={res} onAsk={onAsk} />}
    </>
  );
}
