from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

Severity = Literal["blocking", "advisory"]


@dataclass(frozen=True)
class Finding:
    rule_id: str
    title: str
    severity: Severity
    file: str
    line: int
    evidence: str
    reasoning: str
    source: str = "static"


@dataclass
class ReviewReport:
    passed: bool
    findings: list[Finding] = field(default_factory=list)
    rubric_results: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "summary": {
                "blocking": sum(f.severity == "blocking" for f in self.findings),
                "advisory": sum(f.severity == "advisory" for f in self.findings),
                "total": len(self.findings),
            },
            "findings": [asdict(f) for f in self.findings],
            "rubric_results": self.rubric_results,
            "metadata": self.metadata,
        }

