"""End-to-end checks for every project: runs each script the way a user would
(from the repo root, which also proves the scripts work from any folder) and
asserts the headline results quoted in the README.

Run:  python -m unittest discover tests -v
"""
import os, re, subprocess, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(script):
    r = subprocess.run([sys.executable, os.path.join(ROOT, script)], cwd=ROOT,
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise AssertionError(f"{script} exited {r.returncode}\n{r.stdout}\n{r.stderr}")
    return r.stdout


def num(pattern, text):
    m = re.search(pattern, text)
    if not m:
        raise AssertionError(f"pattern {pattern!r} not found in output:\n{text}")
    return float(m.group(1))


class Portfolio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p1 = run("p1_bordereaux/pipeline.py")  # p2 and p5 read p1's output

    def test_p1_standardises_all_partner_rows(self):
        self.assertIn("(927, 6)", self.p1)

    def test_p2_controls_catch_every_injected_issue(self):
        out = run("p2_dq_controls/dq_checks.py")
        self.assertEqual(num(r"Injected issues: (\d+)", out), 90)
        self.assertEqual(num(r"precision ([\d.]+)", out), 1.0)
        self.assertEqual(num(r"recall ([\d.]+)", out), 1.0)
        unexplained = [abs(float(line.split()[-1])) for line in out.splitlines()
                       if line.strip().startswith(("AlphaIns", "BetaCover", "GammaRisk"))]
        self.assertEqual(len(unexplained), 3)
        self.assertTrue(all(u < 0.01 for u in unexplained), unexplained)

    def test_p4_triage_accuracy_and_ref_extraction(self):
        out = run("p4_complaints_triage/triage.py")
        self.assertGreaterEqual(num(r"Overall accuracy \(no review\): ([\d.]+)", out), 0.95)
        self.assertEqual(num(r"booking-ref extraction agreement ([\d.]+)", out), 1.0)

    def test_p5_mcp_server_end_to_end(self):
        self.assertIn("ALL MCP TESTS PASSED", run("p5_mcp_server/test_client.py"))

    def test_p6_rl_router_beats_keyword_baseline(self):
        out = run("p6_agent_harness_eval/harness.py")
        baseline = num(r"keyword-rule baseline\s+: ([\d.]+)", out)
        rl = num(r"REINFORCE policy\s+: ([\d.]+)", out)
        self.assertGreater(rl, baseline)

    def test_p7_hooks(self):
        self.assertIn("6/6 hook tests passed", run("p7_claude_code_skill/test_hooks.py"))


if __name__ == "__main__":
    unittest.main()
