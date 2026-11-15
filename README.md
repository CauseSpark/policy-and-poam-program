# policy-and-poam-program

[![tests](https://github.com/CauseSpark/policy-and-poam-program/actions/workflows/tests.yml/badge.svg)](https://github.com/CauseSpark/policy-and-poam-program/actions/workflows/tests.yml)

A complete security policy set and a working POA&M program for the fictional Acme HR Portal:

- **Eight policies** on one template. Every statement is mapped to SP 800-53 controls, and every
  organization-defined value comes from a single parameter register.
- **A policy linter** that catches value drift, stale version references, unmapped statements,
  and overdue reviews before an assessor does.
- **A POA&M tracker** in Python and Excel. It checks every due date against the policy, flags
  overdue items and milestones, and writes the monthly status report.

> **Personal study material.** This is not official guidance from NIST or any agency.
> Acme Defense Fabrication, the HR Portal, every person, and every finding are fictional.

## Purpose

Writing a policy is the easy part. Keeping eight of them consistent with each other, with the
SSP, and with what actually happens takes more. My
[ssp-document-consistency-review](https://github.com/CauseSpark/ssp-document-consistency-review)
repo finds that kind of drift after the fact. This repo is the other half: a policy set built so
drift **can't happen quietly**, plus the POA&M process that turns findings into tracked, dated fixes.

## Versions referenced (checked November 2026)

| Source | Version | Used for |
|---|---|---|
| [NIST SP 800-53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) | Rev 5, Release 5.2.0 | Control mapping for every statement; CA-5 for the POA&M |
| [NIST SP 800-37](https://csrc.nist.gov/pubs/sp/800/37/r2/final) | Rev 2 | Where the POA&M fits in the RMF |
| [NIST SP 800-30](https://csrc.nist.gov/pubs/sp/800/30/r1/final) | Rev 1 | Required method for system risk assessments (ISP-RA) |

## Quick start

```bash
git clone https://github.com/CauseSpark/policy-and-poam-program.git
cd policy-and-poam-program
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

python src/policy_lint.py                              # check the policy set
python src/poam_tracker.py --as-of 2026-11-15          # validate the POA&M and print the monthly report
python src/build_tracker.py                            # rebuild the Excel tracker
pytest
```

## The policy set

| Document | Topic | Statements | Notable rule |
|---|---|---|---|
| ISP-00 | Program, roles, exceptions, training | 7 | One parameter register for every organization-defined value |
| ISP-AC | Access control | 8 | Accounts inactive for 35 days are disabled automatically |
| ISP-AU | Audit and accountability | 6 | Every weekly log review leaves a record, even when nothing is found |
| ISP-CA | Assessment and POA&M | 7 | Only the CIO accepts risk, for 12 months at most |
| ISP-CM | Configuration management | 6 | TLS 1.2 minimum; public access to cloud storage blocked |
| ISP-CP | Contingency planning | 5 | Every annual test includes a real restore |
| ISP-IR | Incident response | 5 | Personal data incidents go to Legal right away |
| ISP-RA | Risk and vulnerability management | 5 | 15/30/60/90-day fix windows; builds fail on overdue dependency flaws |

ISP-AC and ISP-AU were revised to v4.1 on 2026-11-14 in response to SAR findings AHR-2026-001 and
AHR-2026-004 (see [policies/README.md](policies/README.md)).

### How a parameter works

A policy never types a value on its own. It writes the value and cites its ID:

```markdown
4.4 Local, service, and break-glass accounts that show no activity for **35 days** (`P-AC-01`)
are disabled automatically. [AC-2(3)]
```

`data/parameters.csv` holds `P-AC-01 = 35 days`. If anyone edits the policy to "30 days", the
linter fails:

```
ISP-AC: P-AC-01 says '30 days' but the register says '35 days'
```

The POA&M tracker reads its deadlines from the same register, so the policy and the tooling
can't disagree.

## The POA&M (as of 2026-11-15)

| Measure | Count |
|---|---|
| Active items | 8 (High 2, Moderate 4, Low 2) |
| Overdue | 1: **POAM-0008**, High flaw on the jump host, 4 days late |
| Overdue milestones | 1 |
| Closed | 1 |
| Risk accepted | 1, approved by the CIO until 2027-11-05 |

Items come from three places, and each one traces back to its source:

| Items | Source | Repo |
|---|---|---|
| POAM-0001 to 0004 | SAR findings AHR-2026-001 to 004 | [rmf-ato-package-templates](https://github.com/CauseSpark/rmf-ato-package-templates) |
| POAM-0005 to 0007 | Risks R-01, R-08, R-04 | [risk-assessment-800-30](https://github.com/CauseSpark/risk-assessment-800-30) |
| POAM-0008 to 0010 | Weekly scans and an assessment observation | this repo |

The full monthly report is in [`reports/poam_status_2026-11.md`](reports/poam_status_2026-11.md).

### The Excel tracker

[`output/acme_hr_portal_poam_tracker.xlsx`](output/acme_hr_portal_poam_tracker.xlsx) holds the
same data, live:

- **One As-of date cell** drives every calculation. Type `=TODAY()` in it and the tracker updates itself.
- **Calculated columns:** policy window, Within Window, days open, days to due, flag, and open
  and overdue milestones per item.
- **Dashboard:** active, overdue, due-soon, and on-track counts; active items by risk; the oldest
  active item; and a check that turns red if any item is scheduled past its policy window.
- **Dropdowns** for status and risk, **conditional formatting** on flags, and a Rules sheet read
  from the parameter register.

A test recalculates the workbook in LibreOffice and checks every flag and count against the Python tracker.

## What's in the repo

| Path | What it is |
|---|---|
| `policies/` | The eight policies, an index, and a template |
| `data/parameters.csv` | 26 organization-defined parameters, each with its control and home policy |
| `poam/poam.csv`, `poam/milestones.csv` | The POA&M record (10 items, 21 milestones) |
| `src/policy_lint.py` | Structure, mapping, parameter, version, and review-date checks |
| `src/poam_tracker.py` | Policy-rule validation, status flags, and the monthly report |
| `src/build_tracker.py` | Builds the Excel tracker |
| `reports/poam_status_2026-11.md` | November 2026 status report, generated |
| `docs/poam_lifecycle.md` | Sources, required fields, statuses, deviations, reporting, closure |
| `tests/` | 43 pytest cases |

## What this demonstrates

- **Policy writing:** plain-language, testable statements with clear roles, exceptions, and revision history
- **Control mapping:** every statement tagged to SP 800-53, with the header kept in sync automatically
- **POA&M management:** due dates enforced by risk, real milestones, closure evidence, and risk acceptance limited by time and authority
- **Excel:** a date-driven tracker with lookups, `COUNTIFS`/`MAXIFS`, validation, and conditional formatting
- **Closing the loop:** findings → policy revisions → POA&M items → monthly reporting

## Related repos

Part 3 of a four-repo series on the same fictional system:

1. [risk-assessment-800-30](https://github.com/CauseSpark/risk-assessment-800-30): what could go wrong and how bad it is
2. [control-audit-evidence-kit](https://github.com/CauseSpark/control-audit-evidence-kit): how the controls were tested and what evidence backs each result
3. **policy-and-poam-program** (this repo): the policies and the POA&M tracker that drives the fixes
4. [security-risk-briefings](https://github.com/CauseSpark/security-risk-briefings): how it's explained to leadership

## Disclaimer

This repository is personal study material created for learning and portfolio purposes:

- It is **not** affiliated with or endorsed by NIST, the DoD, or any employer or client.
- The policies are examples, not legal or compliance advice. Have counsel review real policies.
- All names, systems, and findings are fictional.

## License

[MIT](LICENSE) © 2026 Peyton Seay
