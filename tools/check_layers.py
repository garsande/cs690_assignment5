"""Checks the layer rules of the backend in app/.

    python tools/check_layers.py

L1  SQL lives in app/repository.py: no other module in app/ imports sqlite3 or holds
    SQL text (SELECT ... FROM, INSERT INTO, UPDATE ... SET, DELETE FROM, CREATE TABLE).
L2  HTTP lives in app/routes.py and app/main.py: no other module imports fastapi or
    starlette.
L3  app/routes.py does not import app.repository: routes call the service.
L4  The five modules exist, and app/main.py defines create_app.
L5  No ORM or other database library anywhere in app/.

Exit code 0 when every rule holds, 1 otherwise. The grader runs its own copy of this
file, so changing this copy changes nothing.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REQUIRED = ["main.py", "routes.py", "service.py", "repository.py", "models.py"]
HTTP_ALLOWED = {"routes.py", "main.py"}
HTTP_LIBS = {"fastapi", "starlette"}
DB_LIBS = {"sqlalchemy", "sqlmodel", "peewee", "tortoise", "pony", "aiosqlite", "databases", "orm"}
SQL = re.compile(
    r"\bselect\b[^;]*?\bfrom\s+\w+|\binsert\s+into\b|\bupdate\s+\w+\s+set\b|\bdelete\s+from\b|\bcreate\s+table\b",
    re.IGNORECASE | re.DOTALL,
)


def imported_modules(tree: ast.AST) -> list[tuple[str, int]]:
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [(alias.name, node.lineno) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = "." * node.level + (node.module or "")
            found.append((base, node.lineno))
            if node.module is None:
                found += [("." * node.level + alias.name, node.lineno) for alias in node.names]
    return found


def docstring_nodes(tree: ast.AST) -> set[int]:
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                ids.add(id(body[0].value))
    return ids


def sql_strings(tree: ast.AST) -> list[int]:
    skip = docstring_nodes(tree)
    lines = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            if SQL.search(node.value):
                lines.append(node.lineno)
    return lines


def check(root: Path) -> list[str]:
    app = root / "app"
    problems: list[str] = []
    if not app.is_dir():
        return ["L4: there is no app/ folder"]
    for name in REQUIRED:
        if not (app / name).is_file():
            problems.append(f"L4: app/{name} is missing")
    for path in sorted(app.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except SyntaxError as err:
            problems.append(f"L4: {rel} does not parse: {err}")
            continue
        is_repo = rel == "app/repository.py"
        top = path.relative_to(app).as_posix()
        for module, line in imported_modules(tree):
            first = module.lstrip(".").split(".")[0]
            if first == "sqlite3" and not is_repo:
                problems.append(f"L1: {rel}:{line} imports sqlite3; only app/repository.py may")
            if first in HTTP_LIBS and top not in HTTP_ALLOWED:
                problems.append(f"L2: {rel}:{line} imports {first}; only app/routes.py and app/main.py may")
            if first in DB_LIBS:
                problems.append(f"L5: {rel}:{line} imports {first}; use sqlite3 in app/repository.py only")
            if top == "routes.py" and (module in ("app.repository", ".repository") or module.endswith(".repository") or module == "repository"):
                problems.append(f"L3: {rel}:{line} imports the repository; routes must call the service")
        if not is_repo:
            for line in sql_strings(tree):
                problems.append(f"L1: {rel}:{line} contains SQL; only app/repository.py may")
        if rel == "app/main.py":
            names = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            if "create_app" not in names:
                problems.append("L4: app/main.py does not define create_app")
    return problems


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    problems = check(root)
    if problems:
        print("Layer check FAILED:")
        for p in problems:
            print("  " + p)
        return 1
    print("Layer check passed: L1 to L5 hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
