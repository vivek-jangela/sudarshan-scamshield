"""Rule-based URL risk scorer + identifier extractor for SATARK NETRA (offline, no training data needed)."""
import re, math
from urllib.parse import urlparse
from difflib import SequenceMatcher

BRANDS = {
 "sbi":["sbi.co.in","onlinesbi.sbi","sbi.bank.in","sbicard.com"],
 "hdfc":["hdfcbank.com"],"icici":["icicibank.com"],"axis":["axisbank.com"],
 "paytm":["paytm.com"],"phonepe":["phonepe.com"],"amazon":["amazon.in","amazon.com"],
 "flipkart":["flipkart.com"],"google":["google.com"],"whatsapp":["whatsapp.com"],
 "indiapost":["indiapost.gov.in"],"incometax":["incometax.gov.in"],
 "uidai":["uidai.gov.in"],"npci":["npci.org.in"],"irctc":["irctc.co.in"],
}
SUSP_TLDS = {"xyz","top","click","live","online","site","info","cn","icu","vip","work","shop","buzz","cfd","sbs","rest","fit","gq","tk","ml","ga","cf"}
KEYWORDS = ["kyc","verify","update","login","secure","account","blocked","suspend","refund","claim","reward","win","bonus","loan","cash","pay","bill","challan","track","parcel","otp","apk","download","invest","earn","free","offer","fine","disconnect"]
SHORTENERS = {"bit.ly","tinyurl.com","t.co","goo.gl","cutt.ly","rb.gy","is.gd","ow.ly","shorturl.at","tiny.cc"}
TWO_LEVEL = {"co.in","gov.in","ac.in","org.in","net.in","nic.in","res.in","com.au","co.uk"}

def _split(host):
    parts = host.lower().split(".")
    if len(parts)>=3 and ".".join(parts[-2:]) in TWO_LEVEL:
        return ".".join(parts[:-3]), parts[-3], ".".join(parts[-2:])
    if len(parts)>=2: return ".".join(parts[:-2]), parts[-2], parts[-1]
    return "", host, ""

def _entropy(s):
    if not s: return 0
    return -sum((s.count(c)/len(s))*math.log2(s.count(c)/len(s)) for c in set(s))

def analyze_url(url):
    u = url.strip()
    p = urlparse(u if "://" in u else "http://"+u)
    host = (p.hostname or "").lower()
    sub, name, suffix = _split(host)
    reg = f"{name}.{suffix}" if suffix else name
    score, why = 0, []
    def add(pts, msg): 
        nonlocal score; score += pts; why.append(f"{msg} (+{pts})")
    # Trusted exact domain -> low
    for b, doms in BRANDS.items():
        if reg in doms or any(host==d or host.endswith("."+d) for d in doms):
            return {"url":url,"host":host,"score":0,"level":"LOW","indicators":["Official domain of known brand: "+reg],"trusted_brand_domain":True}
    if suffix in ("gov.in","nic.in","ac.in","edu") : 
        return {"url":url,"host":host,"score":0,"level":"LOW","indicators":["Government/academic domain: "+reg],"trusted_brand_domain":False}
    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host): add(40,"IP address used instead of domain")
    if reg in SHORTENERS: add(20,"URL shortener hides destination")
    if suffix.split(".")[-1] in SUSP_TLDS: add(20,f"High-abuse TLD .{suffix}")
    if p.scheme=="http": add(10,"No HTTPS")
    if "@" in u.split("?")[0].split("//",1)[-1].split("/")[0]: add(25,"'@' in authority part")
    if host.count("-")>=2: add(10,"Multiple hyphens in domain")
    if len(host)>40: add(10,"Very long hostname")
    if sub.count(".")>=2: add(10,"Many subdomain levels")
    if host.startswith("xn--") or "xn--" in host: add(20,"Punycode (possible homograph)")
    if re.search(r"[a-z][0-9][a-z]|[a-z]0[a-z]|1[a-z]{3}", name) : add(10,"Digit/letter substitution in name")
    # brand impersonation
    full = host.replace("-",".")
    for b, doms in BRANDS.items():
        if b in full or b in p.path.lower().split("/")[1:2]:
            add(35, f"Impersonates brand '{b}' but is not its official domain ({reg})"); break
        # typosquat
        if SequenceMatcher(None, name.replace("0","o").replace("1","l"), b).ratio()>0.8 and name!=b:
            add(30, f"Look-alike of brand '{b}'"); break
    hits=[k for k in KEYWORDS if k in (host+p.path).lower()]
    if hits: add(min(5*len(hits),20), "Scam keywords: "+", ".join(hits[:5]))
    if p.path.lower().endswith(".apk"): add(25,"Direct APK download")
    if _entropy(name)>3.6 and len(name)>12: add(10,"Random-looking domain")
    score=min(score,100)
    level="HIGH" if score>=50 else "MEDIUM" if score>=25 else "LOW"
    return {"url":url,"host":host,"score":score,"level":level,"indicators":why or ["No suspicious indicators found"],"trusted_brand_domain":False}

# ---------- identifier extraction ----------
UPI_HANDLES = "ybl|ibl|axl|okaxis|okhdfcbank|okicici|oksbi|paytm|apl|upi|sbi|hdfcbank|icici|axisbank|pnb|barodampay|kotak|idfcbank|fbl|ikwik|freecharge|jio|airtel|postbank|aubank|yesbank|rbl|cnrb|unionbank|indus|federal"
RX = {
 "urls": re.compile(r"(?:https?://|www\.)[^\s<>\"']+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|in|xyz|top|click|live|online|site|info|cn|icu|vip|co|net|org|apk)\b(?:/[^\s<>\"']*)?", re.I),
 "upi_ids": re.compile(rf"\b[a-z0-9._-]{{2,}}@(?:{UPI_HANDLES})\b", re.I),
 "phones": re.compile(r"(?<![\d])(?:\+?91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?!\d)"),
 "ifsc": re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),
 "bank_accounts": re.compile(r"(?i)(?:a/?c|account)(?:\s*(?:no|number|num))?\.?\s*[:\-]?\s*(\d{9,18})"),
 "btc": re.compile(r"\b(?:bc1[a-z0-9]{25,60}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b"),
 "eth": re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
 "trx": re.compile(r"\bT[1-9A-HJ-NP-Za-km-z]{33}\b"),
 "emails": re.compile(r"\b[\w.+-]+@(?!(?:%s)\b)[\w-]+(?:\.[\w-]+)+\b" % UPI_HANDLES, re.I),
}
def extract_identifiers(text):
    out={}
    for k,rx in RX.items():
        m=[x if isinstance(x,str) else x for x in rx.findall(text)]
        m=[re.sub(r"[\s-]","",x) if k=="phones" else x.rstrip(".,;)") for x in m]
        out[k]=sorted(set(m))
    out["phones"]=sorted({re.sub(r"^(\+?91|0)","",x) for x in out["phones"]})
    return {k:v for k,v in out.items() if v}
