import copy
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest
from openpyxl import load_workbook

import build_tracker as bt
import poam_tracker as pt

ROOT = Path(__file__).resolve().parent.parent
AS_OF = date(2026, 11, 15)


@pytest.fixture(scope="module")
def data():
    return pt.read_csv(pt.POAM), pt.read_csv(pt.MILESTONES), pt.load_windows()


def test_repo_poam_is_valid():
    problems, _ = pt.load(AS_OF)
    assert problems == []


def test_windows_come_from_parameter_register(data):
    _, _, w = data
    assert w["poam"] == {"High": 30, "Moderate": 90, "Low": 180}
    assert w["flaw"] == {"Critical": 15, "High": 30, "Moderate": 60, "Low": 90}
    assert w["acceptance_months"] == 12


def test_summary_as_of_report_date():
    _, items = pt.load(AS_OF)
    s = pt.summary(items)
    assert (s["active"], s["overdue"], s["on_track"], s["closed"], s["risk_accepted"]) == (8, 1, 7, 1, 1)
    assert s["active_by_risk"] == {"High": 2, "Moderate": 4, "Low": 2}
    assert s["overdue_milestones"] == 1
    assert s["oldest_active_days"] == 37


def test_overdue_item_is_poam_0008():
    _, items = pt.load(AS_OF)
    overdue = [i for i in items if i.flag == "Overdue"]
    assert [i.id for i in overdue] == ["POAM-0008"]
    assert overdue[0].days_to_due == -4


def test_flags_move_with_the_date():
    _, items = pt.load(date(2026, 11, 25))
    flags = {i.id: i.flag for i in items}
    assert flags["POAM-0002"] == "Due Soon"          # due 2026-11-30
    _, items = pt.load(date(2026, 12, 1))
    assert {i.id: i.flag for i in items}["POAM-0002"] == "Overdue"


def test_sar_items_match_rmf_package(data):
    # POAM-0001..0004 come straight from the RMF repo's poam.csv.
    poam, _, _ = data
    by_id = {r["poam_id"]: r for r in poam}
    expected = {
        "POAM-0001": ("AHR-2026-001", "AC-2(3)", "Moderate", "2026-12-15"),
        "POAM-0002": ("AHR-2026-002", "SI-2", "Moderate", "2026-11-30"),
        "POAM-0003": ("AHR-2026-003", "CP-4", "Low", "2027-02-26"),
        "POAM-0004": ("AHR-2026-004", "AU-6", "Low", "2026-12-31"),
    }
    for pid, (ref, ctl, risk, due) in expected.items():
        r = by_id[pid]
        assert (r["source_ref"], r["control"], r["risk_rating"], r["scheduled_completion_date"]) == (ref, ctl, risk, due)


def test_risk_assessment_items_match(data):
    # POAM-0005..0007 come from the risk register in risk-assessment-800-30.
    poam, _, _ = data
    refs = {r["poam_id"]: (r["source_ref"], r["risk_rating"]) for r in poam}
    assert refs["POAM-0005"] == ("R-01", "High")
    assert refs["POAM-0006"] == ("R-08", "Moderate")
    assert refs["POAM-0007"] == ("R-04", "Moderate")


def test_report_is_current():
    _, items = pt.load(AS_OF)
    committed = (ROOT / "reports" / "poam_status_2026-11.md").read_text(encoding="utf-8")
    assert committed == pt.render(items, AS_OF)


# --- Validation catches policy violations -------------------------------------

def check(poam, ms, as_of=AS_OF):
    return pt.validate(poam, ms, pt.load_windows(), as_of)


def mutate(data, pid, **changes):
    poam, ms, _ = data
    poam = copy.deepcopy(poam)
    for r in poam:
        if r["poam_id"] == pid:
            r.update(changes)
    return poam, copy.deepcopy(ms)


def test_window_violation(data):
    poam, ms = mutate(data, "POAM-0005", scheduled_completion_date="2027-01-31")
    assert any("POAM-0005: High item scheduled 79 days out; the limit is 30" in p for p in check(poam, ms))


def test_scan_items_use_flaw_window(data):
    # A High scan item gets 30 days from detection (P-SI-02), the same as High POA&M items.
    poam, ms = mutate(data, "POAM-0008", scheduled_completion_date="2026-11-12")
    assert any("POAM-0008" in p and "limit is 30" in p for p in check(poam, ms))


def test_closed_without_evidence(data):
    poam, ms = mutate(data, "POAM-0009", closure_evidence="")
    assert "POAM-0009: closed without closure evidence (ISP-CA 4.5)" in check(poam, ms)


def test_only_cio_accepts_risk(data):
    poam, ms = mutate(data, "POAM-0010", deviation_approved_by="Dana Ruiz, System Owner (2026-11-05)")
    assert "POAM-0010: only the CIO can accept risk (ISP-CA 4.6)" in check(poam, ms)


def test_acceptance_longer_than_12_months(data):
    poam, ms = mutate(data, "POAM-0010", deviation_expires="2027-12-31")
    assert any("POAM-0010: acceptance expires 2027-12-31, later than 2027-11-05" in p for p in check(poam, ms))


def test_expired_acceptance(data):
    poam, ms, _ = data
    assert any("risk acceptance expired" in p for p in check(poam, ms, as_of=date(2027, 11, 6)))


def test_milestone_after_completion_date(data):
    poam, ms = mutate(data, "POAM-0006", scheduled_completion_date="2026-12-10")
    assert "POAM-0006: a milestone is due after the scheduled completion date" in check(poam, ms)


def test_item_needs_a_milestone(data):
    poam, ms, _ = data
    ms = [m for m in ms if m["poam_id"] != "POAM-0003"]
    assert "POAM-0003: needs at least one milestone" in check(poam, ms)


def test_bad_status(data):
    poam, ms = mutate(data, "POAM-0001", status="Done")
    assert any("POAM-0001: status 'Done'" in p for p in check(poam, ms))


def test_cli(capsys):
    assert pt.main(["--as-of", "2026-11-15"]) == 0
    assert "POAM-0008" in capsys.readouterr().out


# --- Excel tracker ---------------------------------------------------------------

@pytest.fixture(scope="module")
def built(tmp_path_factory):
    return bt.build(tmp_path_factory.mktemp("xl") / "tracker.xlsx", AS_OF)


def test_tracker_sheets_and_formulas(built):
    wb = load_workbook(built)
    assert wb.sheetnames == ["Dashboard", "POA&M", "Milestones", "Rules", "Instructions"]
    ws = wb["POA&M"]
    assert ws[f"{bt.PC['Flag']}{bt.FIRST}"].value.startswith("=IF(")
    assert "Dashboard!$C$4" in ws[f"{bt.PC['Days Open']}{bt.FIRST}"].value


def test_rules_sheet_uses_register(built):
    ws = load_workbook(built)["Rules"]
    assert [ws[f"C{r}"].value for r in (6, 7, 8)] == [30, 90, 180]


@pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice not installed")
def test_tracker_formulas_match_python(built, tmp_path):
    subprocess.run(["soffice", "--headless", "--convert-to", "xlsx", "--outdir", str(tmp_path), str(built)],
                   check=True, capture_output=True, timeout=120)
    wb = load_workbook(tmp_path / built.name, data_only=True)
    ws = wb["POA&M"]
    _, items = pt.load(AS_OF)
    for i, item in enumerate(items):
        r = bt.FIRST + i
        assert ws[f"A{r}"].value == item.id
        assert ws[f"{bt.PC['Flag']}{r}"].value == item.flag
        assert ws[f"{bt.PC['Days Open']}{r}"].value == item.days_open
        assert ws[f"{bt.PC['Overdue Milestones']}{r}"].value == len(item.overdue_milestones)
    dash = wb["Dashboard"]
    s = pt.summary(items)
    assert dash["C7"].value == s["active"]
    assert dash["C8"].value == s["overdue"]
    assert dash["C11"].value == s["overdue_milestones"]
    assert dash["C14"].value == s["oldest_active_days"]
