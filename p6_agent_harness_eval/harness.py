"""Small agent-harness study (numpy only, no LLM calls):
 1) Evaluation pipeline: held-out tool-routing tasks, scored against labelled ground truth.
 2) RL: REINFORCE (policy gradient) learns a tool-selection policy from reward; compared to a keyword baseline.
 3) Context optimisation: TF-IDF retrieval packs only the most relevant runbook chunks into the prompt;
    measures token savings vs recall of the needed chunk.
Run: python harness.py"""
import random, math, re
import numpy as np
random.seed(3); np.random.seed(3)

TOOLS = ["run_quality_checks", "list_flagged_records", "reconcile_to_ledger"]
T = {
 0: ["how many issues are in the {p} file", "run the data quality checks", "give me a quality summary for {p}", "are there any errors in the {p} upload", "check {p} for problems", "list how many problems we found"],
 1: ["show me the duplicate records", "which refs have missing fields", "list the schema errors for {p}", "show the negative premium rows", "which policies were flagged as duplicates", "show variance rows that were flagged"],
 2: ["does the total match the ledger", "reconcile premiums for {p}", "what is the variance by partner", "does {p} reconcile to the ledger", "how far off is the {p} total from the ledger", "show me the ledger variance"],
}
P = ["AlphaIns", "BetaCover", "GammaRisk", "this month", "the latest"]
NOISE = ["please", "quickly", "for me", "now", "can you", "hey", "urgent", "thanks"]

def gen(n):
    X, y = [], []
    for _ in range(n):
        k = random.randrange(3)
        q = random.choice(T[k]).format(p=random.choice(P))
        if random.random() < .5: q = random.choice(NOISE) + " " + q
        if random.random() < .3: q = q + " " + random.choice(NOISE)
        X.append(q); y.append(k)
    return X, y

tok = lambda s: re.findall(r"[a-z]+", s.lower())
Xtr, ytr = gen(1500); Xte, yte = gen(500)
vocab = sorted({w for q in Xtr for w in tok(q)}); vi = {w: i for i, w in enumerate(vocab)}
def feat(q):
    v = np.zeros(len(vocab) + 1); v[-1] = 1
    for w in tok(q):
        if w in vi: v[vi[w]] = 1
    return v
Ftr = np.array([feat(q) for q in Xtr]); Fte = np.array([feat(q) for q in Xte])

# ---- baseline: keyword rules
def rules(q):
    w = set(tok(q))
    if w & {"reconcile", "ledger", "variance", "total"}: return 2
    if w & {"show", "list", "which"}: return 1
    return 0
base_acc = np.mean([rules(q) == y for q, y in zip(Xte, yte)])

# ---- RL: REINFORCE
def softmax(z): z = z - z.max(-1, keepdims=True); e = np.exp(z); return e / e.sum(-1, keepdims=True)
W = np.zeros((Ftr.shape[1], 3)); b = 0.0; lr = 0.3; curve = []
untrained = np.mean(softmax(Fte @ W).argmax(1) == yte)
for ep in range(4000):
    i = np.random.randint(len(Xtr)); p = softmax(Ftr[i] @ W)
    a = np.random.choice(3, p=p)
    r = 1.0 if a == ytr[i] else 0.0                 # reward from the evaluator
    b = 0.99 * b + 0.01 * r                          # moving-average baseline
    g = -p; g[a] += 1
    W += lr * (r - b) * np.outer(Ftr[i], g)
    if (ep + 1) % 1000 == 0: curve.append(round(float(np.mean(softmax(Fte @ W).argmax(1) == yte)), 3))
rl_acc = np.mean(softmax(Fte @ W).argmax(1) == yte)
print(f"Tool-routing accuracy on {len(Xte)} held-out queries")
print(f"  random/untrained policy : {untrained:.3f}")
print(f"  keyword-rule baseline   : {base_acc:.3f}")
print(f"  REINFORCE policy        : {rl_acc:.3f}  (accuracy after every 1000 episodes: {curve})")

# ---- context optimisation: pack top-K runbook chunks by TF-IDF cosine similarity
CHUNKS = [
 "duplicate records share the same partner and policy reference; keep the first and flag the rest",
 "missing fields: name and inception date are mandatory, flag the row if either is blank",
 "schema errors: currency must be GBP, any other code is flagged for partner follow-up",
 "negative or zero premium is a financial mismatch and must be reviewed before handoff",
 "reconcile each partner premium total to the ledger and explain variance from duplicates and sign flips",
 "date formats differ by partner: day slash month, ISO, and day dash month name",
 "column headers differ by partner and are mapped to ref, name, date, premium and currency",
 "partner handoff happens on the fifth working day after month end",
 "complaints emails are triaged by confidence and low confidence goes to a human queue",
 "the ledger total is the sum of premiums booked by finance before any partner correction",
 "escalate unexplained variance above one pound to the insurance operations lead",
 "store flagged records in a csv and attach it to the partner email",
]
GOLD = [(0, "how many duplicate records are there"), (1, "which rows have missing fields"), (2, "currency code not GBP what happens"),
        (3, "what do we do with a negative premium"), (4, "how do I reconcile to the ledger"), (5, "partner dates look different"),
        (6, "headers are different between partners"), (7, "when is handoff to the partner"), (8, "where do low confidence complaints go"),
        (9, "how is the ledger total defined"), (10, "when do I escalate variance"), (11, "where are flagged records stored")]
docs = [tok(c) for c in CHUNKS]; N = len(docs)
df = {}; [df.__setitem__(w, df.get(w, 0) + 1) for d in docs for w in set(d)]
idf = lambda w: math.log((N + 1) / (df.get(w, 0) + 1)) + 1
def vec(ws):
    v = {}
    for w in ws: v[w] = v.get(w, 0) + idf(w)
    return v
def cos(a, b):
    num = sum(a[w] * b.get(w, 0) for w in a)
    return num / (math.sqrt(sum(x * x for x in a.values())) * math.sqrt(sum(x * x for x in b.values())) + 1e-9)
dv = [vec(d) for d in docs]
full_tokens = sum(len(d) for d in docs)
print(f"\nContext packing (full runbook = {full_tokens} tokens)")
for K in [1, 2, 3]:
    hit = 0; used = 0
    for gi, q in GOLD:
        s = sorted(range(N), key=lambda i: -cos(vec(tok(q)), dv[i]))[:K]
        hit += gi in s; used += sum(len(docs[i]) for i in s)
    print(f"  top-{K}: gold-chunk recall {hit/len(GOLD):.2f} | avg context {used/len(GOLD):.0f} tokens | {100*(1-(used/len(GOLD))/full_tokens):.0f}% fewer tokens than full runbook")
