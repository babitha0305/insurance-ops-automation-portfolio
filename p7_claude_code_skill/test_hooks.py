"""Tests the hook scripts by feeding them the JSON Claude Code sends on stdin."""
import json, subprocess, sys, tempfile, os
def run(script, payload):
    r = subprocess.run([sys.executable, f".claude/hooks/{script}"], input=json.dumps(payload), capture_output=True, text=True)
    return r.returncode, r.stderr.strip()
cases = [
 ("block_protected.py", {"tool_name":"Write","tool_input":{"file_path":"p1_bordereaux/data_AlphaIns.csv"}}, 2),
 ("block_protected.py", {"tool_name":"Edit","tool_input":{"file_path":"p1_bordereaux/truth.json"}}, 2),
 ("block_protected.py", {"tool_name":"Write","tool_input":{"file_path":".env"}}, 2),
 ("block_protected.py", {"tool_name":"Write","tool_input":{"file_path":"p2_dq_controls/dq_checks.py"}}, 0),
]
bad = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False); bad.write("def f(:\n  pass"); bad.close()
good = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False); good.write("x = 1\n"); good.close()
cases += [("post_edit_check.py", {"tool_input":{"file_path":bad.name}}, 2), ("post_edit_check.py", {"tool_input":{"file_path":good.name}}, 0)]
ok = 0
for s, p, want in cases:
    code, err = run(s, p); ok += code == want
    print(f"{s:20} {p['tool_input']['file_path'][-28:]:28} exit={code} expected={want} {'OK' if code==want else 'FAIL'}")
print(f"{ok}/{len(cases)} hook tests passed"); os.unlink(bad.name); os.unlink(good.name)
