const OK = "Implemented", PART = "Backend ready, UI basic", NO = "Not in this build";
// Requirement matrix for PS01. Keep this honest: update the status as you build.
const ROWS = [
  ["Must have", "Analyse a message or URL, return a risk level with reasons", "Check, Link safety", OK],
  ["Must have", "Analyse an APK or website and extract identifiers (URLs, phones, UPI)", "Check", OK],
  ["Must have", "Dashboard with case history, search and downloadable report", "Home, Case register", OK],
  ["Feature", "Classify SMS, email, WhatsApp, social text and URLs; urgency, impersonation, fake KYC, look-alike domains, domain age, redirects, HTTPS, blacklist", "Check, Technical details", OK],
  ["Feature", "APK permissions, embedded URLs/IPs, package metadata, comparison with known suspicious apps", "Check, Technical details", OK],
  ["Feature", "Website promises of guaranteed returns, MLM language, betting; hosting details; extract UPI, bank, phone, crypto", "Check", OK],
  ["Feature", "Low / Medium / High with triggering indicators; warn before opening a risky link", "Result panel, Link safety", OK],
  ["Feature", "Searchable case history; linked domains, apps, phones, payment IDs", "Case register, Linked identifiers", OK],
  ["Feature", "Repeat-content and similarity detection", "Case detail", OK],
  ["Feature", "Evidence snapshots and downloadable reports", "Case detail (SHA-256), PDF / HTML", OK],
  ["Feature", "Citizens and officers submit items; heat-list of most reported identifiers", "Report, Heat-list", OK],
  ["Good to have", "Linking the same identifier across messages, apps and websites", "Linked identifiers", OK],
  ["Good to have", "Heat-list of trending scam domains and numbers", "Heat-list, Home", OK],
  ["Good to have", "Browser extension or WhatsApp / Telegram bot", "API ready (/api/check, CORS on)", NO],
  ["Out of scope", "Dynamic malware sandbox, automatic takedown, private data access", "Deliberately excluded", "Excluded"],
];
const STEPS = [["1 · Ingest", "Message, URL, APK, store link or website page."], ["2 · Extract", "URLs, phone numbers, UPI IDs, bank details, wallets, IPs."], ["3 · Analyse", "Rules, reputation, domain and certificate age, permissions, content cues."], ["4 · Explain", "Low, Medium or High with the exact evidence behind it."], ["5 · Investigate", "Link cases, detect repeat campaigns, hash evidence, export report."]];
export default function About() {
  return (
    <>
      <h1>About SUDARSHAN</h1>
      <p className="lede">SUDARSHAN is a unified analysis and investigation platform for PS01 (Cyber Fraud / Phishing / Malicious Apps), built for the Rajasthan Police Hackathon 2026. It uses static analysis only and synthetic data.</p>
      <div className="steps">{STEPS.map(([t, s]) => <div key={t}><b>{t}</b><small>{s}</small></div>)}</div>
      <div className="card"><h3>Problem statement coverage</h3>
        <table><thead><tr><th>Scope</th><th>Requirement</th><th>Where</th><th>Status</th></tr></thead>
          <tbody>{ROWS.map((r, i) => <tr key={i}><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td><span className={"st " + (r[3] === OK ? "ok" : r[3] === NO ? "no" : "ex")}>{r[3]}</span></td></tr>)}</tbody></table>
      </div>
      <div className="grid2">
        <div className="card"><h3>Privacy and safety</h3><ul><li>Synthetic and sample data only; no real personal data.</li><li>No access to private accounts or non-public data.</li><li>All activity is intended to be audit-logged in the final build.</li></ul></div>
        <div className="card"><h3>Roadmap</h3><ul><li>Retrain the message classifier on real R4C samples</li><li>LLM assistant: set ANTHROPIC_API_KEY (a rule-based assistant is built in)</li><li>Browser extension and WhatsApp / Telegram bot</li><li>Server-side authentication and audit log</li></ul></div>
      </div>
    </>
  );
}
