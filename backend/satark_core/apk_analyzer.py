"""Static APK analyzer (no execution). Pure Python: zipfile + minimal binary-AndroidManifest (AXML) parser."""
import zipfile, hashlib, re, struct, json, os
from url_features import extract_identifiers, BRANDS

DANGEROUS = {  # permission -> (points, why)
 "READ_SMS":(12,"reads SMS (OTP theft)"),"RECEIVE_SMS":(8,"intercepts incoming SMS"),"SEND_SMS":(8,"can send SMS"),
 "READ_CONTACTS":(12,"reads contacts (harassment / recovery abuse)"),"WRITE_CONTACTS":(5,"modifies contacts"),
 "READ_CALL_LOG":(10,"reads call log"),"CAMERA":(6,"camera access"),"RECORD_AUDIO":(6,"microphone access"),
 "READ_EXTERNAL_STORAGE":(4,"reads photos/files"),"MANAGE_EXTERNAL_STORAGE":(8,"full storage access"),
 "ACCESS_FINE_LOCATION":(4,"precise location"),"READ_PHONE_STATE":(4,"reads device identifiers"),
 "SYSTEM_ALERT_WINDOW":(10,"draws over other apps (overlay attacks)"),"BIND_ACCESSIBILITY_SERVICE":(15,"accessibility service abuse"),
 "REQUEST_INSTALL_PACKAGES":(8,"can install other apps"),"BIND_DEVICE_ADMIN":(12,"device admin"),"READ_PHONE_NUMBERS":(4,"reads phone number"),
 "GET_ACCOUNTS":(4,"lists accounts"),"QUERY_ALL_PACKAGES":(4,"lists installed apps"),"CALL_PHONE":(3,"places calls"),
}
LOAN_WORDS = ["loan","cash","credit","rupee","money","fast","instant","quick","emi","borrow","lend","paisa","kredit","finance"]
INVEST_WORDS = ["invest","trade","trading","crypto","earn","profit","bet","casino","teen patti","ludo","rummy","mining"]

# ---- minimal AXML parser ----
def _read_pool(d, off):
    typ,hs,size,n,_,flags,sstart,_ = struct.unpack_from("<HHIIIIII", d, off)
    utf8 = bool(flags & 0x100)
    offs = struct.unpack_from(f"<{n}I", d, off+hs)
    out=[]
    for o in offs:
        p = off+sstart+o
        if utf8:
            l = d[p]; p += 1 + (1 if l&0x80 else 0)
            l2 = d[p]; p+=1
            if l2&0x80: l2=((l2&0x7f)<<8)|d[p]; p+=1
            out.append(d[p:p+l2].decode("utf-8","replace"))
        else:
            l=struct.unpack_from("<H",d,p)[0]; p+=2
            if l&0x8000: l=((l&0x7fff)<<16)|struct.unpack_from("<H",d,p)[0]; p+=2
            out.append(d[p:p+l*2].decode("utf-16le","replace"))
    return out, size

def parse_manifest(d):
    if struct.unpack_from("<H",d,0)[0]!=0x0003: raise ValueError("not binary XML")
    off=8; pool=[]; res={"package":None,"version_name":None,"app_label":None,"permissions":[],"components":0}
    while off<len(d):
        typ,hs,size=struct.unpack_from("<HHI",d,off)
        if typ==0x0001: pool,_=_read_pool(d,off)
        elif typ==0x0102:
            ns,name,astart,asize,acount=struct.unpack_from("<IIHHH",d,off+0x10)[0:5]
            tag=pool[name] if name<len(pool) else ""
            ao=off+0x10+20
            attrs={}
            for i in range(acount):
                _ns,an,raw,vsz,_r,vt,vd = struct.unpack_from("<IIIHBBI",d,ao+i*20)
                key=pool[an] if an<len(pool) else str(an)
                val=pool[raw] if raw!=0xFFFFFFFF and raw<len(pool) else (pool[vd] if vt==3 and vd<len(pool) else vd)
                attrs[key]=val
            if tag=="manifest": res["package"]=attrs.get("package"); res["version_name"]=attrs.get("versionName")
            elif tag=="uses-permission" and "name" in attrs: res["permissions"].append(str(attrs["name"]))
            elif tag=="application" and isinstance(attrs.get("label"),str): res["app_label"]=attrs["label"]
            elif tag in ("activity","service","receiver","provider"): res["components"]+=1
        off+=size
    return res

def _cert_hash(z):
    for n in z.namelist():
        if n.upper().startswith("META-INF/") and n.upper().endswith((".RSA",".DSA",".EC")):
            return hashlib.sha256(z.read(n)).hexdigest()
    return None

def analyze_apk(path, known_path=None):
    z=zipfile.ZipFile(path)
    names=z.namelist()
    if "AndroidManifest.xml" not in names: raise ValueError("Not an APK (no AndroidManifest.xml)")
    m=parse_manifest(z.read("AndroidManifest.xml"))
    perms=sorted({p.split(".")[-1] for p in m["permissions"]})
    score,ind=0,[]
    for p in perms:
        if p in DANGEROUS:
            pts,why=DANGEROUS[p]; score+=pts; ind.append(f"Permission {p}: {why} (+{pts})")
    combo = {"READ_SMS","READ_CONTACTS"} <= set(perms) or {"READ_CONTACTS","CAMERA","READ_EXTERNAL_STORAGE"} <= set(perms)
    if combo: score+=15; ind.append("Risky combination (SMS/contacts/camera/storage together) typical of predatory loan apps (+15)")
    # strings from dex / assets / resources
    blob=b""
    for n in names:
        if n.endswith((".dex",".json",".xml",".html",".js",".txt",".properties")) and not n.startswith("META-INF") and n!="AndroidManifest.xml":
            blob+=z.read(n)[:5_000_000]
    text=blob.decode("latin-1")
    text=re.sub(r"[^\x20-\x7e\n]"," ",text)
    ids=extract_identifiers(text)
    urls=[u for u in ids.get("urls",[]) if not re.search(r"schemas\.android|w3\.org|apache\.org|google\.com|googleapis|gstatic|example\.com|android\.com|github\.com|xmlpull|schemas\.microsoft",u)]
    ips=sorted(set(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b",text)))
    ips=[i for i in ips if all(int(o)<256 for o in i.split(".")) and not i.startswith(("0.","127.","255."))]
    ids.pop("urls",None); ids["urls"]=sorted(set(urls))[:25]
    if ips: ids["ip_addresses"]=ips[:15]; score+=8; ind.append("Hard-coded IP addresses in code (+8)")
    pkg=m["package"] or ""; label=(m["app_label"] or "")
    lw=[w for w in LOAN_WORDS if w in (pkg+" "+label).lower()]
    iw=[w for w in INVEST_WORDS if w in (pkg+" "+label).lower()]
    category="Suspicious App" if score>=25 else "App (low risk)"
    if lw and score>=15: score+=15; category="Fake/Predatory Loan App"; ind.append(f"Loan-style name/package {lw} with sensitive permissions (+15)")
    if iw and score>=10: score+=15; category="Fake Investment/Betting App"; ind.append(f"Investment/betting-style name/package {iw} (+15)")
    if pkg and not re.match(r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$",pkg,re.I): score+=5; ind.append("Unusual package identifier (+5)")
    cert=_cert_hash(z)
    if not cert: score+=5; ind.append("APK has no readable signing certificate (+5)")
    # similarity vs known bad registry
    match=None
    if known_path and os.path.exists(known_path):
        for k in json.load(open(known_path)):
            if (cert and k.get("cert_sha256")==cert) or (pkg and k.get("package")==pkg):
                match=k; score+=40; ind.append(f"Matches known suspicious app '{k.get('name')}' (same package/signature) (+40)"); break
    score=min(score,100)
    level="HIGH" if score>=50 else "MEDIUM" if score>=25 else "LOW"
    return {"type":"apk","package":pkg,"app_label":label,"version":m["version_name"],"permissions":perms,"cert_sha256":cert,
            "sha256":hashlib.sha256(open(path,'rb').read()).hexdigest(),"score":score,"level":level,"category":category,
            "indicators":ind or ["No suspicious indicators found"],"identifiers":{k:v for k,v in ids.items() if v},"known_match":match}
