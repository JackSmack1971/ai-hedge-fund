from pathlib import Path
import re


def test_no_bare_except_in_source_tree():
    source_roots = [Path("src"), Path("app")]
    bare_except_pattern = re.compile(r"^\s*except:\s*$")
    findings = []

    for root in source_roots:
        for path in root.rglob("*.py"):
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if bare_except_pattern.match(line):
                    findings.append(f"{path.as_posix()}:{line_number}: {line.strip()}")

    assert findings == [], "Bare except clauses found:\n" + "\n".join(findings)
