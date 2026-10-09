"""Strict unified-diff parser; malformed/unsupported input never silently passes."""
from dataclasses import dataclass
import ast
import re

@dataclass(frozen=True)
class AddedLine:
    file: str
    line: int
    text: str

_HUNK = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?:.*)$')


def added_lines(diff_text: str) -> list[AddedLine]:
    if not diff_text.strip():
        return []
    current_file = None
    old_left = new_left = 0
    new_line = 0
    in_hunk = False
    seen_file = False
    result = []
    for raw in diff_text.splitlines():
        if in_hunk and (old_left or new_left):
            if raw.startswith('\\ No newline at end of file'):
                continue
            prefix = raw[:1]
            if prefix not in (' ', '+', '-'):
                raise RuntimeError('Malformed diff: incomplete hunk')
            if prefix in (' ', '-'):
                old_left -= 1
            if prefix in (' ', '+'):
                new_left -= 1
            if old_left < 0 or new_left < 0:
                raise RuntimeError('Malformed diff: hunk length mismatch')
            if prefix == '+':
                if current_file is None:
                    raise RuntimeError('Malformed diff: added line without a file')
                result.append(AddedLine(current_file, new_line, raw[1:]))
            if prefix in (' ', '+'):
                new_line += 1
            continue
        in_hunk = False
        if raw.startswith('diff --git '):
            seen_file = True
            current_file = None
        elif raw.startswith('+++ '):
            value = raw[4:]
            if value.startswith('"'):
                try:
                    value = ast.literal_eval(value)
                except (ValueError, SyntaxError) as exc:
                    raise RuntimeError('Malformed quoted path') from exc
            if value == '/dev/null':
                current_file = None
            elif value.startswith('b/'):
                current_file = value[2:]
            else:
                raise RuntimeError('Unsupported diff path; use git diff')
        elif raw.startswith('@@'):
            match = _HUNK.fullmatch(raw)
            if not match or not seen_file:
                raise RuntimeError('Malformed or combined diff hunk')
            old_left = int(match[2] or 1)
            new_line = int(match[3])
            new_left = int(match[4] or 1)
            in_hunk = True
        elif raw.startswith(('GIT binary patch', 'Binary files', 'diff --cc', 'diff --combined')):
            raise RuntimeError('Binary and combined diffs require manual review')
        elif raw.startswith(('index ', '--- ', 'new file mode ', 'deleted file mode ',
                             'old mode ', 'new mode ', 'similarity index ', 'rename from ',
                             'rename to ', 'copy from ', 'copy to ', 'dissimilarity index ',
                             '\\ No newline at end of file')) or not raw:
            continue
        else:
            raise RuntimeError('Malformed diff: unexpected content outside hunk')
    if old_left or new_left:
        raise RuntimeError('Malformed diff: truncated hunk')
    if not seen_file:
        raise RuntimeError('Input is not a git unified diff')
    return result
