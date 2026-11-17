"""Validate the POA&M and produce the monthly status report.

Remediation windows come from the parameter register (data/parameters.csv), the
same values the policies state, so the tracker and ISP-CA cannot disagree.

    python src/poam_tracker.py --as-of 2026-11-15
    python src/poam_tracker.py --as-of 2026-11-15 --write reports/poam_status_2026-11.md

Exit code 1 means the POA&M breaks a policy rule (validation problems).
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
POAM = ROOT / "poam" / "poam.csv"
MILESTONES = ROOT / "poam" / "milestones.csv"
PARAMS = ROOT / "data" / "parameters.csv"

RISKS = ["High", "Moderate", "Low"]
STATUSES = ["Open", "In Progress", "Closed", "Risk Accepted"]
DONE = {"Closed", "Risk Accepted"}
DUE_SOON_DAYS = 14
AS_OF = date(2026, 11, 15)   # date of the committed monthly report
SCAN_SOURCE = "Weekly scan"


def d(value: str) -> date:
    return date.fromisoformat(value)


def read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _days(value: str) -> int:
    m = re.fullmatch(r"(\d+) days", value)
    if not m:
        raise ValueError(f"expected 'N days', got '{value}'")
    return int(m.group(1))


def load_windows(path: Path = PARAMS) -> dict:
    p = {r["param_id"]: r["value"] for r in read_csv(path)}
    months = re.fullmatch(r"(\d+) months", p["P-CA-05"])
    return {
        "poam": {"High": _days(p["P-CA-01"]), "Moderate": _days(p["P-CA-02"]), "Low": _days(p["P-CA-03"])},
        "flaw": {"Critical": _days(p["P-SI-01"]), "High": _days(p["P-SI-02"]),
                 "Moderate": _days(p["P-SI-03"]), "Low": _days(p["P-SI-04"])},
        "acceptance_months": int(months.group(1)),
    }


def add_months(day: date, months: int) -> date:
    y, m = divmod(day.month - 1 + months, 12)
    year, month = day.year + y, m + 1
    for dd in (day.day, 30, 29, 28):
        try:
            return date(year, month, dd)
        except ValueError:
            continue
    raise AssertionError("unreachable")


@dataclass
class Item:
    row: dict
    milestones: list[dict]
    flag: str = ""
    days_open: int = 0
    days_to_due: int | None = None
    overdue_milestones: list[dict] = field(default_factory=list)
    next_milestone: dict | None = None

    @property
    def id(self) -> str:
        return self.row["poam_id"]


def window_for(row: dict, windows: dict) -> int:
    if row["source"].startswith(SCAN_SOURCE):
        return windows["flaw"][row["risk_rating"]]
    return windows["poam"][row["risk_rating"]]


def validate(poam: list[dict], milestones: list[dict], windows: dict, as_of: date) -> list[str]:
    problems = []
    ids = [r["poam_id"] for r in poam]
    if len(ids) != len(set(ids)):
        problems.append("duplicate POA&M IDs")
    by_item: dict[str, list[dict]] = {}
    for m in milestones:
        if m["poam_id"] not in ids:
            problems.append(f"milestone {m['poam_id']} {m['milestone']}: no such POA&M item")
        by_item.setdefault(m["poam_id"], []).append(m)
        if m["completed_date"] and d(m["completed_date"]) > as_of:
            problems.append(f"{m['poam_id']} {m['milestone']}: completed date {m['completed_date']} is after {as_of}")

    for r in poam:
        pid = r["poam_id"]
        if not re.fullmatch(r"POAM-\d{4}", pid):
            problems.append(f"{pid}: ID must look like POAM-0001")
        for col in ("weakness", "control", "point_of_contact", "resources_required", "source_ref"):
            if not r[col].strip():
                problems.append(f"{pid}: '{col}' is empty")
        if r["risk_rating"] not in RISKS:
            problems.append(f"{pid}: risk rating '{r['risk_rating']}' must be one of {', '.join(RISKS)}")
            continue
        if r["status"] not in STATUSES:
            problems.append(f"{pid}: status '{r['status']}' must be one of {', '.join(STATUSES)}")
            continue
        ident, due = d(r["identified_date"]), d(r["scheduled_completion_date"])
        limit = window_for(r, windows)
        if (due - ident).days > limit:
            problems.append(f"{pid}: {r['risk_rating']} item scheduled {(due - ident).days} days out; the limit is {limit}")
        if due < ident:
            problems.append(f"{pid}: scheduled completion is before the identified date")

        ms = by_item.get(pid, [])
        if r["status"] != "Risk Accepted":
            if not ms:
                problems.append(f"{pid}: needs at least one milestone")
            elif max(d(m["due_date"]) for m in ms) > due:
                problems.append(f"{pid}: a milestone is due after the scheduled completion date")

        if r["status"] == "Closed":
            if not r["completion_date"]:
                problems.append(f"{pid}: closed without a completion date")
            if not r["closure_evidence"].strip():
                problems.append(f"{pid}: closed without closure evidence (ISP-CA 4.5)")
            if any(not m["completed_date"] for m in ms):
                problems.append(f"{pid}: closed with open milestones")
        elif r["completion_date"]:
            problems.append(f"{pid}: has a completion date but status is {r['status']}")

        if r["status"] == "Risk Accepted":
            approver = r["deviation_approved_by"]
            if not r["deviation_type"]:
                problems.append(f"{pid}: risk accepted without a deviation type")
            if "CIO" not in approver:
                problems.append(f"{pid}: only the CIO can accept risk (ISP-CA 4.6)")
            m = re.search(r"\((\d{4}-\d{2}-\d{2})\)", approver)
            if not m or not r["deviation_expires"]:
                problems.append(f"{pid}: risk acceptance needs an approval date and an expiry date")
            else:
                latest = add_months(d(m.group(1)), windows["acceptance_months"])
                if d(r["deviation_expires"]) > latest:
                    problems.append(f"{pid}: acceptance expires {r['deviation_expires']}, later than {latest}")
                if d(r["deviation_expires"]) < as_of:
                    problems.append(f"{pid}: risk acceptance expired on {r['deviation_expires']}")
        elif r["deviation_type"]:
            problems.append(f"{pid}: has a deviation but status is {r['status']}")
    return problems


def compute(poam: list[dict], milestones: list[dict], as_of: date) -> list[Item]:
    by_item: dict[str, list[dict]] = {}
    for m in milestones:
        by_item.setdefault(m["poam_id"], []).append(m)
    items = []
    for r in poam:
        it = Item(row=r, milestones=sorted(by_item.get(r["poam_id"], []), key=lambda m: m["due_date"]))
        ident, due = d(r["identified_date"]), d(r["scheduled_completion_date"])
        end = d(r["completion_date"]) if r["completion_date"] else as_of
        it.days_open = (end - ident).days
        if r["status"] in DONE:
            it.flag = r["status"]
        else:
            it.days_to_due = (due - as_of).days
            if due < as_of:
                it.flag = "Overdue"
            elif it.days_to_due <= DUE_SOON_DAYS:
                it.flag = "Due Soon"
            else:
                it.flag = "On Track"
            open_ms = [m for m in it.milestones if not m["completed_date"]]
            it.overdue_milestones = [m for m in open_ms if d(m["due_date"]) < as_of]
            it.next_milestone = open_ms[0] if open_ms else None
        items.append(it)
    return items


def load(as_of: date, poam_path=POAM, ms_path=MILESTONES, params_path=PARAMS):
    poam, ms = read_csv(poam_path), read_csv(ms_path)
    windows = load_windows(params_path)
    return validate(poam, ms, windows, as_of), compute(poam, ms, as_of)


def summary(items: list[Item]) -> dict:
    active = [i for i in items if i.row["status"] not in DONE]
    return {
        "total": len(items),
        "active": len(active),
        "overdue": sum(1 for i in items if i.flag == "Overdue"),
        "due_soon": sum(1 for i in items if i.flag == "Due Soon"),
        "on_track": sum(1 for i in items if i.flag == "On Track"),
        "closed": sum(1 for i in items if i.flag == "Closed"),
        "risk_accepted": sum(1 for i in items if i.flag == "Risk Accepted"),
        "active_by_risk": {r: sum(1 for i in active if i.row["risk_rating"] == r) for r in RISKS},
        "overdue_milestones": sum(len(i.overdue_milestones) for i in active),
        "oldest_active_days": max((i.days_open for i in active), default=0),
    }


def render(items: list[Item], as_of: date) -> str:
    s = summary(items)
    active = [i for i in items if i.row["status"] not in DONE]
    out = [
        f"# POA&M status report: Acme HR Portal, as of {as_of}",
        "",
        "> FICTIONAL. Generated by `src/poam_tracker.py` from `poam/poam.csv` and `poam/milestones.csv`.",
        "",
        "## Summary",
        "",
        "| Measure | Count |",
        "|---|---|",
        f"| Active items | {s['active']} |",
        f"| Overdue items | {s['overdue']} |",
        f"| Due in the next {DUE_SOON_DAYS} days | {s['due_soon']} |",
        f"| On track | {s['on_track']} |",
        f"| Overdue milestones | {s['overdue_milestones']} |",
        f"| Closed | {s['closed']} |",
        f"| Risk accepted | {s['risk_accepted']} |",
        f"| Oldest active item (days open) | {s['oldest_active_days']} |",
        "",
        "Active items by risk: " + ", ".join(f"{k} {v}" for k, v in s["active_by_risk"].items()),
        "",
        "## Needs attention",
        "",
    ]
    attention = [i for i in active if i.flag == "Overdue" or i.overdue_milestones]
    if not attention:
        out.append("Nothing is overdue.")
    for i in attention:
        late = (as_of - d(i.row["scheduled_completion_date"])).days
        what = f"**{i.id}** ({i.row['risk_rating']}, {i.row['control']}): {i.row['weakness']}."
        if i.flag == "Overdue":
            what += f" Overdue by {late} days."
        for m in i.overdue_milestones:
            what += f" Milestone {m['milestone']} ({m['description']}) was due {m['due_date']}."
        what += f" Owner: {i.row['point_of_contact']}. Latest note: {i.row['comments'] or 'none'}."
        out.append(f"- {what}")
    out += ["", f"## Coming due in the next {DUE_SOON_DAYS} days", ""]
    upcoming = []
    for i in active:
        for m in i.milestones:
            if not m["completed_date"] and 0 <= (d(m["due_date"]) - as_of).days <= DUE_SOON_DAYS:
                upcoming.append((m["due_date"], i.id, m["milestone"], m["description"], i.row["point_of_contact"]))
    if not upcoming:
        out.append("No milestones due.")
    else:
        out += ["| Due | Item | Milestone | Owner |", "|---|---|---|---|"]
        out += [f"| {due} | {pid} | {ms}: {desc} | {poc} |" for due, pid, ms, desc, poc in sorted(upcoming)]
    out += ["", "## All active items", "",
            "| Item | Risk | Control | Due | Days left | Status | Flag | Next milestone |",
            "|---|---|---|---|---|---|---|---|"]
    order = {"Overdue": 0, "Due Soon": 1, "On Track": 2}
    for i in sorted(active, key=lambda x: (order[x.flag], RISKS.index(x.row["risk_rating"]), x.row["scheduled_completion_date"])):
        nm = f"{i.next_milestone['milestone']} {i.next_milestone['due_date']}" if i.next_milestone else "none"
        out.append(f"| {i.id} | {i.row['risk_rating']} | {i.row['control']} | {i.row['scheduled_completion_date']} | "
                   f"{i.days_to_due} | {i.row['status']} | {i.flag} | {nm} |")
    out += ["", "## Closed and risk accepted", "", "| Item | Outcome | Detail |", "|---|---|---|"]
    for i in items:
        if i.flag == "Closed":
            out.append(f"| {i.id} | Closed {i.row['completion_date']} | {i.row['closure_evidence']} |")
        elif i.flag == "Risk Accepted":
            out.append(f"| {i.id} | Risk accepted until {i.row['deviation_expires']} | "
                       f"{i.row['deviation_type']}; approved by {i.row['deviation_approved_by']} |")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Validate the POA&M and report status")
    p.add_argument("--as-of", type=date.fromisoformat, default=AS_OF)
    p.add_argument("--write", type=Path, help="also write the report to this file")
    args = p.parse_args(argv)
    problems, items = load(args.as_of)
    report = render(items, args.as_of)
    print(report)
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(report, encoding="utf-8")
    if problems:
        print("Validation problems:")
        for pr in problems:
            print(f"  - {pr}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
