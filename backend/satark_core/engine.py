"""SATARK NETRA unified engine: message / url / website / apk -> explainable risk + identifiers."""
import re, joblib, os
from url_features import analyze_url, extract_identifiers
from website_analyzer import analyze_website
from apk_analyzer import analyze_apk
HERE=os.path.dirname(os.path.abspath(__file__))
_MSG=None
CAT_POINTS={"Phishing":40,"Identity Theft Scam":40,"Tech Support Scam":35,"Loan Scam":35,"Investment Scam":35,"Refund Scam":30,
            "Reward Scam":30,"Job Scam":30,"SMS Spam":15,"Genuine":0}
IND_POINTS=8; HEAVY={"Asks you to share OTP / PIN / CVV","Demands an upfront fee / deposit / processing charge","Impersonates police / CBI / customs / court","Threatens to leak photos / contact your contacts"}; HEAVY_POINTS=12; URL_HIGH_POINTS=45; URL_MED_POINTS=20
THRESH=(25,50)   # LOW <25, MEDIUM 25-49, HIGH >=50 (same cut-offs as URL/website/APK analyzers)
MSG_RULES=[("Urgency / threat of blocking or disconnection",r"\b(?:blocked?|suspend(?:ed)?|deactivat\w+|disconnect\w*|kat\s+jayega|band\s+ho\s+jayega|expire[sd]?|within\s+\d+\s+(?:hours?|hrs?)|immediately|turant|tonight)\b|कट\s+जाएगा|बंद\s+हो\s+जाएगा"),
 ("Fake KYC / account-verification request",r"\bkyc\b|pan\s+(?:card\s+)?(?:not\s+linked|update)|aadhaar?\s+(?:suspend|verif|link)|verify\s+(?:your\s+)?(?:account|bank|details)"),
 ("Asks you to share OTP / PIN / CVV",r"(?<!not )(?<!never )(?<!na )(?<!mat )share\s+(?:your\s+|the\s+)?(?:otp|pin|cvv|upi\s*pin)|(?:otp|upi\s*pin)\s+(?:daalein|bhejein|batayein)"),
 ("Demands an upfront fee / deposit / processing charge",r"processing\s+fee|registration\s+fee|redelivery\s+fee|security\s+(?:deposit|amount)|pay\s+rs\.?\s*\d+|fee\s+bhejein|jama\s+karein"),
 ("Prize / lottery claim",r"\b(?:lottery|lucky\s+winner|you\s+have\s+won|jeeti|kbc|scratch\s+card)\b|लॉटरी"),
 ("Unrealistic returns / guaranteed profit",r"guarantee[d]?|double\s+(?:your\s+)?money|paisa\s+double|daily\s+profit|\d+%\s*(?:daily|per\s+day)|गारंटीड"),
 ("Asks to install an app / remote-access tool",r"\banydesk\b|teamviewer|quicksupport|download\s+(?:the\s+|our\s+)?app|install\s+(?:our\s+)?app|\.apk\b"),
 ("Impersonates police / CBI / customs / court",r"\b(?:cbi|customs?\s+officer|police\s+notice|digital\s+arrest|trai\s+notice|narcotics|money\s+laundering|arrest)\b"),
 ("Threatens to leak photos / contact your contacts",r"send\s+your\s+photos|all\s+your\s+contacts|contacts\s+ko\s+bhej"),
 ("Offers earning from home with no skills",r"work\s+from\s+home.*earn|earn\s+(?:rs\.?\s*)?\d+.*(?:daily|per\s+day|roz)|ghar\s+baithe|घर\s+बैठे|part[-\s]*time\s+job"),
 ("Contact via WhatsApp / Telegram for money matters",r"whatsapp\s*(?:karein|now|me)?\s*\+?\d|telegram|t\.me/")]
def _msg():
    global _MSG
    if _MSG is None: _MSG=joblib.load(os.path.join(HERE,"message_model_v3.pkl"))
    return _MSG
def _level(s): return "HIGH" if s>=THRESH[1] else "MEDIUM" if s>=THRESH[0] else "LOW"
def analyze_message(text, deep=False):
    ids=extract_identifiers(text); m=_msg()["model"]
    probs=m.predict_proba([text])[0]; cls=list(m.classes_); k=int(probs.argmax()); cat,conf=cls[k],float(probs[k])
    ind=[]; score=CAT_POINTS.get(cat,20)
    if cat!="Genuine": ind.append(f"Classifier: {cat} ({conf:.0%} confidence) (+{CAT_POINTS.get(cat,20)})")
    hits=[n for n,rx in MSG_RULES if re.search(rx,text,flags=re.I|re.S)]
    for n in hits:
        p=HEAVY_POINTS if n in HEAVY else IND_POINTS; score+=p; ind.append(n+f" (+{p})")
    url_results=[]
    for u in ids.get("urls",[]):
        if re.fullmatch(r"[\w.-]+\.(?:com|in)",u) and "@" in text and u in text.split("@")[-1]: continue  # email domain
        r=analyze_url(u); url_results.append(r)
        if r["level"]=="HIGH": score+=URL_HIGH_POINTS; ind.append(f"Suspicious link {r['host']}: "+"; ".join(r["indicators"][:3])+f" (+{URL_HIGH_POINTS})")
        elif r["level"]=="MEDIUM": score+=URL_MED_POINTS; ind.append(f"Questionable link {r['host']}: "+"; ".join(r["indicators"][:2])+f" (+{URL_MED_POINTS})")
    if cat=="Genuine" and not any(r["level"]!="LOW" for r in url_results): score=min(score,20)
    score=min(score,100)
    return {"type":"message","category":cat,"confidence":round(conf,3),"score":score,"level":_level(score),
            "indicators":ind or ["No scam indicators found"],"identifiers":ids,"url_results":url_results}
def analyze_url_item(url, deep=False):
    r=analyze_url(url); res={"type":"url","category":"Malicious URL" if r["level"]=="HIGH" else "Suspicious URL" if r["level"]=="MEDIUM" else "No scam pattern",
        "score":r["score"],"level":r["level"],"indicators":list(r["indicators"]),"identifiers":{"urls":[url]},"host":r["host"]}
    if deep:
        try:
            import url_intelligence as ui
            intel=ui.analyze_url_intelligence(url); ir=ui.calculate_intelligence_risk(intel)
            res["intelligence"]=intel
            if ir["intelligence_risk_score"]:
                res["score"]=min(100,res["score"]+ir["intelligence_risk_score"]); res["indicators"]+= [i+" (live check)" for i in ir["indicators"]]
                res["level"]=_level(res["score"]) if res["score"]>=res["score"] else res["level"]
        except Exception as e: res["intelligence_error"]=str(e)
    return res
def analyze(kind, value=None, html=None, path=None, url=None, deep=False):
    if kind=="message": return analyze_message(value,deep)
    if kind=="url": return analyze_url_item(value,deep)
    if kind=="website": return analyze_website(html if html is not None else value, url=url)
    if kind=="apk": return analyze_apk(path, known_path=os.path.join(HERE,"known_bad_apps.json"))
    raise ValueError("kind must be message|url|website|apk")
