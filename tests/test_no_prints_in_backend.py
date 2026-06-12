from ast import Call, Name, walk, parse
from pathlib import Path


def test_no_print_calls_in_backend_source_tree():
    findings = []
    for path in Path("app/backend").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        tree = parse(path.read_text(encoding="utf-8"))
        for node in walk(tree):
            if isinstance(node, Call) and isinstance(node.func, Name) and node.func.id == "print":
                findings.append(f"{path.as_posix()}:{node.lineno}: print() call")

    assert findings == [], "print() calls found in app/backend:\n" + "\n".join(findings)
