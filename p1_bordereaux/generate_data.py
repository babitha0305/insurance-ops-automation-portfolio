"""Generate synthetic monthly bordereaux from 3 partners with different layouts
and injected data-quality problems (ground truth saved for later evaluation)."""
import random, json, os
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))  # so the script runs from any folder
random.seed(42)
N = 300
partners = {
 "AlphaIns": {"cols": ["PolicyRef","InsuredName","InceptionDate","GrossPremium","Currency"], "datefmt": "%d/%m/%Y"},
 "BetaCover": {"cols": ["policy_no","customer","start_date","premium_gbp","ccy"], "datefmt": "%Y-%m-%d"},
 "GammaRisk": {"cols": ["Ref","Name","Inception","Premium","CCY"], "datefmt": "%d-%b-%Y"},
}
names = ["Smith Ltd","Jones & Co","Patel Travel","Brown Holidays","Khan Tours","Lee Group","Wright Stays","Evans Trips"]
truth = []
for p, cfg in partners.items():
    rows = []
    for i in range(N):
        ref = f"{p[:2].upper()}{100000+i}"
        d = pd.Timestamp("2026-10-01") + pd.Timedelta(days=random.randint(0,29))
        prem = round(random.uniform(20,900),2)
        rows.append([ref, random.choice(names), d, prem, "GBP"])
    df = pd.DataFrame(rows, columns=["ref","name","date","prem","ccy"])
    ledger_total = round(df["prem"].sum(),2)
    issues = []
    for idx in random.sample(range(N), 9):   # duplicates
        issues.append(("duplicate", df.iloc[idx]["ref"]))
        df = pd.concat([df, df.iloc[[idx]]])
    df = df.reset_index(drop=True)
    for idx in random.sample(range(N), 10):  # missing fields
        col = random.choice(["name","date"]); df.loc[idx,col] = None; issues.append(("missing", df.loc[idx,"ref"]))
    for idx in random.sample(range(N), 6):   # bad currency
        df.loc[idx,"ccy"] = random.choice(["EUR","GBPP","???"]); issues.append(("schema", df.loc[idx,"ref"]))
    for idx in random.sample(range(N), 5):   # negative premium
        df.loc[idx,"prem"] = -abs(df.loc[idx,"prem"]); issues.append(("financial", df.loc[idx,"ref"]))
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime(cfg["datefmt"])
    out.columns = cfg["cols"]
    out.to_csv(os.path.join(HERE, f"data_{p}.csv"), index=False)
    truth.append({"partner":p,"ledger_total":ledger_total,"issues":issues})
json.dump(truth, open(os.path.join(HERE, "truth.json"),"w"), default=str, indent=1)
print("generated", len(partners), "partner files")
