"""Adapter between the SATARK NETRA engine and the ScamShield UI.

Every analyze_* function: runs the engine -> converts its output to the UI shape (Low/Medium/High, 0-1 score, verdict,
advice, indicator objects, normalised identifiers) -> applies the heat-list blacklist -> stores a case -> returns it.
No FastAPI import here, so this module can be tested on its own (scripts/selftest.py)."""
import re
import json
import socket
import hashlib
from urllib.parse import urlparse, parse_qs
from .. import config, db
from . import core, fetcher


class AnalysisError(ValueError):
    """User-facing problem (bad input, unreadable file). The API turns it into HTTP 400."""


THRESH = (25, 50)  # LOW < 25, MEDIUM 25-49, HIGH >= 50 (same cut-offs as the engine)


def _level(score):
    return "High" if score >= THRESH[1] else "Medium" if score >= THRESH[0] else "Low"


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s or "").lower()).strip("_") or "unknown"


# ------------------------------------------------------------------ advice
BASE_ADVICE = {
    "High": "Do not click, reply, install or pay. Never share OTP, PIN or CVV. If money is already lost, call 1930 at once "
            "and report on cybercrime.gov.in.",
    "Medium": "Do not act on this yet. Verify through the official website or app, or the number printed on your card or bill. "
              "If unsure, report it.",
    "Low": "No strong scam signals were found, but stay careful. Never share OTP, PIN or CVV with anyone.",
}
EXTRA_ADVICE = [
    ("loan", "Loan apps must be tied to an RBI-regulated lender. Do not allow SMS, contacts or photo permissions to a loan app."),
    ("invest|ponzi|mlm|betting|crypto", "Check registration on sebi.gov.in before investing. Guaranteed or daily returns are a red flag."),
    ("identity|arrest", "No agency arrests or interrogates anyone over a video call. Hang up and call 1930."),
    ("phishing|kyc", "Banks do not ask for KYC through links. Open your bank's official app or website yourself."),
    ("job", "Genuine employers never ask you to pay to earn. Leave the Telegram or WhatsApp group."),
    ("tech_support", "Never install AnyDesk, TeamViewer or QuickSupport at a stranger's request."),
    ("refund|reward", "Refunds and prizes never require you to share an OTP or pay a fee first."),
]


def advice_for(level, verdict):
    extra = next((t for k, t in EXTRA_ADVICE if re.search(k, verdict or "")), "")
    return (BASE_ADVICE[level] + (" " + extra if extra and level != "Low" else "")).strip()


# ------------------------------------------------------------------ indicators
_W = re.compile(r"\s*\(\+(\d+)\)\s*$")
_CATS = [
    (r"otp|\bpin\b|cvv|password|card number|aadhaar|upi pin", "credential_harvesting"),
    (r"kyc|account-verification", "fake_kyc"),
    (r"police|cbi|customs|court|arrest|trai", "impersonation"),
    (r"leak|contacts ko", "blackmail_harassment"),
    (r"fee|deposit|charge|payment|upi id|wallet", "payment_request"),
    (r"guarantee|returns|double|profit", "unrealistic_returns"),
    (r"referral|mlm|downline", "mlm_referral"),
    (r"bet|casino|gambl", "illegal_betting"),
    (r"urgen|block|suspend|disconnect|expire|pressure", "urgency"),
    (r"prize|lottery|winner", "reward_lure"),
    (r"earning|work from home|job", "job_lure"),
    (r"whatsapp|telegram", "off_platform_contact"),
    (r"install|anydesk|apk|teamviewer|remote-access", "malicious_app"),
]


def _cat(text):
    t = text.lower()
    if t.startswith(("permission", "risky combination")):
        return "dangerous_permission"
    if t.startswith(("suspicious link", "questionable link")) or re.search(
            r"tld|https|domain|shortener|ip address|punycode|look-alike|impersonates brand|hyphen|subdomain|hostname|random-looking|'@'|substitution", t):
        return "domain_risk"
    if t.startswith("classifier"):
        return "text_classification"
    if t.startswith(("matches known", "identifier")):
        return "blacklist"
    for rx, c in _CATS:
        if re.search(rx, t):
            return c
    return "suspicious_content"


def _msg_rule_map():
    return {n: rx for n, rx in core.engine.MSG_RULES}


def _evidence(kind, text, name, ctx):
    t = text.lower()
    if t.startswith("classifier"):
        return (ctx.get("text") or "")[:90]
    if kind == "message":
        rx = _msg_rule_map().get(name)
        if rx and ctx.get("text"):
            m = re.search(rx, ctx["text"], flags=re.I | re.S)
            if m:
                return m.group(0).strip()[:90]
        m = re.match(r"(?:suspicious|questionable) link (\S+?):", text, flags=re.I)
        if m:
            return m.group(1)
    if kind == "website" and ": " in text:
        tail = text.split(": ", 1)[1]
        if tail and not tail.startswith("Domain"):
            return tail[:120]
    if kind == "apk":
        return "AndroidManifest.xml" if text.lower().startswith(("permission", "risky")) else "package " + (ctx.get("package") or "")
    return ctx.get("host") or (ctx.get("text") or "")[:90] or "-"


def adapt_indicators(kind, raw, ctx):
    out, seen = [], set()
    for s in raw or []:
        m = _W.search(s)
        weight = int(m.group(1)) if m else 0
        body = _W.sub("", s).strip()
        if not m and body.lower().startswith("no "):
            continue  # placeholder like "No scam indicators found"
        name = body.split(": ", 1)[0] if kind in ("website",) or (kind == "message" and body in _msg_rule_map()) else body
        explanation = name if (kind == "website" and m) else body
        key = (explanation, weight)
        if key in seen:
            continue
        seen.add(key)
        category = "trusted_domain" if body.lower().startswith(("official domain", "government")) else _cat(body)
        out.append({"explanation": explanation[:300], "category": category,
                    "source": "ml_text_classifier" if body.lower().startswith("classifier") else
                    "apk_static" if kind == "apk" else "website_content" if kind == "website" else
                    "url_rules" if kind == "url" else "message_rules",
                    "weight": weight, "evidence": _evidence(kind, body, name, ctx)})
    return out


# ------------------------------------------------------------------ identifiers
def _host(u):
    try:
        h = urlparse(u if "://" in u else "http://" + u).hostname or ""
    except ValueError:
        return ""
    return h.lower().removeprefix("www.")


def normalize_ids(raw, safe_hosts=(), extra=None):
    """Engine identifier keys -> UI/heat-list types. Hosts that scored 0 are not stored as 'domain' (no false links)."""
    out = {}

    def put(t, v):
        v = str(v).strip()
        if v and v not in out.setdefault(t, []) and len(out[t]) < 25:
            out[t].append(v)
    for u in raw.get("urls", []):
        put("url", u[:300])
        h = _host(u)
        if h and h not in safe_hosts:
            put("domain", h)
    for k, t, f in (("phones", "phone", str), ("upi_ids", "upi", str.lower), ("ifsc", "ifsc", str.upper),
                    ("bank_accounts", "bank_account", str), ("emails", "email", str.lower), ("ip_addresses", "ip", str)):
        for v in raw.get(k, []):
            put(t, f(v))
    for k in ("btc", "eth", "trx"):
        for v in raw.get(k, []):
            put("crypto", v)
    for t, vals in (extra or {}).items():
        for v in vals:
            put(t, v)
    return {k: v for k, v in out.items() if v}


# ------------------------------------------------------------------ live URL intelligence
_LIVE_POINTS = {"Very recently registered domain": 20, "Multiple redirects detected": 15,
                "Invalid SSL certificate": 20, "Flagged by multiple security engines": 35}


def live_checks(url):
    """Domain age (RDAP), redirect chain, HTTPS/SSL, resolved IP. Needs internet; fails soft when offline."""
    host = _host(url)
    info, inds = {}, []
    if not config.DEEP_CHECKS or not host:
        return info, inds
    try:
        intel = core.url_intelligence.analyze_url_intelligence(url)
    except Exception as e:  # network library problems must never break an analysis
        return {"live_checks": f"unavailable ({type(e).__name__})"}, inds
    age = intel.get("domain_age", {}) or {}
    if age.get("status") == "Success":
        info["domain_age_days"] = age.get("domain_age_days")
        info["domain_created"] = str(age.get("creation_date", ""))[:10]
    else:
        info["domain_age"] = age.get("status", "not checked")
    red = intel.get("redirect_analysis", {}) or {}
    if red.get("status") == "Completed":
        info["redirect_count"] = red.get("redirect_count", 0)
        info["final_url"] = red.get("final_url")
        chain = [c.get("url") for c in red.get("redirect_chain", [])]
        if len(chain) > 1:
            info["redirect_chain"] = chain
    else:
        info["redirects"] = red.get("status", "not checked")
    https = intel.get("https_analysis", {}) or {}
    info["https_enabled"] = https.get("https_enabled")
    if https.get("ssl_certificate_valid") is not None:
        info["ssl_certificate_valid"] = https.get("ssl_certificate_valid")
    try:
        if core.url_intelligence.is_public_domain(host):
            ip = socket.gethostbyname(host)
            info["resolved_ip"] = ip
            try:
                info["reverse_dns"] = socket.gethostbyaddr(ip)[0]
            except OSError:
                pass
    except OSError:
        pass
    risk = core.url_intelligence.calculate_intelligence_risk(intel)
    for text in risk.get("indicators", []):
        inds.append({"explanation": text + " (live check)", "category": "domain_risk" if "domain" in text.lower() else "transport_security",
                     "source": "live_intelligence", "weight": _LIVE_POINTS.get(text, 10), "evidence": host})
    return info, inds


# ------------------------------------------------------------------ common finishing step
def _finish(kind, *, indicators, base_score, ids, info, title, content, verdict, channel=None, source="web", reporter="citizen"):
    reporter = reporter if reporter in ("citizen", "officer") else "citizen"
    inds = list(indicators)
    score = base_score + sum(i["weight"] for i in inds if i["source"] == "live_intelligence")
    # heat-list blacklist: identifiers already seen in flagged cases push the score up
    prior = db.prior_reports(ids)
    hot = [(t, v, n) for t, v, n in prior if n >= config.BLACKLIST_MIN_REPORTS]
    if hot:
        inds.append({"explanation": "Identifier(s) already on the heat-list: " + "; ".join(f"{t} {v} ({n} reports)" for t, v, n in hot[:4]),
                     "category": "blacklist", "source": "heat_list", "weight": 20, "evidence": ", ".join(v for _, v, _ in hot[:4])})
        score += 20
    elif prior:
        t, v, n = prior[0]
        inds.append({"explanation": f"Identifier seen in {n} earlier flagged case(s): {t} {v}", "category": "blacklist",
                     "source": "heat_list", "weight": 0, "evidence": v})
    score = max(0, min(100, int(score)))
    level = _level(score)
    verdict = _slug(verdict)
    if level != "Low" and verdict in ("genuine", "no_scam_pattern", "app_low_risk", "store_listing_no_signals"):
        verdict = "suspicious_content"
    inds.sort(key=lambda i: -i["weight"])
    rec = {"kind": kind, "channel": channel, "source": source, "reporter": reporter,
           "title": (title or "")[:120], "verdict": verdict, "level": level, "score": round(score / 100, 3),
           "advice": advice_for(level, verdict), "content": content,
           "evidence_sha256": hashlib.sha256((kind + "\n" + content).encode("utf-8", "replace")).hexdigest(),
           "indicators": inds, "info": info, "identifiers": ids}
    cid = db.add_case(rec)
    return db.get_case(cid)


def _clean(text, what):
    text = (text or "").strip()
    if len(text) < 3:
        raise AnalysisError(f"Please enter the {what}.")
    if len(text) > config.MAX_TEXT_CHARS:
        raise AnalysisError(f"The {what} is too long (limit {config.MAX_TEXT_CHARS} characters).")
    return text


# ------------------------------------------------------------------ 1. message
def analyze_message(text, reporter="citizen", channel="sms"):
    text = _clean(text, "message text")
    res = core.engine.analyze("message", text)
    safe = {r["host"] for r in res.get("url_results", []) if r["score"] == 0}
    ids = normalize_ids(res.get("identifiers", {}), safe)
    inds = adapt_indicators("message", res["indicators"], {"text": text})
    info = {"model": "TF-IDF + logistic regression (10 classes, EN/Hinglish/Hindi)", "model_confidence": f"{res['confidence']:.0%}",
            "links_checked": ", ".join(r["host"] for r in res.get("url_results", [])) or "none"}
    return _finish("message", indicators=inds, base_score=res["score"], ids=ids, info=info,
                   title=re.sub(r"\s+", " ", text)[:70], content=text, verdict=res["category"],
                   channel=channel if channel in ("sms", "whatsapp", "email", "social") else "sms", reporter=reporter)


# ------------------------------------------------------------------ 2. url
def _clean_url(url):
    url = _clean(url, "link")
    if re.search(r"\s", url) or len(url) > 2048:
        raise AnalysisError("That does not look like a single valid link.")
    if not _host(url) or "." not in _host(url):
        raise AnalysisError("That does not look like a valid web address.")
    return url


def analyze_url(url, reporter="citizen", deep=None, source="web"):
    url = _clean_url(url)
    res = core.engine.analyze_url_item(url, False)
    trusted = any(i.lower().startswith(("official domain", "government")) for i in res["indicators"])
    deep = config.DEEP_CHECKS if deep is None else deep
    info = {"host": res["host"]}
    live_inds = []
    if deep and not trusted:
        li, live_inds = live_checks(url)
        info.update(li)
    ids = normalize_ids({"urls": [url]}, safe_hosts={res["host"]} if res["score"] == 0 else ())
    inds = adapt_indicators("url", res["indicators"], {"host": res["host"]}) + live_inds
    return _finish("url", indicators=inds, base_score=res["score"], ids=ids, info=info, title=res["host"],
                   content=url, verdict=res["category"], source=source, reporter=reporter)


def check_link(url, reporter="citizen"):
    """Fast warn-before-open check (no live network lookups) for the link-safety page, browser extension and bot."""
    c = analyze_url(url, reporter, deep=False, source="precheck")
    return {"level": c["level"], "score": c["score"], "reasons": [i["explanation"] for i in c["indicators"] if i["weight"] > 0][:6]
            or [i["explanation"] for i in c["indicators"]][:3], "advice": c["advice"], "case_id": c["case_id"], "warn": c["level"] != "Low"}


# ------------------------------------------------------------------ 3. website
def analyze_website(html=None, url=None, reporter="citizen"):
    info, live_inds, note = {}, [], None
    source = "paste" if (html and html.strip()) else "url"
    if html and html.strip():
        if len(html.encode("utf-8", "ignore")) > config.MAX_HTML_BYTES:
            raise AnalysisError("The page source is too large.")
        page_url = _clean_url(url) if url else None
    elif url:
        page_url = _clean_url(url)
        html = ""
        if config.FETCH_WEBSITES:
            try:
                got = fetcher.fetch_page(page_url)
                html = got["html"]; info["page_fetched"] = "yes"; info["final_url"] = got["final_url"]
            except fetcher.FetchError as e:
                note = str(e); info["page_fetched"] = "no: " + note
        else:
            info["page_fetched"] = "disabled (FETCH_WEBSITES=0)"
        if not html:  # could not read the page: still assess the address so the officer gets something useful
            return _finish_url_only(page_url, reporter, info)
    else:
        raise AnalysisError("Give a website address or paste the page HTML.")
    res = core.engine.analyze("website", html=html, url=page_url)
    host = _host(page_url) if page_url else ""
    urlres = core.url_features.analyze_url(page_url) if page_url else None
    safe = {host} if urlres and urlres["score"] == 0 else ()
    ids = normalize_ids(res.get("identifiers", {}), safe, extra={"url": [page_url]} if page_url else None)
    if host and host not in safe:
        ids.setdefault("domain", []).append(host)
    if page_url and config.DEEP_CHECKS and urlres and urlres["score"] > 0:
        li, live_inds = live_checks(page_url); info.update(li)
    info["page_title"] = res.get("title") or "-"
    text = core.website_analyzer.page_text(html)[1]
    inds = adapt_indicators("website", res["indicators"], {"text": text}) + live_inds
    return _finish("website", indicators=inds, base_score=res["score"], ids=ids, info=info,
                   title=res.get("title") or host or "Pasted web page", content=((page_url or "") + "\n" + text[:3000]).strip(),
                   verdict=res["category"], source=source, reporter=reporter)


def _finish_url_only(url, reporter, info):
    res = core.engine.analyze_url_item(url, False)
    ids = normalize_ids({"urls": [url]}, safe_hosts={res["host"]} if res["score"] == 0 else ())
    live_inds = []
    if config.DEEP_CHECKS and res["score"] > 0:
        li, live_inds = live_checks(url); info.update(li)
    inds = adapt_indicators("url", res["indicators"], {"host": res["host"]}) + live_inds
    verdict = res["category"]
    return _finish("website", indicators=inds, base_score=res["score"], ids=ids, info=info, title=res["host"],
                   content=url, verdict=verdict, source="url", reporter=reporter)


# ------------------------------------------------------------------ 4. apk upload
def analyze_apk_file(path, filename, reporter="officer"):
    try:
        res = core.engine.analyze("apk", path=path)
    except Exception as e:
        raise AnalysisError(f"Could not read this file as an APK ({type(e).__name__}: {e}).")
    ids = normalize_ids(res.get("identifiers", {}), extra={"package": [res["package"]] if res.get("package") else [],
                                                        "cert": [res["cert_sha256"]] if res.get("cert_sha256") else []})
    ctx = {"package": res.get("package")}
    inds = adapt_indicators("apk", res["indicators"], ctx)
    info = {"package": res.get("package"), "app_name": res.get("app_label") or "-", "version": res.get("version") or "-",
            "permissions": ", ".join(res.get("permissions", [])) or "none", "signing_cert_sha256": res.get("cert_sha256") or "none",
            "apk_sha256": res.get("sha256"), "known_suspicious_app_match": (res.get("known_match") or {}).get("name", "no match"),
            "analysis": "static only (manifest, permissions, strings); the app is never run"}
    sha = res["sha256"]
    return _finish("apk", indicators=inds, base_score=res["score"], ids=ids, info=info,
                   title=f"APK: {res.get('app_label') or res.get('package') or filename}"[:120],
                   content=f"{filename}  sha256={sha}", verdict=res["category"], source="upload", reporter=reporter)


# ------------------------------------------------------------------ 5. store link
def analyze_store_link(link, reporter="citizen"):
    link = _clean_url(link)
    p = urlparse(link if "://" in link else "http://" + link)
    pkg = (parse_qs(p.query).get("id") or [""])[0]
    if "play.google.com" not in (p.hostname or "") or not pkg:
        return analyze_url(link, reporter)   # not a Play Store app link: assess the address itself
    info = {"package": pkg, "store": "Google Play", "note": "Permissions are not visible from a store link. Upload the APK for full static analysis."}
    inds, score, title = [], 0, ""
    low = pkg.lower()
    page_text = ""
    try:
        got = fetcher.fetch_page(link, allowed_hosts={"play.google.com"}) if config.FETCH_WEBSITES else None
        if got:
            soup, page_text = core.website_analyzer.page_text(got["html"])
            title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
            info["store_title"] = title or "-"
    except Exception as e:
        info["store_page"] = f"not read ({type(e).__name__})"
    words = low + " " + title.lower()
    lw = [w for w in core.apk_analyzer.LOAN_WORDS if w in words]
    iw = [w for w in core.apk_analyzer.INVEST_WORDS if w in words]
    verdict = "store_listing_no_signals"
    if lw:
        inds.append({"explanation": f"Loan-style app name/package {lw[:3]}", "category": "malicious_app", "source": "store_listing", "weight": 25, "evidence": pkg}); score += 25; verdict = "fake_loan_app"
    if iw:
        inds.append({"explanation": f"Investment/betting-style app name/package {iw[:3]}", "category": "unrealistic_returns", "source": "store_listing", "weight": 25, "evidence": pkg}); score += 25; verdict = "fake_investment_app"
    try:
        known = json.load(open(config.CORE_DIR / "known_bad_apps.json", encoding="utf-8"))
    except (OSError, ValueError):
        known = []
    for k in known:
        if pkg and k.get("package") == pkg:
            inds.append({"explanation": f"Matches known suspicious app '{k.get('name')}'", "category": "blacklist", "source": "known_apps", "weight": 40, "evidence": pkg}); score += 40
            verdict = verdict if verdict != "store_listing_no_signals" else "known_suspicious_app"
            break
    if page_text:
        w = core.website_analyzer.analyze_website("<html><body>" + page_text[:20000] + "</body></html>")
        extra = adapt_indicators("website", w["indicators"], {"text": page_text})
        for i in extra:
            i["source"] = "store_listing"
        inds += extra; score += min(w["score"], 40)
        if w["score"] >= 25 and verdict == "store_listing_no_signals":
            verdict = _slug(w["category"])
    return _finish("apk", indicators=inds, base_score=score, ids=normalize_ids({}, extra={"package": [pkg] if pkg else []}),
                   info=info, title=f"Store link: {title or pkg}"[:120], content=link, verdict=verdict, source="store_link", reporter=reporter)
