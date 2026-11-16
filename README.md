# Insurance Operations Automation - Portfolio Projects
Seven small projects built around insurance-ops automation: four core data/ops projects, plus three that expose the same controls to AI agents. **All data is synthetic** (generated in code); no real partner or customer data.

## Core insurance-ops projects
| Project | What it does | Run |
|---|---|---|
| p1_bordereaux | Ingests 3 partner schedules with different headers/date formats and standardises them | `python generate_data.py && python pipeline.py` |
| p2_dq_controls | Flags duplicates, missing fields, schema errors, financial mismatches; reconciles totals to a ledger | `python dq_checks.py` (after p1) |
| p3_apps_script | Google Apps Script validator for a Sheet (highlights rows, Exceptions tab, optional email) | Import `test_upload.csv` into a Sheet tab named `Upload`, paste `Code.gs` via Extensions > Apps Script, then Bordereau Controls > Run validation (tested on a live sheet: 10 rows, 7 exceptions, total premium 6700.50; email summary not tested) |
| p4_complaints_triage | Classifies complaint emails, extracts booking refs, routes by confidence, queues low-confidence for human review | `python triage.py` |

## AI-agent projects
| Project | What it does | Run |
|---|---|---|
| p5_mcp_server | MCP server exposing the p2 controls as 3 tools + 1 resource; stdio client test | `pip install "mcp<2"` then `python test_client.py` |
| p6_agent_harness_eval | Tool-routing eval pipeline, REINFORCE router vs keyword baseline, TF-IDF context packing | `python harness.py` |
| p7_claude_code_skill | Claude Code skill + PreToolUse/PostToolUse hooks (scripts tested standalone; not yet exercised inside Claude Code) | `python test_hooks.py` |

## Results (from running the scripts)
| Project | Result |
|---|---|
| p2 | 90 of 90 injected issues flagged, 0 false positives; ~£420K reconciled to ledger across 3 partners with £0.00 unexplained variance |
| p4 | 97.3% overall accuracy; at a 0.6 confidence threshold, 87% of emails auto-routed at 99.2% accuracy and 13% sent to human review |
| p5 | End-to-end MCP client test passes (927 rows, 90 issues, £0.00 unexplained) |
| p6 | Tool routing on 500 held-out queries: untrained 35%, keyword rules 87%, REINFORCE 100%; context packing uses 92% fewer tokens with 92% recall of the needed chunk |
| p7 | 6/6 hook tests pass |

## Requirements
Python 3.10+, pandas, scikit-learn, numpy; `mcp<2` for p5.

## Limitations
- Synthetic data with injected errors, so perfect detection scores reflect the test setup, not real-world performance.
- The triage classifier is TF-IDF + logistic regression; an LLM can replace it.
- p6 uses synthetic, easily separable queries, so 100% reflects the toy setup. No LLM SFT/RL was run in these projects.
