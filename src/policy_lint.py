"""Lint the policy set against its own rules and the parameter register.

Catches the kinds of drift a document consistency review finds by hand:
a value that differs between documents, a reference to a superseded version,
a statement with no control mapping, or a policy past its review date.

    python src/policy_lint.py
    python src/policy_lint.py --as-of 2027-08-01      # see which reviews would be overdue
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICY_DIR = ROOT / "policies"
PARAMS = ROOT / "data" / "parameters.csv"

HEADER_FIELDS = ["Document ID", "Title", "Version", "Effective date", "Next review", "Owner",
                 "Approved by", "Review cycle", "Related controls"]
SECTIONS = ["## 1. Purpose", "## 2. Scope", "## 3. Roles and responsibilities",
            "## 4. Policy statements", "## 5. Exceptions", "## 6. Enforcement",
            "## 7. Revision history"]
CONTROL = r"[A-Z]{2}-\d{1,2}(?:\(\d{1,2}\))?"
STATEMENT = re.compile(rf"^(4\.\d+) (.+) \[({CONTROL}(?:, {CONTROL})*)\]$")
PARAM_USE = re.compile(r"\*\*([^*]+)\*\* \(`(P-[A-Z]{2}-\d{2})`\)")
PARAM_ID_ANYWHERE = re.compile(r"P-[A-Z]{2}-\d{2}")
DOC_REF = re.compile(r"\b(ISP-(?:\d{2}|[A-Z]{2})) v(\d+\.\d+)\b")


@dataclass
class Policy:
    path: Path
    header: dict
    text: str
    statements: list[tuple[str, str, list[str]]] = field(default_factory=list)

    @property
    def doc_id(self) -> str:
        return self.header.get("Document ID", self.path.stem)


def load_params(path: Path = PARAMS) -> dict[str, dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return {r["param_id"]: r for r in csv.DictReader(f)}


def parse_policy(path: Path) -> Policy:
    text = path.read_text(encoding="utf-8")
    header = {}
    for m in re.finditer(r"^\| ([A-Za-z ]+) \| (.+) \|$", text, flags=re.M):
        if m.group(1) in HEADER_FIELDS and m.group(1) not in header:
            header[m.group(1)] = m.group(2).strip()
    pol = Policy(path=path, header=header, text=text)
    section4 = text.split("## 4. Policy statements", 1)[-1].split("## 5.", 1)[0]
    for line in section4.splitlines():
        line = line.strip()
        if not re.match(r"^4\.\d+ ", line):
            continue
        m = STATEMENT.match(line)
        if m:
            pol.statements.append((m.group(1), m.group(2), m.group(3).split(", ")))
        else:
            pol.statements.append((line.split()[0], line, []))
    return pol


def load_policies(policy_dir: Path = POLICY_DIR) -> list[Policy]:
    return [parse_policy(p) for p in sorted(policy_dir.glob("ISP-*.md"))]


def lint(policy_dir: Path = POLICY_DIR, params_path: Path = PARAMS,
         as_of: date | None = None) -> list[str]:
    as_of = as_of or date(2026, 11, 15)
    params = load_params(params_path)
    policies = load_policies(policy_dir)
    problems: list[str] = []
    versions = {p.doc_id: p.header.get("Version") for p in policies}
    used: dict[str, set[str]] = {}

    for pol in policies:
        did = pol.doc_id
        for f in HEADER_FIELDS:
            if not pol.header.get(f):
                problems.append(f"{did}: header is missing '{f}'")
        if not pol.path.name.startswith(f"{did}_"):
            problems.append(f"{did}: file name {pol.path.name} should start with '{did}_'")
        for s in SECTIONS:
            if s not in pol.text:
                problems.append(f"{did}: missing section '{s}'")

        # Review dates
        try:
            eff = date.fromisoformat(pol.header["Effective date"])
            nxt = date.fromisoformat(pol.header["Next review"])
            if nxt != eff.replace(year=eff.year + 1):
                problems.append(f"{did}: next review {nxt} should be one year after {eff}")
            if nxt < as_of:
                problems.append(f"{did}: review overdue since {nxt}")
        except (KeyError, ValueError):
            problems.append(f"{did}: effective date and next review must be YYYY-MM-DD")

        # Version agrees with revision history
        hist = re.findall(r"^\| (\d+\.\d+) \| (\d{4}-\d{2}-\d{2}) \|", pol.text, flags=re.M)
        if hist and hist[-1][0] != pol.header.get("Version"):
            problems.append(f"{did}: header version {pol.header.get('Version')} but last revision is {hist[-1][0]}")
        if hist and hist[-1][1] != pol.header.get("Effective date"):
            problems.append(f"{did}: effective date {pol.header.get('Effective date')} but last revision dated {hist[-1][1]}")

        # Statements are numbered in order and mapped to controls
        tagged: set[str] = set()
        for i, (num, body, controls) in enumerate(pol.statements, start=1):
            if num != f"4.{i}":
                problems.append(f"{did}: statement {num} is out of sequence (expected 4.{i})")
            if not controls:
                problems.append(f"{did} {num}: no control mapping in [brackets] at the end")
            tagged.update(controls)
        if not pol.statements:
            problems.append(f"{did}: no policy statements found")
        header_controls = {c.strip() for c in pol.header.get("Related controls", "").split(",") if c.strip()}
        if header_controls != tagged:
            missing = sorted(tagged - header_controls)
            extra = sorted(header_controls - tagged)
            if missing:
                problems.append(f"{did}: Related controls header is missing {', '.join(missing)}")
            if extra:
                problems.append(f"{did}: Related controls header lists {', '.join(extra)} but no statement uses them")

        # Parameter values must match the register exactly
        for value, pid in PARAM_USE.findall(pol.text):
            used.setdefault(pid, set()).add(did)
            if pid not in params:
                problems.append(f"{did}: unknown parameter {pid}")
            elif value != params[pid]["value"]:
                problems.append(f"{did}: {pid} says '{value}' but the register says '{params[pid]['value']}'")
        cited = set(PARAM_ID_ANYWHERE.findall(pol.text))
        bare = cited - {pid for _, pid in PARAM_USE.findall(pol.text)}
        for pid in sorted(bare):
            problems.append(f"{did}: {pid} is cited without its value in the form **value** (`{pid}`)")

        # Cross-references to other policies must name the current version
        for ref_id, ref_ver in DOC_REF.findall(pol.text):
            if ref_id not in versions:
                problems.append(f"{did}: refers to unknown document {ref_id}")
            elif versions[ref_id] != ref_ver:
                problems.append(f"{did}: refers to {ref_id} v{ref_ver}, but the current version is v{versions[ref_id]}")

    for pid, row in params.items():
        if pid not in used:
            problems.append(f"{pid}: not used in any policy")
        elif row["policy"] not in used[pid]:
            problems.append(f"{pid}: home policy {row['policy']} does not state it")
    return problems


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Lint the policy set")
    p.add_argument("--as-of", type=date.fromisoformat, default=date(2026, 11, 15))
    args = p.parse_args(argv)
    policies = load_policies()
    problems = lint(as_of=args.as_of)
    n_statements = sum(len(x.statements) for x in policies)
    print(f"{len(policies)} policies, {n_statements} statements, {len(load_params())} parameters checked as of {args.as_of}")
    if problems:
        print(f"\n{len(problems)} problems:")
        for pr in problems:
            print(f"  - {pr}")
        return 1
    print("No problems found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
