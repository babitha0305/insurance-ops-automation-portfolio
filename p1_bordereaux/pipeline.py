"""Monthly bordereaux pipeline: ingest -> standardise -> cleanse -> reconcile."""
import json, glob, os
import pandas as pd

CANON = {"policyref":"ref","policy_no":"ref","ref":"ref",
         "insuredname":"name","customer":"name","name":"name",
         "inceptiondate":"date","start_date":"date","inception":"date",
         "grosspremium":"prem","premium_gbp":"prem","premium":"prem",
         "currency":"ccy","ccy":"ccy"}
DATE_FORMATS = ["%d/%m/%Y","%Y-%m-%d","%d-%b-%Y"]

def parse_date(s):
    for f in DATE_FORMATS:
        try: return pd.to_datetime(s, format=f)
        except Exception: pass
    return pd.NaT

def ingest(path):
    partner = os.path.basename(path)[5:-4]
    df = pd.read_csv(path)
    df.columns = [CANON[c.strip().lower()] for c in df.columns]
    df["partner"] = partner
    df["date"] = df["date"].map(lambda s: parse_date(s) if pd.notna(s) else pd.NaT)
    df["name"] = df["name"].astype("string").str.strip()
    return df

def run(outdir="out"):
    os.makedirs(outdir, exist_ok=True)
    raw = pd.concat([ingest(p) for p in sorted(glob.glob("data_*.csv"))], ignore_index=True)
    raw.to_csv(f"{outdir}/standardised.csv", index=False)
    return raw

if __name__ == "__main__":
    df = run(); print(df.shape); print(df.head(3))
