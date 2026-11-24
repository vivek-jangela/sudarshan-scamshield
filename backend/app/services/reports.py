"""Downloadable case report (PDF and printable HTML) with indicators, identifiers, linked cases and the evidence hash."""
import io
from html import escape as h
from xml.sax.saxutils import escape as x
from .. import db

NOTE = ("Automated assessment generated for investigation support. Verify independently before any action. "
        "Static analysis only: no live malware execution, no private data accessed.")
COL = {"High": "#c0392b", "Medium": "#d68910", "Low": "#1e8449"}


def _links(cid):
    return db.links(cid)


def case_html(c):
    lk = _links(c["id"])
    ind = "".join(f"<tr><td>{h(i['explanation'])}</td><td>{h(i['category'].replace('_', ' '))}</td><td>{h(i['source'])}</td>"
                  f"<td>{i['weight']}</td><td><code>{h(str(i['evidence']))}</code></td></tr>" for i in c["indicators"])
    ids = "".join(f"<tr><th>{h(t)}</th><td>{h(', '.join(v))}</td></tr>" for t, v in c["identifiers"].items())
    info = "".join(f"<tr><th>{h(str(k).replace('_', ' '))}</th><td>{h(str(v))}</td></tr>" for k, v in c["info"].items())
    lc = "".join(f"<tr><td>#{n['id']}</td><td>{h(n['title'] or '')}</td><td>{h(n['level'])}</td></tr>" for n in lk["linked_cases"])
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Case #{c['id']} report</title>
<style>body{{font-family:Arial,sans-serif;max-width:900px;margin:24px auto;padding:0 16px;color:#1b1f24}}
h1{{color:#0b2a5b}}table{{width:100%;border-collapse:collapse;font-size:14px;margin:8px 0 18px}}td,th{{border:1px solid #ccd;padding:6px;text-align:left;vertical-align:top}}
.lv{{display:inline-block;color:#fff;background:{COL[c['level']]};padding:4px 12px;border-radius:4px;font-weight:700}}pre{{white-space:pre-wrap;background:#f4f6f9;padding:10px;border:1px solid #dde}}
small{{color:#555}}@media print{{a{{display:none}}}}</style></head><body>
<h1>SUDARSHAN investigation report: Case #{c['id']}</h1>
<p><span class="lv">{h(c['level'].upper())} RISK</span> &nbsp; score {round(c['score']*100)}/100 &nbsp; classification: <b>{h(c['verdict'].replace('_', ' '))}</b></p>
<p><small>Type {h(c['kind'])} | channel {h(c['channel'] or '-')} | source {h(c['source'] or '-')} | reporter {h(c['reporter'] or '-')} | logged {h(c['created_at'])} UTC</small></p>
<p><b>Advice:</b> {h(c['advice'])}</p>
<h3>Why this result</h3><table><tr><th>Indicator</th><th>Category</th><th>Source</th><th>Weight</th><th>Evidence</th></tr>{ind or '<tr><td colspan=5>None</td></tr>'}</table>
<h3>Extracted identifiers</h3><table>{ids or '<tr><td>None found</td></tr>'}</table>
<h3>Technical details</h3><table>{info or '<tr><td>None</td></tr>'}</table>
<h3>Linked cases (shared identifiers)</h3><table>{lc or '<tr><td>None found</td></tr>'}</table>
<h3>Evidence snapshot</h3><pre>{h((c['content'] or '')[:3000])}</pre><p><small>SHA-256: {h(c['evidence_sha256'] or '')}</small></p>
<p><small>{NOTE}</small></p></body></html>"""


def case_pdf(c):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title=f"SUDARSHAN Case {c['id']}", leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    st = getSampleStyleSheet()
    P = lambda t, s="BodyText": Paragraph(x(str(t)).replace("\n", "<br/>"), st[s])
    cell = lambda t: Paragraph(x(str(t)), st["BodyText"])
    el = [P(f"SUDARSHAN - Investigation Report - Case #{c['id']}", "Title"),
          P(f"Type: {c['kind']} | Channel: {c['channel'] or '-'} | Source: {c['source'] or '-'} | Reporter: {c['reporter'] or '-'} | Logged: {c['created_at']} UTC"), Spacer(1, 8)]
    t = Table([[f"RISK: {c['level'].upper()}", f"Score {round(c['score'] * 100)}/100", f"Class: {c['verdict'].replace('_', ' ')}"]], colWidths=[130, 110, 270])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, 0), colors.HexColor(COL[c["level"]])), ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
                           ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"), ("BOX", (0, 0), (-1, -1), .5, colors.grey)]))
    el += [t, Spacer(1, 8), P(f"Advice: {c['advice']}"), Spacer(1, 8), P("Why this result (triggered indicators)", "Heading3")]
    rows = [["Indicator", "Source", "Wt", "Evidence"]] + [[cell(i["explanation"]), cell(i["source"]), str(i["weight"]), cell(i["evidence"])] for i in c["indicators"]]
    tab = Table(rows, colWidths=[230, 80, 25, 175], repeatRows=1)
    tab.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .3, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 8), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                             ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf5"))]))
    el.append(tab)
    if c["identifiers"]:
        el += [Spacer(1, 8), P("Extracted identifiers", "Heading3")]
        tab = Table([[k, cell(", ".join(v)[:300])] for k, v in c["identifiers"].items()], colWidths=[90, 420])
        tab.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .3, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 8), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        el.append(tab)
    if c["info"]:
        el += [Spacer(1, 8), P("Technical details", "Heading3")]
        tab = Table([[str(k).replace("_", " "), cell(str(v)[:300])] for k, v in c["info"].items()], colWidths=[120, 390])
        tab.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .3, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 8), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        el.append(tab)
    lk = _links(c["id"])
    if lk["linked_cases"]:
        el += [Spacer(1, 8), P("Linked cases (shared identifiers)", "Heading3")]
        for n in lk["linked_cases"]:
            via = ", ".join(f"{e['shared_type']}: {e['shared_value']}" for e in lk["edges"] if e["case_id"] == n["id"])
            el.append(P(f"#{n['id']} [{n['level']}] {n['title']} - via {via}"))
    el += [Spacer(1, 8), P("Evidence snapshot", "Heading3"), P((c["content"] or "")[:1500]), P(f"SHA-256: {c['evidence_sha256']}", "Code"),
           Spacer(1, 12), P(NOTE, "Italic")]
    doc.build(el)
    return buf.getvalue()
