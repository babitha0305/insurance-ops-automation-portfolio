#!/usr/bin/env python3
"""PreToolUse hook: block edits to raw partner data, ledger truth files and secrets.
Claude Code passes the tool call as JSON on stdin; exit code 2 blocks the call and sends stderr back to the agent."""
import json, sys, re
PROTECTED = [r"(^|/)data_[^/]+\.csv$", r"(^|/)truth\.json$", r"(^|/)\.env", r"(^|/)secrets?/"]
try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)
path = (payload.get("tool_input") or {}).get("file_path", "") or ""
for pat in PROTECTED:
    if re.search(pat, path):
        print(f"Blocked: {path} is protected source data. Write outputs to a new file instead.", file=sys.stderr)
        sys.exit(2)
sys.exit(0)
