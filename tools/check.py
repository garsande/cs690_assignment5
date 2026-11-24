"""Self-check for Assignment 5. Run it from the folder that holds HANDOUT.md.

    python tools/check.py setup    Part 0: your environment
    python tools/check.py tests    Part 4: your acceptance tests, rule by rule
    python tools/check.py          everything the grader checks by script

It reports; it never changes your files. The grader runs its own copy of these checks
plus hidden tests, so a pass here is a good sign, not a promise.
"""

from __future__ import annotations

import ast
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

LOCK_TAG = "a5-tests-locked"
SUBMIT_TAG = "a5-submit"
RULES = [f"R{n}" for n in range(1, 11)]
AGENTS = ["test-writer", "reviewer", "contract-checker"]
WRITE_TOOLS = {"edit", "write", "bash", "notebookedit", "multiedit", "replace_file_content",
               "write_to_file", "run_command", "edit_file", "create_file"}
EDIT_TOOLS = {"edit", "write", "multiedit", "replace_file_content", "write_to_file", "edit_file", "create_file"}
RUN_TOOLS = {"bash", "run_command"}
LEDGER_FIELDS = ["artifact", "tool", "prompts", "review", "checks", "evidence", "risk"]
TEST_NAME = re.compile(r"^test_r(\d+)_", re.IGNORECASE)
R11_MARKER = "R11. Daily limit"


# ---------------------------------------------------------------- helpers

def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def git_out(root: Path, *args: str) -> str:
    proc = git(root, *args)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def has_rev(root: Path, rev: str) -> bool:
    return git(root, "rev-parse", "-q", "--verify", rev + "^{commit}").returncode == 0


def files_at(root: Path, rev: str, path: str) -> list[str]:
    out = git_out(root, "ls-tree", "-r", "--name-only", rev, "--", path)
    return [line for line in out.splitlines() if line]


def show(root: Path, rev: str, path: str) -> str | None:
    proc = git(root, "show", f"{rev}:./{path}")
    return proc.stdout if proc.returncode == 0 else None


def first_commit_with(root: Path, text: str, path: str, upto: str = "HEAD") -> str | None:
    """Oldest commit (following first parents up to `upto`) in which a file under `path`
    contains `text`."""
    for sha in git_out(root, "rev-list", "--reverse", "--first-parent", upto).splitlines():
        if git(root, "grep", "-q", "-F", text, sha, "--", path).returncode == 0:
            return sha
    return None


def is_strict_ancestor(root: Path, a: str, b: str) -> bool:
    return a != b and git(root, "merge-base", "--is-ancestor", a, b).returncode == 0


def export_rev(root: Path, rev: str, dest: Path) -> None:
    """Write the files of commit `rev` into dest (no .git)."""
    data = subprocess.run(["git", "-C", str(root), "archive", "--format=tar", rev, "."],
                          capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        try:
            tar.extractall(dest, filter="data")
        except TypeError:  # Python before 3.11.4
            tar.extractall(dest)


def run_pytest(folder: Path, targets: list[str], ini: Path | None = None, timeout: int = 600) -> dict:
    """Run pytest in folder. Returns {"ok": bool, "tests": {nodeid: "passed"|"failed"|"skipped"},
    "summary": str}."""
    xml = Path(tempfile.mkdtemp()) / "r.xml"
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml", str(xml)]
    if ini is not None:
        cmd += ["-c", str(ini), "--rootdir", str(folder)]
    cmd += targets
    env = {**__import__("os").environ, "PYTHONPATH": str(folder), "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        proc = subprocess.run(cmd, cwd=folder, capture_output=True, text=True, timeout=timeout, env=env)
        out = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        return {"ok": False, "tests": {}, "summary": f"timed out after {timeout} s"}
    tests: dict[str, str] = {}
    if xml.is_file():
        try:
            for case in ET.parse(xml).getroot().iter("testcase"):
                node = f"{case.get('classname', '')}::{case.get('name', '')}"
                if case.find("failure") is not None or case.find("error") is not None:
                    tests[node] = "failed"
                elif case.find("skipped") is not None:
                    tests[node] = "skipped"
                else:
                    tests[node] = "passed"
        except ET.ParseError:
            pass
    lines = [l for l in out.strip().splitlines() if l.strip()]
    summary = lines[-1] if lines else "no output"
    shutil.rmtree(xml.parent, ignore_errors=True)
    return {"ok": bool(tests) and all(v != "failed" for v in tests.values()), "tests": tests, "summary": summary}


def count(tests: dict, state: str) -> int:
    return sum(1 for v in tests.values() if v == state)


def collected_names(folder: Path, target: str) -> list[str]:
    """Test function names (without parameters) collected under target."""
    env = {**__import__("os").environ, "PYTHONPATH": str(folder), "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", target],
                          cwd=folder, capture_output=True, text=True, env=env, timeout=300)
    names = []
    for line in proc.stdout.splitlines():
        if "::" in line:
            names.append(line.split("::")[-1].split("[")[0].strip())
    return names


def per_rule(names: list[str]) -> dict[str, int]:
    counts = {r: 0 for r in [f"R{n}" for n in range(1, 12)]}
    for name in names:
        m = TEST_NAME.match(name)
        if m and f"R{m.group(1)}" in counts:
            counts[f"R{m.group(1)}"] += 1
    return counts


# ---------------------------------------------------------------- agent files

def parse_frontmatter(text: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    data: dict = {}
    key = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        item = re.match(r"^\s*-\s*(.+?)\s*$", line)
        if item and key:
            if not isinstance(data.get(key), list):
                data[key] = []
            data[key].append(item.group(1).strip("'\""))
            continue
        kv = re.match(r"^([A-Za-z][\w-]*)\s*:\s*(.*?)\s*$", line)
        if kv:
            key, value = kv.group(1), kv.group(2)
            data[key] = value
    tools = data.get("tools")
    if isinstance(tools, str):
        data["tools"] = [t.strip().strip("'\"") for t in tools.strip("[]").split(",") if t.strip()]
    return data


def find_agent(root: Path, name: str) -> Path | None:
    for path in (root / ".claude" / "agents" / f"{name}.md",
                 root / ".agents" / "agents" / f"{name}.md",
                 root / ".agents" / "agents" / name / "agent.md"):
        if path.is_file():
            return path
    return None


def check_agent(root: Path, name: str) -> tuple[bool, bool, str]:
    """(file_ok, tools_ok, note)."""
    path = find_agent(root, name)
    if path is None:
        return False, False, f"{name}: no file in .claude/agents/ or .agents/agents/"
    meta = parse_frontmatter(path.read_text(encoding="utf-8"))
    rel = path.relative_to(root).as_posix()
    body = path.read_text(encoding="utf-8").split("---", 2)[-1].strip() if meta else ""
    file_ok = meta.get("name") == name and bool(str(meta.get("description", "")).strip()) and len(body) >= 80
    tools = [t.lower() for t in meta.get("tools", [])] if isinstance(meta.get("tools"), list) else []
    if not tools:
        return file_ok, False, f"{rel}: no tools list"
    if name == "test-writer":
        tools_ok = bool(set(tools) & EDIT_TOOLS) and bool(set(tools) & RUN_TOOLS)
        need = "an edit or write tool and a run tool"
    else:
        tools_ok = not (set(tools) & WRITE_TOOLS)
        need = "read-only tools only"
    note = f"{rel}: name={meta.get('name')!r}, tools={meta.get('tools')}"
    if not file_ok:
        note += " (needs name matching the file, a description, and instructions)"
    if not tools_ok:
        note += f" (needs {need})"
    return file_ok, tools_ok, note


# ---------------------------------------------------------------- permissions

def lock_rule_present(root: Path, rev: str | None) -> tuple[bool, bool, str]:
    """(acceptance_locked, frontend_locked, note) for the working tree (rev None) or a commit."""
    def read(path: str) -> str | None:
        if rev is None:
            p = root / path
            return p.read_text(encoding="utf-8") if p.is_file() else None
        return show(root, rev, path)

    acceptance = frontend = False
    notes = []
    for path, key in ((".claude/settings.json", "Edit("), ("agent/agy-permissions.json", "write_file(")):
        text = read(path)
        if text is None:
            continue
        try:
            deny = json.loads(text).get("permissions", {}).get("deny", [])
        except (json.JSONDecodeError, AttributeError):
            notes.append(f"{path} is not valid JSON")
            continue
        for rule in deny:
            if isinstance(rule, str) and rule.startswith(key):
                if "tests/acceptance" in rule:
                    acceptance = True
                if "frontend" in rule:
                    frontend = True
    return acceptance, frontend, "; ".join(notes)


# ---------------------------------------------------------------- ledger

def ledger_entries(root: Path) -> list[dict]:
    path = root / "LEDGER.md"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^##\s*My entries\s*$", text, re.M)
    mine = text[m.end():] if m else ""
    parts = re.split(r"^#{1,4}\s*Entry\s*(\d+)[^\n]*$", mine, flags=re.M | re.I)
    entries = []
    for i in range(1, len(parts), 2):
        fields: dict[str, str] = {}
        cur = None
        for raw in parts[i + 1].splitlines():
            s = re.sub(r"^[-*]\s*", "", raw.strip().strip("`")).replace("**", "")
            mm = re.match(r"^(" + "|".join(LEDGER_FIELDS) + r")\s*:\s*(.*)$", s, re.I)
            if mm:
                cur = mm.group(1).lower()
                fields[cur] = mm.group(2).strip()
            elif cur and s and not s.startswith("#"):
                fields[cur] += " " + s
        fields["_n"] = parts[i]
        entries.append(fields)
    return entries


def ledger_summary(root: Path) -> tuple[int, int, list[str]]:
    """(entries, complete entries, missing prompt files)."""
    entries = ledger_entries(root)
    complete = sum(1 for e in entries if all(e.get(k, "").strip() for k in LEDGER_FIELDS))
    have = {p.name for p in (root / "prompts").glob("*") if p.is_file()} if (root / "prompts").is_dir() else set()
    missing = []
    for e in entries:
        named = re.findall(r"prompts/([\w.\-]+)", e.get("prompts", ""))
        if not named:
            missing.append(f"entry {e['_n']}: no prompts/ file named")
        for name in named:
            if name not in have:
                missing.append(f"entry {e['_n']}: prompts/{name} does not exist")
    return len(entries), complete, missing


# ---------------------------------------------------------------- legacy

def annotated_everywhere(source: str) -> tuple[bool, list[str]]:
    tree = ast.parse(source)
    missing = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            for a in args:
                if a.annotation is None and a.arg not in ("self", "cls"):
                    missing.append(f"{node.name}({a.arg})")
            if node.args.vararg is not None and node.args.vararg.annotation is None:
                missing.append(f"{node.name}(*{node.args.vararg.arg})")
            if node.args.kwarg is not None and node.args.kwarg.annotation is None:
                missing.append(f"{node.name}(**{node.args.kwarg.arg})")
            if node.returns is None:
                missing.append(f"{node.name} return")
    return not missing, missing


def first_change_of(root: Path, path: str, original: str, upto: str = "HEAD") -> str | None:
    norm = original.replace("\r\n", "\n")
    for sha in git_out(root, "rev-list", "--reverse", "--first-parent", upto).splitlines():
        text = show(root, sha, path)
        if text is not None and text.replace("\r\n", "\n") != norm:
            return sha
    return None


def original_legacy(root: Path) -> str | None:
    roots = git_out(root, "rev-list", "--max-parents=0", "HEAD").splitlines()
    for r in roots[::-1]:
        text = show(root, r, "legacy/old_format.py")
        if text is not None:
            return text
    return None


# ---------------------------------------------------------------- report

class Report:
    def __init__(self) -> None:
        self.fails = 0

    def line(self, state: str, text: str) -> None:
        if state == "FAIL":
            self.fails += 1
        print(f"[{state:^4}] {text}")


def check_setup(root: Path, rep: Report) -> None:
    v = sys.version_info
    rep.line("OK" if v >= (3, 11) else "FAIL", f"Python {v.major}.{v.minor}.{v.micro} (3.11 or later needed)")
    wanted = {}
    for line in (root / "requirements.txt").read_text(encoding="utf-8").splitlines():
        if "==" in line:
            pkg, ver = line.strip().split("==")
            wanted[pkg] = ver
    import importlib.metadata as md
    for pkg, ver in wanted.items():
        try:
            have = md.version(pkg)
            rep.line("OK" if have == ver else "WARN", f"{pkg} {have} installed (requirements.txt pins {ver})")
        except md.PackageNotFoundError:
            rep.line("FAIL", f"{pkg} is not installed: run pip install -r requirements.txt")
    in_git = git(root, "rev-parse", "--is-inside-work-tree").returncode == 0
    rep.line("OK" if in_git else "FAIL", "inside a git repository")
    prefix = git_out(root, "rev-parse", "--show-prefix")
    if in_git and prefix:
        rep.line("WARN", f"this folder is {prefix} inside its repository: always start your agent here, in the folder that holds HANDOUT.md")
    origin = git_out(root, "remote", "get-url", "origin")
    if "md685-njit/Assignment-5" in origin:
        rep.line("WARN", "origin still points at the course repository: set it to your own (README, Setup step 2)")
    elif origin:
        rep.line("OK", f"origin is {origin}")
    else:
        rep.line("WARN", "no origin remote yet")
    for p in ("frontend/index.html", "frontend/app.js", "docs/spec.md", "tests/conftest.py"):
        rep.line("OK" if (root / p).is_file() else "FAIL", f"{p} present")


def check_tests(root: Path, rep: Report) -> None:
    names = collected_names(root, "tests/acceptance")
    counts = per_rule(names)
    rep.line("OK" if len(names) >= 20 else "FAIL", f"{len(names)} acceptance tests collected (at least 20)")
    for rule in RULES + ["R11"]:
        n = counts[rule]
        if rule == "R11" and n == 0:
            rep.line("--", "R11: 0 tests (R11 comes in Part 8)")
            continue
        rep.line("OK" if n else "FAIL", f"{rule}: {n} test{'' if n == 1 else 's'} named test_{rule.lower()}_...")
    other = [n for n in names if not TEST_NAME.match(n)]
    if other:
        rep.line("WARN", f"{len(other)} tests do not start with test_r<N>_: {', '.join(sorted(set(other))[:5])}")
    result = run_pytest(root, ["tests/acceptance"])
    t = result["tests"]
    rep.line("INFO", f"run now: {count(t, 'passed')} passed, {count(t, 'failed')} failed or errored")


def check_all(root: Path, rep: Report) -> None:
    print("== Instructions and agents (Parts 1 and 2)")
    agents_md = (root / "AGENTS.md").read_text(encoding="utf-8") if (root / "AGENTS.md").is_file() else ""
    sec = agents_md.split("## Backend rules", 1)[1] if "## Backend rules" in agents_md else ""
    lines = [l for l in sec.splitlines() if l.strip() and "Part 1: write this section" not in l]
    rep.line("OK" if len(lines) >= 6 else "FAIL", f"AGENTS.md, Backend rules: {len(lines)} lines (at least 6)")
    claude_used = (root / ".claude" / "agents").is_dir()
    if claude_used:
        ok = "@AGENTS.md" in ((root / "CLAUDE.md").read_text(encoding="utf-8") if (root / "CLAUDE.md").is_file() else "")
        rep.line("OK" if ok else "FAIL", "CLAUDE.md imports @AGENTS.md")
    for name in AGENTS:
        file_ok, tools_ok, note = check_agent(root, name)
        rep.line("OK" if file_ok and tools_ok else "FAIL", note)

    print("== Lock (Part 4)")
    locked = has_rev(root, LOCK_TAG)
    rep.line("OK" if locked else "FAIL", f"tag {LOCK_TAG} exists")
    acc, front, note = lock_rule_present(root, None)
    rep.line("OK" if acc and front else "FAIL", "deny rules for tests/acceptance/ and frontend/ in your permission file" + (f" ({note})" if note else ""))
    if locked:
        acc_t, front_t, _ = lock_rule_present(root, LOCK_TAG)
        rep.line("OK" if acc_t and front_t else "FAIL", f"the same deny rules are in the commit tagged {LOCK_TAG}")
        app_code = [f for f in files_at(root, LOCK_TAG, "app") if f.endswith(".py") and not f.endswith("__init__.py")]
        rep.line("OK" if not app_code else "FAIL", f"no backend code at {LOCK_TAG}" + (f": found {app_code}" if app_code else ""))
        tmp = Path(tempfile.mkdtemp())
        try:
            export_rev(root, LOCK_TAG, tmp)
            names = collected_names(tmp, "tests/acceptance")
            counts = per_rule(names)
            missing = [r for r in RULES if counts[r] == 0]
            rep.line("OK" if not missing else "FAIL", f"at the lock: a test for each of R1 to R10" + (f" (missing {missing})" if missing else ""))
            rep.line("OK" if len(names) >= 20 else "FAIL", f"at the lock: {len(names)} tests (at least 20)")
            res = run_pytest(tmp, ["tests/acceptance"])
            passed = count(res["tests"], "passed")
            rep.line("OK" if res["tests"] and passed == 0 else "FAIL", f"at the lock: every test fails or errors ({passed} passed)")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        changed = []
        locked_files = set(files_at(root, LOCK_TAG, "tests/acceptance"))
        for line in git_out(root, "diff", "--relative", "--name-status", LOCK_TAG, "HEAD", "--", "tests/acceptance").splitlines():
            status, *paths = line.split("\t")
            if paths and paths[0] in locked_files:
                changed.append(f"{status} {paths[0]}")
        prefix = git_out(root, "rev-parse", "--show-prefix")
        dirty = [l for l in git_out(root, "status", "--porcelain", "--", "tests/acceptance").splitlines() if l[3:].removeprefix(prefix) in locked_files]
        rep.line("OK" if not changed and not dirty else "FAIL", "locked test files unchanged since the lock" + (f": {changed + dirty}" if changed or dirty else ""))
    ev = root / "evidence" / "permission-denied.md"
    rep.line("OK" if ev.is_file() and len(ev.read_text(encoding="utf-8").strip()) > 80 else "FAIL", "evidence/permission-denied.md filled in")

    print("== Plan and build (Parts 5 and 6)")
    plan = (root / "docs" / "plan.md").read_text(encoding="utf-8") if (root / "docs" / "plan.md").is_file() else ""
    heads = all(re.search(rf"^#+\s*Task\s*{n}\b", plan, re.M | re.I) for n in (1, 2, 3))
    notin = re.search(r"^#+\s*Not in this change", plan, re.M | re.I) is not None
    rep.line("OK" if heads and notin else "FAIL", "docs/plan.md has Task 1, Task 2, Task 3 and Not in this change headings")
    code_commit = first_commit_with(root, "daily_limit", "app")
    if locked:
        end = code_commit or "HEAD"
        rng = f"{LOCK_TAG}..{end}"
        builds = [s for s in git_out(root, "rev-list", "--first-parent", rng, "--", "app").splitlines() if s != code_commit]
        rep.line("OK" if len(builds) >= 3 else "FAIL", f"{len(builds)} commits change app/ between the lock and the R11 code (at least 3)")
    layer = subprocess.run([sys.executable, str(Path(__file__).with_name("check_layers.py")), str(root)], capture_output=True, text=True)
    rep.line("OK" if layer.returncode == 0 else "FAIL", "layer check: " + layer.stdout.strip().replace("\n", " | "))
    res = run_pytest(root, ["tests/acceptance"])
    t = res["tests"]
    rep.line("OK" if t and count(t, "failed") == 0 else "FAIL", f"acceptance tests on your backend: {count(t, 'passed')} passed, {count(t, 'failed')} failed or errored")
    shot = root / "evidence" / "page.png"
    ok = shot.is_file() and shot.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    rep.line("OK" if ok else "FAIL", "evidence/page.png is a PNG screenshot")

    print("== Reviews (Part 7)")
    for f in ("review.md", "contract-check.md"):
        p = root / "evidence" / f
        rep.line("OK" if p.is_file() and len(p.read_text(encoding="utf-8").strip()) > 80 else "FAIL", f"evidence/{f} holds a report")

    print("== Spec change (Part 8)")
    spec = (root / "docs" / "spec.md").read_text(encoding="utf-8")
    rep.line("OK" if R11_MARKER in spec and "daily_limit" in spec else "FAIL", f"docs/spec.md has '{R11_MARKER}' and daily_limit")
    spec_commit = first_commit_with(root, R11_MARKER, "docs/spec.md")
    test_commit = first_commit_with(root, "daily_limit", "tests/acceptance")
    if code_commit and spec_commit and test_commit:
        rep.line("OK" if is_strict_ancestor(root, spec_commit, code_commit) else "FAIL", "the spec commit comes before the code commit")
        rep.line("OK" if is_strict_ancestor(root, test_commit, code_commit) else "FAIL", "the test commit comes before the code commit")
    else:
        rep.line("FAIL", f"first commits: R11 in spec {spec_commit and spec_commit[:7]}, daily_limit in tests {test_commit and test_commit[:7]}, daily_limit in app {code_commit and code_commit[:7]}")
    counts = per_rule(collected_names(root, "tests/acceptance"))
    rep.line("OK" if counts["R11"] >= 3 else "FAIL", f"{counts['R11']} tests named test_r11_... (at least 3)")
    decisions = re.findall(r"^[ \t]*-[ \t]*D\d+\.[ \t]*\S.{5,}$", spec, re.M)
    rep.line("OK" if len(decisions) >= 3 else "FAIL", f"{len(decisions)} decisions D1, D2, ... in spec section 7 (at least 3)")

    print("== ADR (Part 9)")
    adrs = sorted((root / "docs" / "adr").glob("0001*.md"))
    if adrs:
        text = adrs[0].read_text(encoding="utf-8")
        need = ["Context", "Options considered", "Decision", "Consequences"]
        miss = [h for h in need if not re.search(rf"^#+\s*{h}\b", text, re.M | re.I)]
        ok = not miss and re.search(r"^Status:\s*\S", text, re.M)
        rep.line("OK" if ok else "FAIL", f"{adrs[0].relative_to(root).as_posix()}" + (f" is missing {miss or 'Status'}" if not ok else " has Status and all sections"))
    else:
        rep.line("FAIL", "no docs/adr/0001-...md")

    print("== Legacy (Part 10)")
    names = collected_names(root, "tests/legacy")
    rep.line("OK" if len(names) >= 8 else "FAIL", f"{len(names)} characterization tests in tests/legacy (at least 8)")
    res = run_pytest(root, ["tests/legacy"])
    rep.line("OK" if res["tests"] and count(res["tests"], "failed") == 0 else "FAIL", f"they pass on your refactored file: {res['summary']}")
    original = original_legacy(root)
    current = (root / "legacy" / "old_format.py").read_text(encoding="utf-8")
    if original is not None:
        tmp = Path(tempfile.mkdtemp())
        try:
            shutil.copytree(root, tmp / "r", ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__"))
            (tmp / "r" / "legacy" / "old_format.py").write_text(original, encoding="utf-8")
            res = run_pytest(tmp / "r", ["tests/legacy"])
            rep.line("OK" if res["tests"] and count(res["tests"], "failed") == 0 else "FAIL", f"they pass on the original file: {res['summary']}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        changed = current.replace("\r\n", "\n") != original.replace("\r\n", "\n")
        rep.line("OK" if changed else "FAIL", "legacy/old_format.py has been refactored")
        refactor = first_change_of(root, "legacy/old_format.py", original)
        tests_first = first_commit_with(root, "old_format", "tests/legacy")
        if refactor and tests_first:
            rep.line("OK" if is_strict_ancestor(root, tests_first, refactor) else "FAIL", "the characterization tests were committed before the refactor")
    ok, missing = annotated_everywhere(current)
    rep.line("OK" if ok else "FAIL", "type hints on every function" + (f": missing {missing}" if missing else ""))

    print("== Report and ledger (Part 11)")
    n, complete, missing = ledger_summary(root)
    rep.line("OK" if complete >= 8 else "FAIL", f"LEDGER.md: {n} entries, {complete} with all seven fields (at least 8)")
    rep.line("OK" if n and not missing else "FAIL", "every entry names a prompt file that exists" + (f": {missing[:4]}" if missing else ""))
    report = (root / "REPORT.md").read_text(encoding="utf-8")
    rep.line("OK" if re.search(r"^Name:[ \t]*\S", report, re.M) else "FAIL", "REPORT.md has your name")
    rep.line("OK" if has_rev(root, SUBMIT_TAG) else "--", f"tag {SUBMIT_TAG} (add it last, then push with tags)")


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    rep = Report()
    if mode == "setup":
        check_setup(root, rep)
    elif mode == "tests":
        check_tests(root, rep)
    else:
        check_all(root, rep)
    print()
    print("All checks passed." if rep.fails == 0 else f"{rep.fails} check(s) failed.")
    return 1 if rep.fails else 0


if __name__ == "__main__":
    sys.exit(main())
