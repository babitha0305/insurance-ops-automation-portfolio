"""MCP server exposing the bordereau data-quality controls as tools an AI agent can call.
Run:  python server.py   (stdio transport)"""
import sys, json, os
import pandas as pd
from mcp.server.fastmcp import FastMCP

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "p2_dq_controls"))
import dq_checks  # reuse the controls from project 2

DATA = os.path.join(HERE, "..", "p1_bordereaux")
mcp = FastMCP("bordereau-controls")

def _load():
    return pd.read_csv(os.path.join(DATA, "out", "standardised.csv"))

@mcp.tool()
def run_quality_checks(partner: str = "") -> str:
    """Run duplicate/missing/schema/financial checks. Optionally limit to one partner. Returns issue counts as JSON."""
    df = _load()
    if partner: df = df[df["partner"] == partner]
    flags = dq_checks.run_all(df)
    return json.dumps({"rows_checked": len(df), "issues": flags["issue"].value_counts().to_dict()})

@mcp.tool()
def list_flagged_records(issue: str, limit: int = 5) -> str:
    """List flagged records for one issue type: duplicate, missing, schema or financial."""
    flags = dq_checks.run_all(_load())
    sel = flags[flags["issue"] == issue].head(limit)
    return sel.to_json(orient="records")

@mcp.tool()
def reconcile_to_ledger() -> str:
    """Reconcile each partner's premium total to the ledger and show how much variance duplicates and negative premiums explain."""
    truth = json.load(open(os.path.join(DATA, "truth.json")))
    ledger = {t["partner"]: t["ledger_total"] for t in truth}
    return dq_checks.reconcile(_load(), None, ledger).to_json(orient="records")

@mcp.resource("bordereau://summary")
def summary() -> str:
    """Quick dataset summary."""
    df = _load()
    return f"{len(df)} rows, partners: {sorted(df['partner'].unique())}"

if __name__ == "__main__":
    mcp.run()
