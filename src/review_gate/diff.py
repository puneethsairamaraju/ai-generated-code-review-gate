from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class AddedLine:
    file: str
    line: int
    text: str


_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def added_lines(diff_text: str) -> list[AddedLine]:
    """Return added source lines from a unified git diff with new-file line numbers."""
    current_file = ""
    new_line = 0
    result: list[AddedLine] = []
    for raw in diff_text.splitlines():
        if raw.startswith("+++ b/"):
            current_file = raw[6:]
            continue
        match = _HUNK.match(raw)
        if match:
            new_line = int(match.group(1))
            continue
        if not current_file or raw.startswith(("diff --git ", "--- ")):
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            result.append(AddedLine(current_file, new_line, raw[1:]))
            new_line += 1
        elif raw.startswith("-"):
            continue
        elif not raw.startswith("\\"):
            new_line += 1
    return result

