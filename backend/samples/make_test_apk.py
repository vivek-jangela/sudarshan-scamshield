"""Builds SAFE synthetic test APKs (binary AndroidManifest + fake dex strings). Not runnable apps."""
import struct, zipfile
def _pool(strings):
    data=b""; offs=[]
    for s in strings:
        offs.append(len(data)); b=s.encode("utf-16le"); data+=struct.pack("<H",len(s))+b+b"\x00\x00"
    while len(data)%4: data+=b"\x00"
    hs=28; start=hs+4*len(strings)
    return struct.pack("<HHIIIIII",0x0001,hs,start+len(data),len(strings),0,0,start,0)+struct.pack(f"<{len(strings)}I",*offs)+data
def build_manifest(package, label, perms):
    S=["package","name","label","versionName","manifest","uses-permission","application","1.0",package,label]+["android.permission."+p for p in perms]
    ix={s:i for i,s in enumerate(S)}
    def start(tag,attrs):
        a=b"".join(struct.pack("<IIIHBBI",0xFFFFFFFF,ix[k],ix[v],8,0,3,ix[v]) for k,v in attrs)
        body=struct.pack("<IIHHHHHH",0xFFFFFFFF,ix[tag],20,20,len(attrs),0,0,0)+a
        return struct.pack("<HHIII",0x0102,16,16+len(body),1,0xFFFFFFFF)+body
    def end(tag):
        body=struct.pack("<II",0xFFFFFFFF,ix[tag]); return struct.pack("<HHIII",0x0103,16,16+len(body),1,0xFFFFFFFF)+body
    chunks=_pool(S)+start("manifest",[("package",package),("versionName","1.0")])
    for p in perms: chunks+=start("uses-permission",[("name","android.permission."+p)])+end("uses-permission")
    chunks+=start("application",[("label",label)])+end("application")+end("manifest")
    return struct.pack("<HHI",0x0003,8,8+len(chunks))+chunks
def make(path,package,label,perms,dex_text):
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("AndroidManifest.xml",build_manifest(package,label,perms))
        z.writestr("classes.dex",b"dex\n035\x00"+dex_text.encode())
        z.writestr("META-INF/CERT.RSA",b"TEST-CERT-"+package.encode())
if __name__=="__main__":
    make("test_loan.apk","com.fastcash.instantloan","FastCash Instant Loan",
         ["INTERNET","READ_SMS","READ_CONTACTS","CAMERA","READ_EXTERNAL_STORAGE","READ_CALL_LOG","READ_PHONE_STATE"],
         "http://45.33.12.9/api/upload_contacts http://fastcash-loan.xyz/collect pay to loanrecover88@ybl call 9876501234 https://schemas.android.com/apk/res/android")
    make("test_calc.apk","com.simple.calculator","Simple Calculator",["INTERNET"],"https://github.com/example/calc")
    make("test_bet.apk","com.teenpatti.earnbet","Teen Patti Earn",["INTERNET","READ_SMS","SYSTEM_ALERT_WINDOW"],"http://bet99.top/deposit usdt TXyz1234567890abcdefghijklmnopqrst")
