import json
from pathlib import Path

from review_gate.benchmark import run_benchmark
from review_gate.diff import added_lines
from review_gate.rules import run_static_rules


def test_diff_tracks_added_line_numbers():
    diff = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -2,2 +2,3 @@
 same
+password = "super-secret-value"
 end
"""
    lines = added_lines(diff)
    assert [(line.file, line.line) for line in lines] == [("a.py", 3)]


def test_static_gate_detects_blocking_security_issue():
    diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -0,0 +1 @@
+db.query("SELECT * FROM users WHERE id=" + user_id)
"""
    findings = run_static_rules(added_lines(diff))
    assert [(item.rule_id, item.severity) for item in findings] == [("SEC002", "blocking")]


def test_benchmark_meets_project_target():
    result = run_benchmark(Path("benchmark/cases.json"))
    assert result["detection_rate"] >= 0.9
    assert result["false_positive_rate"] < 0.1

