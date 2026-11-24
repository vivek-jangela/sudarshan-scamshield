import pandas as pd, numpy as np, joblib, re, warnings
warnings.filterwarnings("ignore")
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import classification_report, accuracy_score

from msg_text import norm
def make():
    feats=FeatureUnion([
      ("w",TfidfVectorizer(preprocessor=norm,ngram_range=(1,2),min_df=2,sublinear_tf=True)),
      ("c",TfidfVectorizer(preprocessor=norm,analyzer="char_wb",ngram_range=(2,5),min_df=3,sublinear_tf=True,max_features=60000))])
    return Pipeline([("f",feats),("clf",LogisticRegression(C=8,max_iter=2000,class_weight="balanced"))])

def main():
    df=pd.read_csv("messages_synthetic.csv")
    X,y,g=df.text.values,df.label.values,df.template.values
    # honest eval: whole templates held out
    pred=np.empty(len(y),dtype=object)
    for tr,te in GroupKFold(5).split(X,y,g):
        m=make().fit(X[tr],y[tr]); pred[te]=m.predict(X[te])
    print("Held-out-TEMPLATE accuracy: %.3f"%accuracy_score(y,pred))
    print(classification_report(y,pred,digits=3))

    # independent hand-written test set (different wording from templates)
    IND=[
    ("Dear SBI customer, your YONO account is suspended. Complete KYC today: http://sbi-yono-kyc.top/login","Phishing"),
    ("Your Amazon order is on hold. Confirm delivery address and pay Rs 25: http://amzn-delivery-help.xyz/a","Phishing"),
    ("Bijli vibhag: aapka bill 3 mahine se pending hai, aaj connection kat dena hai. Officer se baat karein 9812345670","Phishing"),
    ("Work from home, like and subscribe tasks, earn 4000 daily. DM on Telegram t.me/earnfast","Job Scam"),
    ("Ghar se kaam karke 5000 rupaye roz kamayein. Abhi WhatsApp karein 9123456780","Job Scam"),
    ("You have been selected as lucky winner of Rs 10,00,000 in Jio lucky draw. Pay Rs 999 to receive","Reward Scam"),
    ("Instant loan Rs 1 lakh approved without documents, install FastCash app http://fastcash-loan.xyz/app.apk","Loan Scam"),
    ("Double your money in 21 days. Guaranteed returns. Refer 5 friends for bonus. Join http://profit-club.top","Investment Scam"),
    ("Your refund is pending, share the OTP sent to you to receive money","Refund Scam"),
    ("Your phone is infected. Install AnyDesk and call our technician on 9988776655","Tech Support Scam"),
    ("This is CBI. A case is registered against your Aadhaar. Join video call and do not tell anyone","Identity Theft Scam"),
    ("Get 40% off on shoes this weekend only at our store, Jaipur. Visit now","SMS Spam"),
    ("482913 is your one time password for HDFC Bank NetBanking. Never share it with anyone.","Genuine"),
    ("Rs 2,300 debited from your account ending 4421 on 22-Nov. UPI ref 3321 -ICICI Bank","Genuine"),
    ("Your Flipkart order has been delivered. Thank you for shopping!","Genuine"),
    ("Hey, can you send me the notes from yesterday's lecture?","Genuine"),
    ("Kal subah 10 baje meeting hai, time par aana","Genuine"),
    ("Your Swiggy order is out for delivery and will reach in 15 minutes","Genuine"),
    ("Your electricity bill for October is Rs 1,840. Pay before 5 Dec via the official app.","Genuine"),
    ("Aapka OTP 559201 hai. Kisi ke saath share na karein.","Genuine"),
    ]
    m_all=make().fit(X,y)
    p=m_all.predict([t for t,_ in IND]); ok=0
    for (t,l),pp in zip(IND,p):
        ok+= (pp==l); print(("OK  " if pp==l else "MISS"),f"{l:20s}->{pp:20s}",t[:62])
    print(f"Independent set: {ok}/{len(IND)}")
    bin_ok=sum((pp=="Genuine")==(l=="Genuine") for (t,l),pp in zip(IND,p)); print(f"Scam-vs-genuine only: {bin_ok}/{len(IND)}")
    joblib.dump({"model":m_all,"classes":list(m_all.classes_),"version":"3.0-synthetic","note":"trained on synthetic template data; retrain with R4C sample set"},"message_model_v3.pkl")

if __name__=='__main__':
    main()
