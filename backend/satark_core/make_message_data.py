"""Synthetic India-specific scam/genuine message generator (template families, EN / Hinglish / Hindi).
NEVER uses real personal data. Each row carries a template id so evaluation can hold out whole templates."""
import random, csv
R = random.Random(7)
BANKS = ["SBI","HDFC Bank","ICICI Bank","Axis Bank","PNB","Bank of Baroda","Kotak","Canara Bank","Paytm Payments Bank","IDFC First"]
BRANDS = ["Amazon","Flipkart","Meesho","Myntra","Swiggy","Zomato","BlueDart","Delhivery","India Post","DTDC"]
SCAMTLD = ["xyz","top","click","live","online","site","info","icu","vip","cfd"]
def dom(b): return f"{b.lower().replace(' ','')}-{R.choice(['kyc','verify','update','secure','pay','track','claim'])}.{R.choice(SCAMTLD)}"
def link(b=None): return f"http://{dom(b or R.choice(BANKS+BRANDS))}/{R.choice(['login','kyc','pay','x','a1b2','verify'])}"
def short(): return R.choice(["bit.ly","tinyurl.com","cutt.ly","rb.gy"])+"/"+"".join(R.choice("abcdefghijkmnpqrstuvwxyz23456789") for _ in range(6))
def ph(): return str(R.choice([6,7,8,9]))+"".join(R.choice("0123456789") for _ in range(9))
def amt(): return R.choice(["5000","10000","25000","50000","1 lakh","2 lakh","5 lakh","25 lakh","99,000"])
def small(): return R.choice(["10","49","99","149","199","499"])
def disc(): return R.choice(["tomorrow","today","24 hours","2 hours","tonight","immediately"])
def otp(): return "".join(R.choice("0123456789") for _ in range(R.choice([4,6])))
def name(): return R.choice(["Rahul","Priya","Amit","Neha","Vikas","Sunita","Ravi","Pooja","Mohit","Anita"])
def upi(): return R.choice(["pay","help","claim","refund","support"])+str(R.randint(10,9999))+"@"+R.choice(["ybl","paytm","okaxis","ibl","oksbi"])

T = {}
T["Phishing"] = [
 "Dear customer, your {B} account will be blocked {D}. Update your KYC now: {L}",
 "{B} ALERT: Your PAN card is not linked. Account will be suspended. Click {L} to update",
 "Dear {B} user your net banking is deactivated. Re-activate here {L} or call {P}",
 "Your electricity bill is unpaid, power will be disconnected tonight 9:30 PM. Contact officer {P} immediately",
 "Bijli bill pending hai, aaj raat connection kat jayega. Turant {P} par sampark karein ya {L}",
 "Aapka {B} account block ho jayega. KYC update karne ke liye click karein {L}",
 "आपका बिजली कनेक्शन आज रात 9:30 बजे कट जाएगा। तुरंत {P} पर संपर्क करें",
 "आपका {B} खाता बंद हो जाएगा। KYC अपडेट करने के लिए यहाँ क्लिक करें {L}",
 "Your {BR} parcel is held at customs. Pay Rs {S} redelivery fee here: {L}",
 "{BR}: delivery failed due to incomplete address. Update address within {D}: {L}",
 "Aapka parcel atka hua hai, address confirm karein {L} warna return ho jayega",
 "Income Tax Dept: refund of Rs {SM} pending. Verify bank details at {L}",
 "Aadhaar suspended due to illegal activity. Verify at {L} to avoid action",
 "Traffic challan of Rs {S} issued on your vehicle. Pay now to avoid court notice: {L}",
 "Your SIM will be blocked in {D}. Complete KYC at {L}",
 "{B}: Rs {SM} debited from your account. If not you, login to secure account {L}",
 "Your {B} credit card reward points worth Rs {S} expire today. Redeem now {L}",
]
T["Job Scam"] = [
 "Work from home job! Earn Rs {S} per day by liking YouTube videos. WhatsApp {P}",
 "Part time job offer: earn Rs {SM} daily, no experience needed. Join Telegram group {L}",
 "Hiring {BR} data entry. Salary 30000 monthly, pay Rs {S} registration fee. Contact {P}",
 "Ghar baithe kamayein Rs {S} roz, sirf mobile chahiye. WhatsApp karein {P}",
 "Aapka resume shortlist hua hai. Job confirm karne ke liye Rs {S} jama karein {upi}",
 "घर बैठे हर दिन {S} रुपये कमाएं। अभी WhatsApp करें {P}",
 "Congratulations, you are selected for {BR} work from home task job. Task income Rs {SM}/day. Message {P}",
 "Online typing job, daily payment guaranteed. Deposit Rs {S} security amount to {upi}",
 "Hi, HR from {BR} here. Part-time review job, earn 3000-8000 per day. Reply on {L}",
]
T["Reward Scam"] = [
 "Congratulations! You have won Rs {BIG} in KBC lottery. Send processing fee to claim. Call {P}",
 "You are lucky winner of {BR} mega draw prize Rs {BIG}. Claim now {L}",
 "Aapne Rs {BIG} ki lottery jeeti hai! Claim karne ke liye fee bhejein {upi}",
 "आपने {BIG} रुपये की लॉटरी जीती है। इनाम पाने के लिए संपर्क करें {P}",
 "Dear customer you won an iPhone from {BR} anniversary sale. Pay Rs {S} delivery charge {L}",
 "Free gift! Scratch card of Rs {BIG} is waiting for you. Claim before {D}: {L}",
 "Cashback of Rs {S} credited? Click {L} to receive reward now",
]
T["Loan Scam"] = [
 "Instant loan Rs {BIG} approved in 5 minutes, no documents. Download app {L}",
 "Pre-approved personal loan of Rs {BIG} at 0% interest. Pay processing fee Rs {S} {upi}",
 "Aapka loan approve ho gaya hai Rs {BIG}. App download karein {L} aur contact allow karein",
 "Urgent cash loan without CIBIL. Install our app {L} and get money in 10 minutes",
 "आपका {BIG} का लोन मंजूर हो गया है। एप डाउनलोड करें {L}",
 "Loan app: repay Rs {SM} today or we will send your photos to all your contacts. Call {P}",
 "Low interest loan up to Rs {BIG}, no income proof, instant disbursal. WhatsApp {P}",
]
T["Investment Scam"] = [
 "Invest Rs {S} and get Rs {BIG} in 30 days guaranteed returns. Join {L}",
 "Share market tips group, 100% profit guaranteed daily. VIP group {L} call {P}",
 "Crypto doubling scheme: send USDT and receive double in 7 days. Contact {P}",
 "Paisa double karein 15 din mein, guaranteed return. Refer friends aur commission kamayein {L}",
 "निवेश करें और हर दिन 5% रिटर्न पाएं। गारंटीड मुनाफा। अभी जुड़ें {L}",
 "Join our betting platform, deposit Rs {S}, win Rs {BIG}. IPL fixed match tips {L}",
 "Earn passive income: MLM plan, refer 3 members and get Rs {SM} bonus per referral. {L}",
 "Trading signals with 95% accuracy, deposit {S} and withdraw profit daily on {L}",
]
T["Refund Scam"] = [
 "Your refund of Rs {SM} is ready. Share OTP to receive money in your account",
 "{BR}: order cancelled, refund pending. Click {L} to enter card details for refund",
 "Aapka refund atka hua hai. Refund lene ke liye apna UPI PIN daalein {L}",
 "Excess amount of Rs {SM} was debited. Return it to {upi} or legal action will be taken",
 "GST refund pending Rs {SM}. Verify account at {L}",
]
T["Tech Support Scam"] = [
 "WARNING: your phone has a virus. Call Microsoft support {P} immediately",
 "Your {B} app is expired. Install AnyDesk and share the 9 digit code with our agent to renew",
 "Security alert: your device is hacked. Download TeamViewer QuickSupport and call {P}",
 "Aapka phone hack ho gaya hai, turant {P} par call karein",
 "Your Google account is compromised. Contact support {P} to secure it",
]
T["Identity Theft Scam"] = [
 "This is {B} officer. Share your Aadhaar and PAN for verification or account will be frozen. Call {P}",
 "Your parcel contains illegal items. CBI/Customs officer {P} will call you. Do not disconnect. Send ID proof",
 "Police notice: your Aadhaar is linked to money laundering case. Video call {P} to avoid arrest",
 "Aapke naam par illegal SIM mili hai. Aadhaar aur PAN ki copy bhejein {P}",
 "TRAI notice: your number will be disconnected. Press 1 to talk to officer, share Aadhaar {P}",
 "Digital arrest warning: stay on video call, share bank details with officer {P}",
]
T["SMS Spam"] = [
 "Flat 50% off on all items at {BR}. Shop now! T&C apply",
 "Get your dream home with easy EMI. Call {P} for site visit this weekend",
 "Big Billion sale starts tomorrow. Up to 80% off on electronics. Visit store",
 "Recharge Rs {S} and get 2GB extra data. Offer valid till Sunday",
 "Learn English speaking in 30 days. Join our coaching, free demo class. Call {P}",
 "Dhamaka offer! Buy 1 get 1 free on pizza at {BR} today only",
 "Congratulations on your anniversary! Visit our jewellery showroom for 10% off making charges",
 "Open a demat account with zero brokerage. Download our app from the Play Store",
]
T["Genuine"] = [
 "{otp} is your OTP for {B} transaction of Rs {SM}. Do not share it with anyone.",
 "Your OTP for login to {BR} is {otp}. Valid for 10 minutes. Do not share.",
 "Rs {SM} debited from A/c XX{n4} on {D2} via UPI. Ref {n4}{n4}. If not you call 1800-1234 - {B}",
 "Rs {SM} credited to your A/c XX{n4}. Available balance Rs {BIG}. -{B}",
 "Dear customer, your {BR} order has been shipped and will arrive on Thursday. Track in the app.",
 "Your {BR} order #{n4}-{n4} was delivered. Rate your experience in the app.",
 "Hey are we meeting for lunch tomorrow at 1?",
 "Hi mom I will be late today, dinner at 9",
 "Bhai kal match dekhne chalna hai kya? Shaam ko 7 baje",
 "Meeting moved to 4 pm, conf room B. Please bring the report.",
 "Your appointment with Dr. {N} is confirmed for tomorrow 11:30 AM at the clinic.",
 "PNR {n4}{n4}: your train ticket is confirmed. Seat S4/32. Happy journey. -IRCTC",
 "Salary of Rs {BIG} has been credited to your account XX{n4}.",
 "Your electricity bill of Rs {SM} for the month is generated. Pay by due date at the official portal or app.",
 "Your {B} credit card statement is generated. Minimum due Rs {SM}. Pay via the official app.",
 "Reminder: your LIC premium of Rs {SM} is due on {D2}. -LIC of India",
 "Thanks for your payment of Rs {SM}. Receipt sent to your email.",
 "आपका ओटीपी {otp} है। इसे किसी के साथ साझा न करें।",
 "Aapka recharge Rs {S} successful ho gaya. Validity 28 din. Thank you.",
 "Happy birthday {N}! Wishing you a wonderful year ahead.",
 "Your {BR} refund of Rs {SM} has been processed to your original payment method in 3-5 days.",
 "{B}: Never share your OTP, PIN or CVV with anyone. We never ask for it on call or SMS.",
 "Your cab is arriving in 3 minutes. Driver: {N}, plate RJ14 {n4}.",
 "Class test on Monday. Please complete chapters 4 and 5.",
]

def fill(t):
    return (t.replace("{B}",R.choice(BANKS)).replace("{BR}",R.choice(BRANDS)).replace("{L}",R.choice([link(),link(),short()]))
        .replace("{P}",ph()).replace("{S}",small() if R.random()<.5 else R.choice(["500","1000","2500"])).replace("{SM}",R.choice(["1,250","499","3,200","780","15,000","2,499"]))
        .replace("{BIG}",amt()).replace("{D}",disc()).replace("{D2}",R.choice(["12-Nov","03-Dec","28-Nov","15-Dec"]))
        .replace("{upi}",upi()).replace("{otp}",otp()).replace("{N}",name()).replace("{n4}",str(R.randint(1000,9999))))

def build(per_template=14):
    rows=[]
    for label, temps in T.items():
        for i,t in enumerate(temps):
            for _ in range(per_template):
                rows.append((fill(t),label,f"{label}:{i}"))
    R.shuffle(rows); return rows
if __name__=="__main__":
    rows=build()
    with open("messages_synthetic.csv","w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["text","label","template"]); w.writerows(rows)
    print(len(rows),"rows")
