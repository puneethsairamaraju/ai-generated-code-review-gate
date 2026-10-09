from __future__ import annotations

import json
from pathlib import Path

from .diff import added_lines
from .rules import run_static_rules


def run_benchmark(path: Path) -> dict:
    cases = json.loads(path.read_text(encoding="utf-8"))
    true_positive = false_negative = false_positive = true_negative = 0
    details = []
    for case in cases:
        diff = f"diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1,0 +1,1 @@\n+{case['code']}\n"
        detected = {finding.rule_id for finding in run_static_rules(added_lines(diff))}
        expected = set(case["expected_rules"])
        caught = expected.issubset(detected) if expected else not detected
        if expected and caught:
            true_positive += 1
        elif expected:
            false_negative += 1
        elif detected:
            false_positive += 1
        else:
            true_negative += 1
        details.append({"id": case["id"], "passed": caught, "expected": sorted(expected), "detected": sorted(detected)})
    positive = true_positive + false_negative
    negative = true_negative + false_positive
    return {
        "cases": len(cases),
        "detection_rate": true_positive / positive if positive else 1.0,
        "false_positive_rate": false_positive / negative if negative else 0.0,
        "confusion_matrix": {
            "true_positive": true_positive, "false_negative": false_negative,
            "false_positive": false_positive, "true_negative": true_negative,
        },
        "details": details,
    }
