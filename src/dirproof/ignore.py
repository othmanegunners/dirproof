"""Read user-supplied exclusion patterns from a UTF-8 text file."""
from __future__ import annotations

from pathlib import Path


def read_exclusion_patterns(path: str | Path) -> list[str]:
    """Read one glob per line; ignore empty lines and # comments.

    Patterns are matched against POSIX-style paths relative to the scanned root.
    Existing .gitignore syntax, negation patterns, and anchored patterns are
    deliberately *not* supported.
    """
    contents = Path(path).expanduser().read_text(encoding='utf-8-sig')
    patterns = []
    for line in contents.splitlines():
        pattern = line.strip()
        if pattern and not pattern.startswith('#') and pattern not in patterns:
            patterns.append(pattern)
    return patterns
