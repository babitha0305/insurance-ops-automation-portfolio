"""Complaints email triage with human-in-the-loop review.
Classifies synthetic complaint emails (TF-IDF + logistic regression), extracts a booking reference,
auto-routes confident predictions and sends low-confidence ones to a human review queue.
The classifier is pluggable: swap `predict_proba` for an LLM call to extend it."""
import random, re, os
import numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
random.seed(7)

TEAMS = {
 "refund":   ["I want a refund for my cancelled stay", "please refund the charge, I was billed twice", "money back for booking {r}, the host cancelled", "still waiting on my reimbursement"],
 "claim":    ["I need to claim on my cancellation insurance", "my luggage was lost, how do I make a claim", "submitting an insurance claim for medical cancellation", "claim form for booking {r} was rejected"],
 "policy":   ["can you send my policy documents", "what does my cover include", "I need a copy of my certificate for {r}", "is flight delay covered under my policy"],
 "service":  ["the app crashed when I tried to log in", "your agent was rude on the phone", "very slow response from customer support", "website will not let me change my booking {r}"],
}
FILLER = ["Hi,", "Hello team,", "Dear support,", "Urgent:", "", "Thanks in advance.", "Regards, a customer", "Please help.", "This is unacceptable."]
MIXERS = ["refund", "claim", "policy", "service"]

def make_email(label):
    base = random.choice(TEAMS[label]).format(r=f"BK{random.randint(100000,999999)}")
    if random.random() < 0.25:                      # ambiguous: blend in a second topic
        other = random.choice([m for m in MIXERS if m != label])
        base += ". Also, " + random.choice(TEAMS[other]).format(r=f"BK{random.randint(100000,999999)}").lower()
    return " ".join([random.choice(FILLER), base, random.choice(FILLER)]).strip()

def extract_ref(text):
    m = re.search(r"BK\d{6}", text); return m.group(0) if m else None

if __name__ == "__main__":
    rows = [(make_email(l), l) for l in TEAMS for _ in range(250)]
    df = pd.DataFrame(rows, columns=["email", "label"]).sample(frac=1, random_state=1)
    tr, te = train_test_split(df, test_size=0.3, random_state=1, stratify=df["label"])
    vec = TfidfVectorizer(ngram_range=(1, 2)).fit(tr["email"])
    clf = LogisticRegression(max_iter=1000).fit(vec.transform(tr["email"]), tr["label"])
    proba = clf.predict_proba(vec.transform(te["email"]))
    pred = clf.classes_[proba.argmax(1)]; conf = proba.max(1)
    te = te.assign(pred=pred, conf=conf, ref=te["email"].map(extract_ref))
    print(f"Overall accuracy (no review): {(te.pred == te.label).mean():.3f}")
    print("threshold | auto-routed % | accuracy of auto-routed | sent to human %")
    for th in [0.5, 0.6, 0.7, 0.8]:
        auto = te[te.conf >= th]
        print(f"{th:>9} | {100*len(auto)/len(te):>12.1f} | {(auto.pred==auto.label).mean():>22.3f} | {100*(1-len(auto)/len(te)):>14.1f}")
    TH = 0.6
    queue = te[te.conf < TH][["email", "pred", "conf"]]
    queue.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "human_review_queue.csv"), index=False)
    refs = te["email"].str.contains(r"BK\d{6}")
    ok = (te.ref.notna() == refs).mean()
    print(f"Review queue saved ({len(queue)} emails at threshold {TH}); booking-ref extraction agreement {ok:.3f}")
