import shutil
from datetime import date
from pathlib import Path

import pytest

import policy_lint as pl

ROOT = Path(__file__).resolve().parent.parent


def test_policy_set_is_clean():
    assert pl.lint() == []


def test_counts():
    pols = pl.load_policies()
    assert [p.doc_id for p in pols] == ["ISP-00", "ISP-AC", "ISP-AU", "ISP-CA", "ISP-CM", "ISP-CP", "ISP-IR", "ISP-RA"]
    assert all(len(p.statements) >= 5 for p in pols)


@pytest.mark.parametrize("pid,value", [
    # These must match the Acme HR Portal SSP in rmf-ato-package-templates.
    ("P-AC-01", "35 days"),
    ("P-SI-01", "15 days"), ("P-SI-02", "30 days"), ("P-SI-03", "60 days"), ("P-SI-04", "90 days"),
    ("P-AU-01", "weekly"), ("P-CM-01", "TLS 1.2"), ("P-RA-02", "weekly"), ("P-CP-01", "annually"),
])
def test_parameters_match_hr_portal_ssp(pid, value):
    assert pl.load_params()[pid]["value"] == value


@pytest.fixture
def pols(tmp_path):
    shutil.copytree(ROOT / "policies", tmp_path / "policies")
    shutil.copytree(ROOT / "data", tmp_path / "data")
    return tmp_path


def run(tmp, as_of=None):
    return pl.lint(tmp / "policies", tmp / "data" / "parameters.csv", as_of)


def edit(path, old, new):
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_value_drift_is_caught(pols):
    edit(pols / "policies" / "ISP-AC_access_control.md", "**35 days** (`P-AC-01`)", "**30 days** (`P-AC-01`)")
    assert "ISP-AC: P-AC-01 says '30 days' but the register says '35 days'" in run(pols)


def test_bare_parameter_reference_is_caught(pols):
    edit(pols / "policies" / "ISP-AU_audit_and_accountability.md", "**12 months** (`P-AU-02`)", "P-AU-02")
    problems = run(pols)
    assert any("P-AU-02 is cited without its value" in p for p in problems)
    assert "P-AU-02: home policy ISP-AU does not state it" in problems or "P-AU-02: not used in any policy" in problems


def test_stale_version_reference_is_caught(pols):
    edit(pols / "policies" / "ISP-CP_contingency_planning.md", "ISP-CA v4.0", "ISP-CA v3.0")
    assert "ISP-CP: refers to ISP-CA v3.0, but the current version is v4.0" in run(pols)


def test_unmapped_statement_is_caught(pols):
    edit(pols / "policies" / "ISP-IR_incident_response.md",
         "from first report to closure. [IR-4]", "from first report to closure.")
    problems = run(pols)
    assert "ISP-IR 4.3: no control mapping in [brackets] at the end" in problems
    assert any("ISP-IR: Related controls header lists IR-4" in p for p in problems)


def test_header_missing_a_tagged_control_is_caught(pols):
    edit(pols / "policies" / "ISP-CM_configuration_management.md",
         "| Related controls | CM-1, CM-2, CM-3, CM-6, CM-7, SC-8 |", "| Related controls | CM-1, CM-2, CM-3, CM-6, CM-7 |")
    assert "ISP-CM: Related controls header is missing SC-8" in run(pols)


def test_overdue_review_is_caught(pols):
    problems = run(pols, as_of=date(2027, 7, 2))
    assert "ISP-00: review overdue since 2027-07-01" in problems
    assert not any(p.startswith("ISP-AC: review overdue") for p in problems)   # revised 2026-11-14


def test_version_must_match_revision_history(pols):
    edit(pols / "policies" / "ISP-RA_risk_and_vulnerability_management.md", "| Version | 4.0 |", "| Version | 4.2 |")
    assert any("ISP-RA: header version 4.2 but last revision is 4.0" in p for p in run(pols))


def test_out_of_sequence_statement_is_caught(pols):
    edit(pols / "policies" / "ISP-CA_assessment_and_poam.md", "4.3 The scheduled", "4.9 The scheduled")
    assert "ISP-CA: statement 4.9 is out of sequence (expected 4.3)" in run(pols)


def test_unused_parameter_is_caught(pols):
    with open(pols / "data" / "parameters.csv", "a", encoding="utf-8") as f:
        f.write("P-MP-01,MP-6,Media sanitization method,NIST 800-88 purge,ISP-MP\n")
    assert "P-MP-01: not used in any policy" in run(pols)


def test_cli(capsys):
    assert pl.main([]) == 0
    assert "No problems found." in capsys.readouterr().out


def test_policy_index_matches_documents():
    import re
    index = (ROOT / "policies" / "README.md").read_text(encoding="utf-8")
    for p in pl.load_policies():
        row = re.search(rf"^\| \[{p.doc_id}\]\(([^)]+)\) \| (.+?) \| ([\d.]+) \| ([\d-]+) \| ([\d-]+) \| (.+) \|$", index, flags=re.M)
        assert row, f"{p.doc_id} missing from policies/README.md"
        assert row.group(1) == p.path.name
        assert row.group(2) == p.header["Title"]
        assert row.group(3) == p.header["Version"]
        assert row.group(4) == p.header["Effective date"]
        assert row.group(5) == p.header["Next review"]
        assert row.group(6) == p.header["Related controls"]
