import { reportUrl } from "../api.js";
const pretty = s => String(s || "").replace(/_/g, " ");
export const Badge = ({ level }) => <span className={`badge ${level}`}>{level}</span>;
const HEAD = { High: "High risk. Do not proceed.", Medium: "Medium risk. Verify first.", Low: "Low risk. No strong scam signals." };
const fmt = v => Array.isArray(v) ? v.map(x => typeof x === "object" ? JSON.stringify(x) : x).join(" → ") : typeof v === "object" ? JSON.stringify(v) : String(v);
// Flatten info (domain age, redirects, HTTPS, APK package/cert, ...) into rows; unknown keys still show.
const rowsOf = (info = {}) => Object.entries(info).filter(([k]) => k !== "identifiers").flatMap(([k, v]) =>
  v && typeof v === "object" && !Array.isArray(v) ? Object.entries(v).map(([a, b]) => [`${k}.${a}`, b]) : [[k, v]]).filter(([, v]) => v !== "" && v != null);

export default function Result({ c, onAsk }) {
  const ids = Object.entries(c.identifiers || {}), tech = rowsOf(c.info);
  return (
    <>
      <div className={`verdict ${c.level}`}>
        <h2>{HEAD[c.level] || c.level}</h2>
        <div>Classification: <b>{pretty(c.verdict)}</b> · risk score {Math.round((c.score || 0) * 100)}%</div>
        <div className="meter"><i style={{ width: `${(c.score || 0) * 100}%` }} /></div>
        <p style={{ margin: "10px 0 0" }}>{c.advice}</p>
      </div>
      <div className="card">
        <h3>Why this result: triggered indicators</h3>
        {(c.indicators || []).length === 0 && <div className="empty">No indicators triggered.</div>}
        {(c.indicators || []).map((i, k) => (
          <div className="ind" key={k}><b>{i.explanation}</b> <small>{pretty(i.category)} · {i.source} · weight {i.weight}</small><br /><small>Evidence:</small> <code>{i.evidence}</code></div>
        ))}
      </div>
      <div className="grid2">
        <div className="card"><h3>Extracted identifiers</h3>
          {ids.length === 0 && <div className="empty">No identifiers found.</div>}
          {ids.map(([t, v]) => <div className="idrow" key={t}><b>{t}</b>{v.map(x => <span className="id" key={x} style={{ marginRight: 6 }}>{x}</span>)}</div>)}
        </div>
        <div className="card"><h3>Technical details</h3>
          {tech.length === 0 ? <div className="empty">No technical details recorded.</div> :
            <table className="kv"><tbody>{tech.map(([k, v]) => <tr key={k}><th>{pretty(k)}</th><td>{fmt(v)}</td></tr>)}</tbody></table>}
        </div>
      </div>
      <p className="row">
        <a className="btn sm" href={reportUrl(c.case_id, "pdf")} target="_blank" rel="noreferrer">Report (PDF)</a>
        <a className="btn sm alt" href={reportUrl(c.case_id, "html")} target="_blank" rel="noreferrer">Report (HTML)</a>
        <a className="btn sm alt" href={`#/case/${c.case_id}`}>Open case #{c.case_id}</a>
        {onAsk && <button className="btn sm alt" onClick={() => onAsk(c.case_id)}>Ask AI about this</button>}
      </p>
    </>
  );
}
