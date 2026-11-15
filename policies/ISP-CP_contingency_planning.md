# ISP-CP: Contingency Planning Policy

> **FICTIONAL.** Acme Defense Fabrication and every person named are invented for study.
> Statements are my own wording; control IDs refer to NIST SP 800-53 Rev 5.

| Field | Value |
|---|---|
| Document ID | ISP-CP |
| Title | Contingency Planning Policy |
| Version | 4.0 |
| Effective date | 2026-07-01 |
| Next review | 2027-07-01 |
| Owner | Priya Natarajan, ISSM |
| Approved by | Morgan Lee, CIO |
| Review cycle | **annually** (`P-PL-01`) |
| Related controls | CP-1, CP-2, CP-4, CP-9, CP-10 |

## 1. Purpose

Make sure Acme can restore its systems and data after an outage, attack, or disaster, within
times the business has agreed to.

## 2. Scope

Every system with an SSP.

## 3. Roles and responsibilities

| Role | Responsibility |
|---|---|
| System owner | Owns the contingency plan and its testing, and sets recovery objectives with the business |
| ISSO | Makes sure the plan matches the SSP and test results reach the POA&M |
| System administrators | Run backups and restores |

## 4. Policy statements

4.1 Each system has a contingency plan that sets recovery time and recovery point objectives that match its availability categorization. [CP-1, CP-2]

4.2 The system owner reviews the plan **annually** (`P-CP-02`) and after major changes. [CP-2]

4.3 Each plan is tested **annually** (`P-CP-01`), and for a new system within its first year of operation. A test must include at least one actual restore from backup, not only a tabletop discussion. Results are recorded in an after-action report. [CP-4]

4.4 Backups are automated, protected from deletion by the accounts that run the system, and stored in a separate location. [CP-9]

4.5 Gaps found in a test go on the POA&M under ISP-CA v4.0. [CP-4, CP-10]

## 5. Exceptions

As set out in ISP-00 v4.0, Section 5.

## 6. Enforcement

As set out in ISP-00 v4.0, Section 6.

## 7. Revision history

| Version | Date | Summary |
|---|---|---|
| 3.0 | 2025-07-01 | Annual review |
| 4.0 | 2026-07-01 | 4.3 now requires an actual restore in each test |
