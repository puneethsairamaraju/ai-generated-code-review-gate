from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from .benchmark import run_benchmark
from .diff import added_lines
from .llm import review_with_provider
from .models import ReviewReport
from .report import markdown, write_json
from .rules import run_static_rules


def _git_diff(base: str, head: str) -> str:
    result = subprocess.run(
        ["git", "diff", "--unified=3", f"{base}...{head}"],
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git diff failed")
    return result.stdout


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-review-gate")
    sub = parser.add_subparsers(dest="command", required=True)
    review = sub.add_parser("review", help="Review a diff and fail on blocking findings")
    source = review.add_mutually_exclusive_group(required=True)
    source.add_argument("--diff", type=Path, help="Path to a unified diff, or - for stdin")
    source.add_argument("--base", help="Base git revision (used with --head)")
    review.add_argument("--head", default="HEAD")
    review.add_argument("--rubric", type=Path, default=Path("rubric.json"))
    review.add_argument("--llm", action="store_true", help="Enable the selected AI rubric reviewer")
    review.add_argument("--provider", choices=["openai", "gemini"], default="openai")
    review.add_argument("--model", help="Provider model ID")
    review.add_argument("--output", type=Path, default=Path("review-report.json"))
    review.add_argument("--markdown", type=Path)
    bench = sub.add_parser("benchmark", help="Measure deterministic rule performance")
    bench.add_argument("--cases", type=Path, default=Path("benchmark/cases.json"))
    bench.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "benchmark":
        result = run_benchmark(args.cases)
        rendered = json.dumps(result, indent=2)
        print(rendered)
        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        return int(result["detection_rate"] < 0.9 or result["false_positive_rate"] >= 0.1)

    args.model = args.model or ("gemini-3.8-flash" if args.provider == "gemini" else "gpt-5-mini")
    try:
        if args.diff:
            diff_text = sys.stdin.read() if str(args.diff) == "-" else args.diff.read_text(encoding="utf-8")
        else:
            diff_text = _git_diff(args.base, args.head)
        findings = run_static_rules(added_lines(diff_text))
        rubric_results: list[dict] = []
        if args.llm:
            llm_findings, rubric_results = review_with_provider(diff_text, args.rubric, args.model, args.provider)
            findings.extend(llm_findings)
        report = ReviewReport(
            passed=not any(item.severity == "blocking" for item in findings),
            findings=findings,
            rubric_results=rubric_results,
            metadata={"llm_enabled": args.llm, "provider": args.provider if args.llm else None, "model": args.model if args.llm else None},
        )
        write_json(report, args.output)
        rendered = markdown(report)
        print(rendered)
        if args.markdown:
            args.markdown.write_text(rendered + "\n", encoding="utf-8")
        return 0 if report.passed else 1
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ai-review-gate: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

