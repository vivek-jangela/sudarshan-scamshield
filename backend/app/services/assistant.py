"""Investigation assistant for POST /api/assistant.
Step 1 (agent tools): gather evidence from the case database - the open case, its links, repeat content, identifiers named in
the question, heat-list, statistics. Step 2: if ANTHROPIC_API_KEY is set, an LLM writes the answer from ONLY that evidence and
cites case numbers; otherwise a rule-based writer answers from the same evidence, so the feature always works offline."""
import re
import json
import requests
from .. import config, db
from . import core, similarity


def gather(question, case_id=None):
    ev = {"case": None, "links": None, "similar": [], "mentioned": [], "heat": None, "stats": None, "recent_high": []}
    q = question.lower()
    if case_id:
        c = db.get_case(case_id)
        if c:
            ev["case"] = c
            ev["links"] = db.links(case_id)
            ev["similar"] = similarity.similar_cases(case_id)
    for k, vals in core.url_features.extract_identifiers(question).items():
        t = {"urls": "domain", "phones": "phone", "upi_ids": "upi", "emails": "email"}.get(k)
        for v in (vals if t else []):
            v = (re.sub(r"^https?://|^www\.", "", v).split("/")[0]) if t == "domain" else v
            hits = db.cases_by_identifier(t, v.lower() if t != "phone" else v)
            if hits:
                ev["mentioned"].append({"type": t, "value": v, "cases": hits})
    if re.search(r"heat|top|most|frequent|trend|repeat", q):
        ev["heat"] = db.heatlist(limit=10)
    if re.search(r"how many|total|count|stat|summary|overview", q):
        ev["stats"] = db.stats()
    if not (ev["case"] or ev["mentioned"] or ev["heat"] or ev["stats"]):
        ev["recent_high"] = [r for r in db.list_cases(level="High", limit=5)]
        ev["stats"] = db.stats()
    return ev


def _sources(ev):
    s = []
    if ev["case"]:
        s.append(f"case #{ev['case']['id']}")
    s += [f"case #{n['id']}" for n in (ev["links"] or {}).get("linked_cases", [])[:5]]
    s += [f"case #{n['id']}" for n in ev["similar"][:3]]
    for m in ev["mentioned"]:
        s += [f"case #{c['id']}" for c in m["cases"][:3]]
    s += [f"case #{r['id']}" for r in ev["recent_high"][:3]]
    out = []
    for x in s:
        if x not in out:
            out.append(x)
    return out


def _rule_answer(question, ev):
    parts = []
    c = ev["case"]
    if c:
        top = [i for i in c["indicators"] if i["weight"] > 0][:4]
        parts.append(f"Case #{c['id']} is rated {c['level']} risk ({round(c['score'] * 100)}%), classified as {c['verdict'].replace('_', ' ')}.")
        if top:
            parts.append("Main reasons: " + "; ".join(f"{i['explanation']} (evidence: {i['evidence']})" for i in top) + ".")
        lk = (ev["links"] or {}).get("linked_cases", [])
        if lk:
            via = {(e["shared_type"], e["shared_value"]) for e in ev["links"]["edges"]}
            parts.append("It is linked to " + ", ".join(f"#{n['id']}" for n in lk[:5]) + " through shared " + ", ".join(f"{t} {v}" for t, v in list(via)[:3]) + ", which suggests one operator or campaign.")
        if ev["similar"]:
            parts.append("Near-identical content appears in " + ", ".join(f"#{s['id']} ({s['similarity']})" for s in ev["similar"][:3]) + ", a repeat campaign.")
        parts.append("Recommended action: " + c["advice"])
    for m in ev["mentioned"]:
        parts.append(f"The {m['type']} {m['value']} appears in " + ", ".join(f"#{x['id']} ({x['level']})" for x in m["cases"][:5]) + ".")
    if ev["heat"]:
        parts.append("Most reported identifiers: " + "; ".join(f"{h['type']} {h['value']} ({h['reports']})" for h in ev["heat"][:6]) + ".")
    if ev["stats"]:
        s = ev["stats"]
        parts.append(f"The register holds {s['total']} cases: {s['high']} High, {s['medium']} Medium, {s['low']} Low.")
    if ev["recent_high"]:
        parts.append("Latest High-risk cases: " + ", ".join(f"#{r['id']} {r['title']}" for r in ev["recent_high"]) + ".")
    return " ".join(parts) or "I could not find matching records. Open a case or name a phone, UPI ID or domain."


SYSTEM = ("You are the investigation assistant of ScamShield, a cyber-fraud analysis desk for Rajasthan Police. "
          "Answer ONLY from the EVIDENCE JSON. Cite case numbers like #12. If the evidence does not contain the answer, say so. "
          "Never invent phone numbers, accounts or cases. Be concise (under 150 words), plain English, practical next steps for an officer or citizen.")


def _llm_answer(question, ev):
    ev_small = json.dumps(ev, default=str, ensure_ascii=False)[:14000]
    r = requests.post("https://api.anthropic.com/v1/messages", timeout=40,
                      headers={"x-api-key": config.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                      json={"model": config.ASSISTANT_MODEL, "max_tokens": 600, "system": SYSTEM,
                            "messages": [{"role": "user", "content": f"EVIDENCE:\n{ev_small}\n\nQUESTION: {question}"}]})
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json().get("content", [])).strip()


def answer(question, case_id=None):
    question = (question or "").strip()
    if not question:
        raise ValueError("Please type a question.")
    ev = gather(question[:1000], case_id)
    text, mode = None, "rules"
    if config.ANTHROPIC_API_KEY:
        try:
            text, mode = _llm_answer(question, ev), "llm"
        except Exception:
            text = None  # fall back silently to the rule-based writer
    if not text:
        text = _rule_answer(question, ev)
    return {"answer": text, "sources": _sources(ev), "mode": mode}
