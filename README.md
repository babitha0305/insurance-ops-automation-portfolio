# Insurance Operations Automation - Portfolio Projects
Four small projects built around insurance-ops automation. **All data is synthetic** (generated in code); no real partner or customer data.

| Project | What it does | Run |
|---|---|---|
| p1_bordereaux | Ingests 3 partner schedules with different headers/date formats and standardises them | `python generate_data.py && python pipeline.py` |
| p2_dq_controls | Flags duplicates, missing fields, schema errors, financial mismatches; reconciles totals to a ledger | `python dq_checks.py` (after p1) |
| p3_apps_script | Google Apps Script validator for a Sheet (highlights rows, Exceptions tab, optional email) | Import `test_upload.csv` into a Sheet tab named `Upload`, paste `Code.gs` via Extensions > Apps Script, then Bordereau Controls > Run validation (tested on a live sheet: 10 rows, 7 exceptions, total premium 6700.50) |
| p4_complaints_triage | Classifies complaint emails, extracts booking refs, routes by confidence, queues low-confidence for human review | `python triage.py` |

Requirements: Python 3.10+, pandas, scikit-learn.
Limitations: synthetic data with injected errors, so perfect detection scores reflect the test setup, not real-world performance. The triage classifier is TF-IDF + logistic regression; an LLM can replace it.

## Added for AI-agent roles
| p5_mcp_server | MCP server exposing the controls as tools/resource; stdio client test | `pip install "mcp<2"` then `python test_client.py` |
| p6_agent_harness_eval | Tool-routing eval pipeline, REINFORCE router vs keyword baseline, TF-IDF context packing | `python harness.py` |
| p7_claude_code_skill | Claude Code skill + PreToolUse/PostToolUse hooks (scripts tested standalone; not yet exercised inside Claude Code) | `python test_hooks.py` |
Note: p6 uses synthetic, easily separable queries, so 100% reflects the toy setup. No LLM SFT/RL was run in these projects.
