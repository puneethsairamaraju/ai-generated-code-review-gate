from __future__ import annotations

import json
from pathlib import Path

from .models import ReviewReport


def write_json(report: ReviewReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")


def markdown(report: ReviewReport) -> str:
    status = "PASS" if report.passed else "FAIL"
    counts = report.to_dict()["summary"]
    lines = [
        f"# AI Review Gate: {status}",
        "",
        f"**{counts['blocking']} blocking** | {counts['advisory']} advisory",
        "",
    ]
    if not report.findings:
        lines.append("No findings.")
    for finding in report.findings:
        icon = "[BLOCK]" if finding.severity == "blocking" else "[WARN]"
        lines.extend([
            f"## {icon} {finding.rule_id}: {finding.title}",
            "",
            f"`{finding.file}:{finding.line}` | **{finding.severity}** | {finding.source}",
            "",
            finding.reasoning,
            "",
            f"> {finding.evidence}",
            "",
        ])
    return "\n".join(lines)
