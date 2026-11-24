"""End-to-end check of the whole analysis stack WITHOUT starting the web server (uses a temporary database).
Run from backend/:   python scripts/selftest.py"""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
tmp = tempfile.mkdtemp()
os.environ["SCAMSHIELD_DB"] = os.path.join(tmp, "test.db")
os.environ["DEEP_CHECKS"] = "0"; os.environ["FETCH_WEBSITES"] = "0"
from app import db
from app.services import analysis as A, similarity, reports, assistant

db.init()
ok = fail = 0
def check(name, cond, extra=""):
    global ok, fail
    cond = bool(cond); ok += cond; fail += (not cond)
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))

m = A.analyze_message("Dear SBI customer, your KYC is blocked. Update now http://sbi-kyc.top/login or call 9812345670", "citizen", "sms")
check("phishing SMS -> High", m["level"] == "High", f"{m['level']} {m['score']} {m['verdict']}")
check("indicators are objects with evidence", all({"explanation", "category", "source", "weight", "evidence"} <= set(i) for i in m["indicators"]))
check("identifiers extracted (domain, phone)", "domain" in m["identifiers"] and "phone" in m["identifiers"], str(m["identifiers"]))
g = A.analyze_message("482913 is your one time password for HDFC Bank NetBanking. Never share it with anyone.")
check("genuine OTP SMS -> Low", g["level"] == "Low", f"{g['level']} {g['score']}")
hi = A.analyze_message("Hello, I am from CBI. Digital arrest warrant on your Aadhaar. Pay Rs 25000 security deposit on UPI scam.fraud@ybl or be arrested immediately")
check("digital-arrest style -> High", hi["level"] == "High", f"{hi['level']} {hi['verdict']}")

u = A.analyze_url("http://indiapost-redeliver.xyz/pay")
check("fake parcel URL -> High", u["level"] == "High", f"{u['level']} {u['score']}")
ok_url = A.analyze_url("https://www.amazon.in/")
check("official domain -> Low", ok_url["level"] == "Low")
chk = A.check_link("http://sbi-kyc-update.top/login")
check("precheck returns level/reasons/case_id", chk["level"] == "High" and chk["reasons"] and chk["case_id"], str(chk["level"]))

html = """<html><title>Double Profit Club</title><body><h1>Guaranteed returns 5% daily profit!</h1><p>Refer and earn level income, binary plan.
Minimum deposit Rs 1000. Pay to UPI profitclub@ybl or call 9812345670. Limited slots, register now.</p>
<form><input type=password name=pw><input name=otp placeholder="OTP"></form></body></html>"""
w = A.analyze_website(html=html, url="http://profit-club.top")
check("Ponzi/MLM page -> High", w["level"] == "High", f"{w['level']} {w['verdict']}")
check("website identifiers include upi + phone", "upi" in w["identifiers"] and "phone" in w["identifiers"])

for name, expect in (("test_loan.apk", "High"), ("test_calc.apk", "Low"), ("test_bet.apk", "Medium")):
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples", name)
    r = A.analyze_apk_file(p, name)
    check(f"{name} -> {expect}", r["level"] == expect, f"{r['level']} {r['score']} {r['verdict']}")
try:
    A.analyze_apk_file(__file__, "x.apk"); check("non-APK rejected", False)
except A.AnalysisError:
    check("non-APK rejected", True)
s = A.analyze_store_link("https://play.google.com/store/apps/details?id=com.fastcash.instantloan")
check("store link with loan package -> flagged", s["level"] != "Low", f"{s['level']} {s['verdict']}")

# linking: phone 9812345670 is shared by m, w (and the digital-arrest case does not share it)
lk = db.links(m["case_id"])
check("cases linked via shared phone/domain", any(n["id"] == w["case_id"] for n in lk["linked_cases"]), str(lk["edges"][:2]))
heat = db.heatlist()
check("heat-list has repeated identifier", any(h["value"] == "9812345670" and h["reports"] >= 2 for h in heat), str(heat[:3]))
check("graph clusters present", len(db.graph()) >= 1)
m2 = A.analyze_message("URGENT SBI KYC pending, account blocked today. Call 9812345670 now")
check("blacklist bonus applied on reused phone", any(i["source"] == "heat_list" for i in m2["indicators"]))
m3 = A.analyze_message("Dear SBI customer, your KYC is blocked. Update now http://sbi-kyc.top/login or call 9876501234")
sim = similarity.similar_cases(m3["case_id"])
check("repeat-content detection", any(x["id"] == m["case_id"] for x in sim), str(sim[:2]))
check("PDF report builds", reports.case_pdf(db.get_case(m["case_id"]))[:4] == b"%PDF")
check("HTML report builds", "Case #" in reports.case_html(db.get_case(m["case_id"])))
ans = assistant.answer("Why is this High risk and is it linked to other cases?", m["case_id"])
check("assistant answers with sources", ans["answer"] and ans["sources"], ans["answer"][:90])
check("list/search works", len(db.list_cases(q="9812345670")) >= 2 and len(db.list_cases(level="high")) >= 3)
try:
    A.analyze_message("  "); check("empty input rejected", False)
except A.AnalysisError:
    check("empty input rejected", True)
print(f"\n{ok} passed, {fail} failed"); sys.exit(1 if fail else 0)
