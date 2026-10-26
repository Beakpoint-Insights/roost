#!/usr/bin/env python3
"""Turns `claude plugin eval --json` result files into a Markdown table for a PR.

Usage: scripts/eval-summary.py <dir of result .json files>
"""
import glob
import json
import os
import sys

rows = []
for path in sorted(glob.glob(os.path.join(sys.argv[1], "*.json"))):
    with open(path) as f:
        result = json.load(f)
    for case in result.get("cases", []):
        runs = case["arms"].get("with", [])
        passed = sum(1 for r in runs if r["passed"])
        failing = sorted({g["name"] for r in runs for g in r["graders"] if g.get("scored") and not g["passed"]})
        score = case.get("aggregates", {}).get("score", 0)
        mark = "✅" if runs and passed == len(runs) else "❌"
        rows.append(f"| {mark} | `{case['name']}` | {passed} of {len(runs)} | {score:.2f} | {', '.join(failing) or ''} |")

print("### Evals\n")
if not rows:
    print("No eval cases ran.")
else:
    print("| | Case | Runs passed | Score | Failing graders |")
    print("|---|---|---|---|---|")
    print("\n".join(rows))
