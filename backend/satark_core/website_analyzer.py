"""Website / page content analyzer: Ponzi, MLM, betting, fake-investment indicators + identifier extraction."""
import re
from bs4 import BeautifulSoup
from url_features import extract_identifiers, analyze_url

RULES = {
 "Guaranteed / unrealistic returns": (30, r"guarantee[d]?\s+(?:return|profit|income)|100%\s*(?:profit|return|safe|guarantee)|double\s+your\s+(?:money|investment)|daily\s+(?:profit|income|return)|\b\d{1,3}\s*%\s*(?:daily|per\s*day|weekly|monthly)\s*(?:return|profit|roi|interest)?|risk[\s-]*free|assured\s+(?:return|profit)|गारंटीड|पैसा\s+दोगुना"),
 "Referral-chain / MLM language": (25, r"refer\s+(?:and|&)\s+earn|referral\s+(?:bonus|commission|income)|downline|upline|level\s+income|binary\s+plan|network\s+marketing|\bmlm\b|team\s+(?:bonus|commission)|join\s+(?:and|&)\s+earn|rank\s+achiever"),
 "Betting / gambling indicators": (30, r"\bbet(?:ting|s)?\b|\bcasino\b|\bsatta\b|\bmatka\b|teen\s*patti|andar\s*bahar|\bjackpot\b|\bcricket\s+id\b|ipl\s+(?:tips|fixed|id)|fixed\s+match|\broulette\b|slot\s+machines?|online\s+slots|sports\s*book|\bwager\b"),
 "Unregistered investment / crypto scheme": (20, r"\busdt\b|crypto\s+(?:mining|doubling|trading)|forex\s+(?:signal|trading)|trading\s+signals?|vip\s+(?:group|tips)|stock\s+tips?|nifty\s+calls?|binary\s+options?|cloud\s+mining"),
 "Pressure / urgency": (10, r"limited\s+(?:time|slots|seats)|hurry|only\s+\d+\s+(?:left|slots|seats)|offer\s+(?:ends|expires)|register\s+(?:now|today)|last\s+chance|act\s+now"),
 "Upfront fee / deposit demanded": (20, r"registration\s+fee|processing\s+fee|security\s+(?:deposit|amount)|minimum\s+deposit|deposit\s+(?:rs|₹|inr)|activation\s+fee|joining\s+fee"),
}
CATEGORY = {"Guaranteed / unrealistic returns":"Ponzi/Investment","Referral-chain / MLM language":"MLM/Ponzi",
            "Betting / gambling indicators":"Illegal Betting","Unregistered investment / crypto scheme":"Fake Investment"}

def page_text(html):
    soup = BeautifulSoup(html, "lxml")
    for t in soup(["script","style","noscript"]): t.decompose()
    return soup, re.sub(r"\s+"," ",soup.get_text(" ")).strip()

def analyze_website(html, url=None):
    soup, text = page_text(html)
    score, indicators, cats = 0, [], {}
    for name,(pts,rx) in RULES.items():
        hits = re.findall(rx, text, flags=re.I)
        if hits:
            score += pts
            ex = sorted({(h if isinstance(h,str) else h[0]).strip().lower() for h in hits})[:3]
            indicators.append(f"{name}: " + ", ".join(f"'{e}'" for e in ex) + f" (+{pts})")
            if name in CATEGORY: cats[CATEGORY[name]] = cats.get(CATEGORY[name],0)+pts
    # forms: credential / card / OTP harvesting
    inputs = [i.get("type","").lower()+" "+(i.get("name","")+i.get("placeholder","")).lower() for i in soup.find_all("input")]
    blob=" ".join(inputs)
    if re.search(r"password",blob) and re.search(r"otp|pin|card|cvv|aadhaar|pan",blob):
        score+=25; indicators.append("Form collects password plus OTP/PIN/card/Aadhaar details (+25)")
    elif re.search(r"otp|cvv|card\s*number|aadhaar|upi\s*pin",blob):
        score+=15; indicators.append("Form collects sensitive financial/ID details (+15)")
    if re.search(r"\.apk\b",str(soup),flags=re.I):
        score+=15; indicators.append("Page pushes a direct APK download (+15)")
    # identifiers (visible text + links)
    hrefs=" ".join(a.get("href","") for a in soup.find_all("a"))
    ids = extract_identifiers(text+" "+hrefs)
    ids.pop("urls",None)
    if ids.get("upi_ids") or ids.get("btc") or ids.get("eth") or ids.get("trx"):
        score+=10; indicators.append("Page asks payment to personal UPI ID / crypto wallet (+10)")
    urlres = analyze_url(url) if url else None
    if urlres and urlres["score"]>=25:
        score += min(urlres["score"]//2, 25); indicators.append(f"Domain risk: {urlres['level']} ({'; '.join(urlres['indicators'][:2])})")
    score=min(score,100)
    level="HIGH" if score>=50 else "MEDIUM" if score>=25 else "LOW"
    top = max(cats,key=cats.get) if cats else ("Suspicious Website" if score>=25 else "No scam pattern")
    return {"type":"website","url":url,"category":top,"score":score,"level":level,
            "indicators":indicators or ["No scam indicators found"],"identifiers":ids,"title":(soup.title.string.strip() if soup.title and soup.title.string else None),
            "text_excerpt":text[:400]}
