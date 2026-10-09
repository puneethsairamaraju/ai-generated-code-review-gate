from __future__ import annotations

from dataclasses import dataclass
import re

from .diff import AddedLine
from .models import Finding, Severity


@dataclass(frozen=True)
class Rule:
    rule_id: str
    title: str
    pattern: re.Pattern[str]
    severity: Severity
    reasoning: str
    exclude: re.Pattern[str] | None = None


RULES = (
    Rule(
        "SEC001", "Possible hardcoded secret",
        re.compile(r"(?i)\b(api[_-]?key|secret|password|token)\b\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
        "blocking",
        "Secrets in source code can leak through version control and build artifacts.",
        re.compile(r"(?i)(example|dummy|test|fake|changeme|your[_-])"),
    ),
    Rule(
        "SEC002", "Possible SQL injection",
        re.compile(r"(?i)(execute|query)\s*\(\s*(f['\"]|['\"].*(\+|%s|\.format\())"),
        "blocking",
        "SQL assembled from strings may allow attacker-controlled input to change the query.",
    ),
    Rule(
        "SEC003", "Dangerous dynamic execution",
        re.compile(r"\b(eval|exec)\s*\("),
        "blocking",
        "Dynamic execution can turn untrusted input into arbitrary code execution.",
    ),
    Rule(
        "SEC004", "Insecure TLS verification disabled",
        re.compile(r"\bverify\s*=\s*False\b"),
        "blocking",
        "Disabling certificate verification enables man-in-the-middle attacks.",
    ),
    Rule(
        "ERR001", "Empty exception handler",
        re.compile(r"^\s*(except\b[^:]*:\s*pass\s*$|catch\s*\([^)]*\)\s*\{\s*\})"),
        "advisory",
        "Swallowed exceptions hide failures and make production incidents difficult to diagnose.",
    ),
    Rule(
        "ERR002", "Overly broad exception handling",
        re.compile(r"^\s*except\s*(Exception)?\s*:\s*$"),
        "advisory",
        "Catching every exception can hide programming errors; catch expected failures explicitly.",
    ),
    Rule(
        "QUAL001", "Debug statement added",
        re.compile(r"\b(print\s*\(|console\.log\s*\()"),
        "advisory",
        "Debug output can expose data or add noise in production; use structured logging.",
    ),
)


def run_static_rules(lines: list[AddedLine]) -> list[Finding]:
    findings: list[Finding] = []
    for line in lines:
        for rule in RULES:
            if rule.pattern.search(line.text) and not (
                rule.exclude and rule.exclude.search(line.text)
            ):
                findings.append(Finding(
                    rule_id=rule.rule_id,
                    title=rule.title,
                    severity=rule.severity,
                    file=line.file,
                    line=line.line,
                    evidence=line.text.strip()[:240],
                    reasoning=rule.reasoning,
                ))
    return findings
