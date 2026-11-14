#!/usr/bin/env python3
"""PostToolUse hook: after an edit to a .py file, syntax-check it; exit 2 feeds the error back to the agent."""
import json, sys, py_compile
try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)
path = (payload.get("tool_input") or {}).get("file_path", "") or ""
if path.endswith(".py"):
    try:
        py_compile.compile(path, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"Syntax error after edit: {e.msg}", file=sys.stderr); sys.exit(2)
sys.exit(0)
