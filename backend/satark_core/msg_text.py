import re

def norm(t):
    t=re.sub(r"https?://\S+|www\.\S+|\b[\w-]+\.(?:xyz|top|click|live|online|site|info|icu|vip|cfd)\S*"," URLTOKEN ",t,flags=re.I)
    t=re.sub(r"\b[6-9]\d{9}\b"," PHONETOKEN ",t)
    t=re.sub(r"[\w.-]+@\w+"," UPITOKEN ",t)
    t=re.sub(r"\b\d{4,6}\b"," NUMTOKEN ",t)
    return t.lower()
