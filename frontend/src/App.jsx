import { useEffect, useState } from "react";
import { current, logout } from "./auth.js";
import Auth from "./pages/Auth.jsx";
import Home from "./pages/Home.jsx";
import Check from "./pages/Check.jsx";
import Precheck from "./pages/Precheck.jsx";
import Report from "./pages/Report.jsx";
import Cases from "./pages/Cases.jsx";
import CaseDetail from "./pages/CaseDetail.jsx";
import Links from "./pages/Links.jsx";
import Heat from "./pages/Heat.jsx";
import Awareness from "./pages/Awareness.jsx";
import About from "./pages/About.jsx";
import Assistant from "./components/Assistant.jsx";
import BrandMark from "./components/BrandMark.jsx";

const NAV = [["", "🏠", "Home"], ["check", "🔎", "Analyse"], ["precheck", "🛡", "Link safety check"], ["report", "📣", "Report a scam"], ["cases", "🗂", "Case register"], ["links", "🕸", "Linked identifiers"], ["heat", "🔥", "Heat-list"], ["awareness", "📚", "Scam awareness"], ["about", "ℹ️", "About & coverage"]];
const NEWS = ["Never share OTP, PIN or CVV with anyone, including bank officials", "Fake KYC and electricity-bill SMS are the most reported frauds", "Install loan and investment apps only from official stores", "Lost money? Call 1930 immediately and file at cybercrime.gov.in"];
const useHash = () => { const [h, setH] = useState(location.hash.slice(2)); useEffect(() => { const f = () => setH(location.hash.slice(2)); addEventListener("hashchange", f); return () => removeEventListener("hashchange", f); }, []); return h.split("/"); };

export default function App() {
  const [user, setUser] = useState(current());
  const [route = "", id] = useHash();
  const [open, setOpen] = useState(false), [aiCase, setAiCase] = useState(null), [pct, setPct] = useState(0), [fz, setFz] = useState(16);
  useEffect(() => { window.scrollTo({ top: 0, behavior: "smooth" }); }, [route, id]);
  useEffect(() => { const f = () => setPct(Math.min(100, scrollY / Math.max(1, document.body.scrollHeight - innerHeight) * 100)); addEventListener("scroll", f); return () => removeEventListener("scroll", f); }, []);
  useEffect(() => { document.documentElement.style.fontSize = fz + "px"; }, [fz]);
  if (!user) return <Auth onAuth={setUser} />;
  const onAsk = (cid, show = true) => { setAiCase(cid); if (show) setOpen(true); };
  const active = route === "case" ? "cases" : route;
  const page = { check: <Check onAsk={onAsk} />, precheck: <Precheck />, report: <Report />, cases: <Cases />, case: <CaseDetail id={id} onAsk={onAsk} />, links: <Links />, heat: <Heat />, awareness: <Awareness />, about: <About /> }[route] || <Home user={user} />;
  return (
    <>
      <div className="progress" style={{ width: pct + "%" }} />
      <div className="band" />
      <div className="notice">Hackathon prototype (PS01). Synthetic data only. Not an official Rajasthan Police website.</div>
      <div className="helpbar"><span>Cyber Crime Helpline <b>1930</b> · cybercrime.gov.in · Emergency <b>112</b></span><span className="sp" />
        <button onClick={() => setFz(Math.max(13, fz - 1))}>A-</button><button onClick={() => setFz(16)}>A</button><button onClick={() => setFz(Math.min(20, fz + 1))}>A+</button></div>
      <header className="site">
        <a className="brand" href="#/"><BrandMark /><span><b>SUDARSHAN</b><small>राजस्थान साइबर सुरक्षा · Cyber Fraud Intelligence Desk</small></span></a>
        <div className="userchip"><span><b>{user.name}</b><small>{user.role === "officer" ? `Officer ${user.officerId} · ${user.district}` : "Citizen"}</small></span><button className="btn sm alt" onClick={() => { logout(); setUser(null); location.hash = "#/"; }}>Log out</button></div>
      </header>
      <div className="ticker"><div className="tk">{[...NEWS, ...NEWS].map((n, i) => <span key={i}>◆ {n}</span>)}</div></div>
      <div className="shell">
        <aside className="rail"><h6>Citizen & Officer Services</h6>{NAV.map(([r, i, n]) => <a key={r} href={`#/${r}`} className={active === r ? "on" : ""}><span>{i}</span>{n}</a>)}
          <div className="railhelp"><b>1930</b><small>Cyber Crime Helpline</small></div></aside>
        <main>{page}</main>
      </div>
      <footer className="site">SUDARSHAN · Rajasthan Police Cyber Security Hackathon 2026 · PS01 · Static analysis only: no sandbox, no takedown, no private data.</footer>
      <button className="totop" onClick={() => scrollTo({ top: 0, behavior: "smooth" })} aria-label="Back to top">↑</button>
      <Assistant open={open} setOpen={setOpen} caseId={aiCase} />
    </>
  );
}
