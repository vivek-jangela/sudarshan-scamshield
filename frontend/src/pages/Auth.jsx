import { useState } from "react";
import { login, signup } from "../auth.js";
import BrandMark from "../components/BrandMark.jsx";

const DISTRICTS = ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer", "Bikaner", "Alwar", "Bharatpur", "Sikar", "Other"];

export default function Auth({ onAuth }) {
  const [mode, setMode] = useState("login"), [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  const [f, setF] = useState({ name: "", email: "", role: "citizen", officerId: "", district: "Jaipur", password: "", confirm: "", agree: false });
  const set = k => e => setF({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });
  const submit = async e => {
    e.preventDefault(); setErr("");
    if (mode === "signup") {
      if (f.password.length < 8) return setErr("Password must be at least 8 characters.");
      if (f.password !== f.confirm) return setErr("Passwords do not match.");
      if (f.role === "officer" && !/^RJ-[A-Z]{2}-\d{4}$/.test(f.officerId)) return setErr("Officer ID format: RJ-IO-0421");
      if (!f.agree) return setErr("Please accept the declaration to continue.");
    }
    setBusy(true);
    try { onAuth(mode === "login" ? await login(f.email, f.password) : await signup(f)); }
    catch (x) { setErr(x.message); }
    setBusy(false);
  };

  return (
    <div className="authwrap">
      <div className="band" />
      <div className="notice"><span>⚠</span> Hackathon prototype (PS01). Synthetic data only. Not an official Rajasthan Police website.</div>
      <div className="auth-utility"><span>राजस्थान सरकार · डिजिटल सुरक्षा पहल</span><span>Skip to main content&nbsp;&nbsp; | &nbsp;&nbsp;A− &nbsp; A &nbsp; A+ &nbsp; | &nbsp; English</span></div>
      <header className="auth-masthead">
        <a className="auth-masthead-brand" href="#/">
          <BrandMark />
          <span><b>SUDARSHAN</b><small>Cyber Fraud Intelligence &amp; Investigation Support</small></span>
        </a>
        <nav className="auth-masthead-nav" aria-label="Portal navigation">
          <a href="#auth-approach">Approach</a><a href="#auth-capabilities">Capabilities</a><a href="#auth-security">Security</a><a href="#auth-workflow">Workflow</a>
          <button type="button" onClick={() => { setMode("login"); setErr(""); }}>Officer Login</button>
        </nav>
      </header>
      <div className="authgrid" id="main-content">
        <section className="cyberpanel">
          <div className="auth-brand">
            <BrandMark />
            <span><b>SUDARSHAN</b><small>राजस्थान साइबर सुरक्षा · Cyber Fraud Intelligence Desk</small></span>
          </div>
          <div className="auth-kicker" id="auth-approach">PS01 · TELECOM &amp; CYBER FRAUD INTELLIGENCE</div>
          <h1>From suspicious clicks to <em>verified protection.</em></h1>
          <p className="auth-intro">A unified cyber-fraud support platform to analyse phishing messages, suspicious links, fake loan and investment apps, and fraudulent websites.</p>
          <div className="auth-feature-grid" id="auth-capabilities">
            <div><b>01</b><span>Explainable risk assessment</span></div>
            <div><b>02</b><span>Linked phone, UPI &amp; app identifiers</span></div>
            <div><b>03</b><span>Evidence-backed case reports</span></div>
            <div><b>04</b><span>Citizen and officer services</span></div>
          </div>
          <div className="helpline">
            <b>1930</b><span><strong>National Cyber Crime Helpline</strong><small>Report financial cyber fraud immediately</small></span>
          </div>
          <div className="auth-image-caption" id="auth-workflow">RAJASTHAN · CYBER AWARENESS · DIGITAL SAFETY</div>
        </section>

        <section className="auth-side">
          <div className="authcard">
            <div className="auth-card-brand"><BrandMark compact /><span><b>SUDARSHAN</b><small>Secure portal access</small></span></div>
            <div className="auth-eyebrow">AUTHORISED PORTAL ACCESS</div>
            <div className="tabs2">
              <button type="button" className={mode === "login" ? "on" : ""} onClick={() => { setMode("login"); setErr(""); }}>Log in</button>
              <button type="button" className={mode === "signup" ? "on" : ""} onClick={() => { setMode("signup"); setErr(""); }}>Sign up</button>
            </div>
            <h2>{mode === "login" ? "Welcome back" : "Create your account"}</h2>
            <p className="auth-subtitle">{mode === "login" ? "Sign in to continue to the cyber fraud intelligence portal." : "Register for citizen or authorised officer access."}</p>
            <form onSubmit={submit}>
              {mode === "signup" && <>
                <label>Full name</label><input required autoComplete="name" value={f.name} onChange={set("name")} placeholder="Enter your full name" />
                <label>Account type</label><select value={f.role} onChange={set("role")}><option value="citizen">Citizen</option><option value="officer">Authorised officer</option></select>
                {f.role === "officer" && <div className="grid2"><div><label>Officer ID</label><input required placeholder="RJ-IO-0421" value={f.officerId} onChange={set("officerId")} /></div><div><label>District</label><select value={f.district} onChange={set("district")}>{DISTRICTS.map(d => <option key={d}>{d}</option>)}</select></div></div>}
              </>}
              <label>Email address</label><input type="email" required autoComplete="email" value={f.email} onChange={set("email")} placeholder="name@example.com" />
              <label>Password</label><input type="password" required autoComplete={mode === "login" ? "current-password" : "new-password"} value={f.password} onChange={set("password")} placeholder="Enter your password" />
              {mode === "signup" && <>
                <label>Confirm password</label><input type="password" required autoComplete="new-password" value={f.confirm} onChange={set("confirm")} placeholder="Re-enter your password" />
                <label className="chk"><input type="checkbox" checked={f.agree} onChange={set("agree")} /> I will submit only genuine reports and understand that portal activity is logged.</label>
              </>}
              {err && <div className="note err" role="alert">{err}</div>}
              <button className="btn auth-submit" style={{ width: "100%", marginTop: 16 }} disabled={busy}>{busy ? "Please wait…" : mode === "login" ? "Sign in securely  →" : "Create account  →"}</button>
            </form>
            <div className="auth-security" id="auth-security"><span>▣</span> Protected access · Session activity may be logged</div>
            <small className="pulse">Prototype: accounts are stored in this browser only. The final build uses server-side authentication. Never enter real personal data.</small>
          </div>
          <div className="auth-side-footer">SUDARSHAN · PS01 · Rajasthan Cyber Security Hackathon 2026</div>
        </section>
      </div>
    </div>
  );
}
