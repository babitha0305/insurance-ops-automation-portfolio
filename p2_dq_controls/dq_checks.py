"""Reusable data-quality controls + ledger reconciliation for standardised bordereaux.
Run:  python dq_checks.py   (expects ../p1_bordereaux/out/standardised.csv and truth.json)"""
import json, os, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))  # so the script runs from any folder
P1 = os.path.join(HERE, "..", "p1_bordereaux", "")
VALID_CCY = {"GBP"}

def check_duplicates(df):  return df[df.duplicated(["partner","ref"], keep="first")][["partner","ref"]].assign(issue="duplicate")
def check_missing(df, cols=("name","date")):
    m = df[list(cols)].isna().any(axis=1); return df[m][["partner","ref"]].assign(issue="missing")
def check_schema(df):      return df[~df["ccy"].isin(VALID_CCY)][["partner","ref"]].assign(issue="schema")
def check_financial(df):   return df[df["prem"] <= 0][["partner","ref"]].assign(issue="financial")

def run_all(df):
    return pd.concat([check_duplicates(df), check_missing(df), check_schema(df), check_financial(df)], ignore_index=True)

def reconcile(df, flags, ledger):
    """Per partner: variance vs ledger, then how much is explained by duplicates and sign-flipped premiums."""
    rows = []
    for p, g in df.groupby("partner"):
        led = ledger[p]
        raw = round(g["prem"].sum(), 2)
        dups = round(g[g.duplicated("ref", keep="first")]["prem"].sum(), 2)
        dedup = g.drop_duplicates("ref")
        neg_effect = round(2 * dedup.loc[dedup["prem"] <= 0, "prem"].sum(), 2)  # a sign flip shifts the total by 2x
        unexplained = round(raw - led - dups - neg_effect, 2)
        rows.append({"partner": p, "ledger": led, "raw_total": raw, "variance": round(raw-led, 2),
                     "from_duplicates": dups, "from_negative_premiums": neg_effect, "unexplained": unexplained})
    return pd.DataFrame(rows)

if __name__ == "__main__":
    df = pd.read_csv(P1 + "out/standardised.csv")
    truth = json.load(open(P1 + "truth.json"))
    flags = run_all(df)
    flags.to_csv(os.path.join(HERE, "flagged_records.csv"), index=False)
    actual = {(t["partner"], i[0], i[1]) for t in truth for i in t["issues"]}
    pred = {(r.partner, r.issue, r.ref) for r in flags.itertuples()}
    tp = len(actual & pred); prec = tp/len(pred); rec = tp/len(actual)
    print(f"Injected issues: {len(actual)} | flagged: {len(pred)} | precision {prec:.3f} recall {rec:.3f}")
    print(flags["issue"].value_counts().to_string())
    ledger = {t["partner"]: t["ledger_total"] for t in truth}
    print(reconcile(df, flags, ledger).to_string(index=False))
