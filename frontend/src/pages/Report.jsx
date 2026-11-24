import { useState } from "react";
import * as api from "../api.js";
import Result from "../components/Result.jsx";
export default function Report() {
  const [k, setK] = useState("message"), [v, setV] = useState(""), [r, setR] = useState("citizen"), [res, setRes] = useState(null), [err, setErr] = useState("");
  const submit = async () => { setErr(""); try { setRes(k === "url" ? await api.analyzeUrl(v, r) : await api.analyzeMessage(v, r)); } catch (e) { setErr(e.message); } };
  return (
    <>
      <h1>Report a suspicious item</h1>
      <p className="lede">Open to citizens and officers. Reports feed the heat-list of repeatedly reported domains, numbers, apps and payment IDs.</p>
      <div className="card rule" style={{ maxWidth: 720 }}>
        <label>What are you reporting?</label><select value={k} onChange={e => setK(e.target.value)}><option value="message">Message</option><option value="url">Link</option></select>
        <label>Paste it</label><textarea value={v} onChange={e => setV(e.target.value)} />
        <label>Reported by</label><select value={r} onChange={e => setR(e.target.value)}><option value="citizen">Citizen</option><option value="officer">Officer</option></select>
        <p><button className="btn" onClick={submit}>Submit report</button></p>
      </div>
      {err && <div className="note">{err}</div>}
      {res && <><div className="note">Report filed as case #{res.case_id}. Thank you.</div><Result c={res} /></>}
    </>
  );
}
