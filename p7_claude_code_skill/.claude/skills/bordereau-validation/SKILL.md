---
name: bordereau-validation
description: Validate and reconcile monthly insurance bordereau CSVs. Use when asked to check partner schedules for duplicates, missing fields, schema errors, negative premiums, or to reconcile totals to a ledger.
---

# Bordereau validation

1. Standardise headers and dates first (see p1_bordereaux/pipeline.py); never validate raw partner files directly.
2. Run the controls in p2_dq_controls/dq_checks.py: duplicates, missing name/date, currency not GBP, premium <= 0.
3. Reconcile per partner to the ledger and report variance explained by duplicates and sign flips.
4. Report counts by issue type and list up to 5 example refs per type. Anything unexplained above £1 is escalated, not silently fixed.
5. Never overwrite source files; write results to a new CSV.
