"""Fill the database with SYNTHETIC demo cases so the dashboard, heat-list and linked clusters are not empty.
Run from backend/:   python scripts/seed_demo.py          (add --reset to wipe the database first)"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("DEEP_CHECKS", "0")      # no internet needed for demo data
os.environ.setdefault("FETCH_WEBSITES", "0")
from app import config, db
from app.services import analysis as A

if "--reset" in sys.argv and os.path.exists(config.DB_PATH):
    os.remove(config.DB_PATH); print("Old database removed.")
db.init()

MESSAGES = [
    ("Dear SBI customer, your YONO account is suspended. Complete KYC today: http://sbi-yono-kyc.top/login or call 9812345670", "sms"),
    ("SBI ALERT: KYC pending, account will be blocked tonight. Update at http://sbi-kyc-update.top/login. Helpline 9812345670", "sms"),
    ("Your India Post parcel is held. Pay Rs 25 redelivery fee: http://indiapost-redeliver.xyz/pay", "sms"),
    ("India Post: package could not be delivered. Pay Rs 30 fee http://indiapost-track.xyz/fee to reschedule", "sms"),
    ("Bijli vibhag: aapka bill pending hai, aaj raat connection kat jayega. Officer se baat karein 9123456780", "whatsapp"),
    ("Work from home, like and subscribe tasks, earn 4000 daily. Join Telegram t.me/earnfast. Pay Rs 500 registration fee to earnfast@ybl", "whatsapp"),
    ("Part time job: earn Rs 5000 per day from home. Deposit Rs 1000 to unlock tasks, UPI earnfast@ybl. WhatsApp 9123456780", "whatsapp"),
    ("Instant loan Rs 1 lakh approved without documents. Install FastCash app http://fastcash-loan.xyz/app.apk", "sms"),
    ("This is CBI. A digital arrest warrant is issued on your Aadhaar. Join video call, do not tell anyone. Pay security deposit to cbi.officer@oksbi", "sms"),
    ("Double your money in 21 days. Guaranteed returns. Refer 5 friends for bonus. Join http://profit-club.top", "social"),
    ("You have won Rs 10,00,000 in Jio lucky draw. Pay Rs 999 processing fee to claim: http://jio-lucky.click/claim", "sms"),
    ("Your phone is infected. Install AnyDesk and call our technician on 9988776655", "email"),
    ("482913 is your one time password for HDFC Bank NetBanking. Never share it with anyone.", "sms"),
    ("Your Swiggy order is out for delivery and will reach in 15 minutes", "sms"),
]
for text, ch in MESSAGES:
    c = A.analyze_message(text, "citizen", ch)
    print(f"#{c['case_id']:<3} {c['level']:<6} {c['verdict']:<24} {text[:55]}")

for url in ("http://sbi-kyc-update.top/login", "https://www.amazon.in/"):
    c = A.analyze_url(url, "citizen"); print(f"#{c['case_id']:<3} {c['level']:<6} url {url}")

SITE = """<html><title>Profit Club - Daily Income</title><body><h1>Guaranteed returns 5% daily profit</h1>
<p>Refer and earn level income, binary plan. Minimum deposit Rs 1000. Pay to profitclub@ybl or call 9812345670. Limited slots, register now.</p>
<form><input type=password name=pw><input name=otp placeholder="OTP"></form></body></html>"""
c = A.analyze_website(html=SITE, url="http://profit-club.top"); print(f"#{c['case_id']:<3} {c['level']:<6} website profit-club.top")

for apk in ("test_loan.apk", "test_bet.apk", "test_calc.apk"):
    c = A.analyze_apk_file(os.path.join(ROOT, "samples", apk), apk, "officer"); print(f"#{c['case_id']:<3} {c['level']:<6} apk {apk}")
print("\nDone.", db.stats())
