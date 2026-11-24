import { useEffect, useState } from "react";
import * as api from "../api.js";
import { Badge } from "../components/Result.jsx";
const TILES = [["check", "🔎", "Analyse an item", "Message, link, website or Android app with a full risk explanation."], ["precheck", "🛡", "Link safety check", "See the warning a citizen gets before opening a risky link."], ["report", "📣", "Report a scam", "Submit a suspicious item and feed the police heat-list."], ["cases", "🗂", "Case register", "Search every case, evidence snapshot and downloadable report."], ["links", "🕸", "Linked identifiers", "Find one scammer reused across messages, apps and websites."], ["awareness", "📚", "Scam awareness", "Learn the common frauds, warning signs and what to do."]];
export default function Home({ user }) {
  const [d, setD] = useState(null), [err, setErr] = useState("");
  useEffect(() => { Promise.all([api.listCases(), api.heatlist(), api.graph()]).then(([cases, heat, graph]) => setD({ cases, heat, graph })).catch(e => setErr(e.message)); }, []);
  const high = d ? d.cases.filter(c => c.level === "High").length : "–";
  const by = {}; d && d.cases.filter(c => c.level !== "Low").forEach(c => by[c.verdict] = (by[c.verdict] || 0) + 1);
  const mx = Math.max(1, ...Object.values(by));
  return (
    <>
      <section className="hero cyber">
        <div>
          <span className="pill">PS01 · Cyber Fraud / Phishing / Malicious Apps</span>
          <h1>Namaste, {user.name.split(" ")[0]}. <em>Cyber-fraud intelligence</em> for Rajasthan.</h1>
          <p>Analyse suspicious messages, links, apps and websites. Understand exactly why they are risky, and link every scam to the same phone numbers, UPI IDs and domains.</p>
          <div className="row"><a className="btn" href="#/check">Analyse now</a><a className="btn ghost" href="#/report">Report a scam</a></div>
        </div>
        <div className="signal"><b>1930</b><span>National Cyber Crime Helpline</span><small>Lost money? Call within the first hour. Never share OTP, PIN or CVV.</small></div>
      </section>
      {err && <div className="note err">{err}</div>}
      <div className="kpis">
        <div className="kpi"><b>{d ? d.cases.length : "–"}</b><span>Cases analysed</span></div>
        <div className="kpi hi"><b>{high}</b><span>High-risk cases</span></div>
        <div className="kpi"><b>{d ? d.heat.length : "–"}</b><span>Reported identifiers</span></div>
        <div className="kpi"><b>{d ? d.graph.length : "–"}</b><span>Linked scam clusters</span></div>
      </div>
      <h2 className="sec">Services</h2>
      <div className="tiles">{TILES.map(([r, i, t, s]) => <a key={r} className="tile" href={`#/${r}`}><span>{i}</span><b>{t}</b><small>{s}</small></a>)}</div>
      <div className="grid2" style={{ marginTop: 22 }}>
        <div className="card"><h3>Threat landscape</h3>
          {Object.keys(by).length === 0 ? <div className="empty">No medium or high risk cases yet.</div> : Object.entries(by).sort((a, b) => b[1] - a[1]).map(([k, n]) => <div className="bar" key={k}><span>{k.replace(/_/g, " ")}</span><i style={{ width: `${n / mx * 60}%` }} /> {n}</div>)}
        </div>
        <div className="card"><h3>Most reported identifiers</h3>
          {!d || d.heat.length === 0 ? <div className="empty">Nothing reported yet.</div> : <table><tbody>{d.heat.slice(0, 5).map((x, i) => <tr key={i}><td>{x.type}</td><td><code>{x.value}</code></td><td><b>{x.reports}</b></td></tr>)}</tbody></table>}
          <p><a href="#/heat">Full heat-list →</a></p>
        </div>
      </div>
      <div className="card"><h3>Recent cases</h3>
        {!d || d.cases.length === 0 ? <div className="empty">No cases yet. Analyse an item to create one.</div> :
          <table><thead><tr><th>#</th><th>Type</th><th>Title</th><th>Risk</th></tr></thead><tbody>{d.cases.slice(0, 6).map(r => <tr key={r.id} className="go" onClick={() => (location.hash = `#/case/${r.id}`)}><td>{r.id}</td><td>{r.kind}</td><td>{r.title}</td><td><Badge level={r.level} /></td></tr>)}</tbody></table>}
      </div>
    </>
  );
}
