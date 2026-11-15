# ISP-CA: Assessment, Authorization, and POA&M Policy

> **FICTIONAL.** Acme Defense Fabrication and every person named are invented for study.
> Statements are my own wording; control IDs refer to NIST SP 800-53 Rev 5.

| Field | Value |
|---|---|
| Document ID | ISP-CA |
| Title | Assessment, Authorization, and POA&M Policy |
| Version | 4.0 |
| Effective date | 2026-07-01 |
| Next review | 2027-07-01 |
| Owner | Priya Natarajan, ISSM |
| Approved by | Morgan Lee, CIO |
| Review cycle | **annually** (`P-PL-01`) |
| Related controls | CA-1, CA-2, CA-5, CA-6, CA-7 |

## 1. Purpose

Make sure controls are tested independently, that weaknesses are tracked to closure, and that
the decision to accept any risk left over is made by the right person.

## 2. Scope

Every system that goes through the RMF at Acme.

## 3. Roles and responsibilities

| Role | Responsibility |
|---|---|
| Internal Audit | Independent control assessments |
| ISSO | Keeps the POA&M current and reports on it |
| Point of contact (per item) | Delivers the milestones on time |
| System owner | Funds remediation |
| CIO (Authorizing Official) | Authorizes systems and approves risk acceptances |

## 4. Policy statements

4.1 Internal Audit, which is independent of IT and the system owner, assesses controls before authorization and reassesses a rotating third of them each year. [CA-1, CA-2, CA-7]

4.2 Every weakness from an assessment, risk assessment, scan, incident, or exercise that is not fixed right away gets a POA&M item with a risk rating, milestones, resources, and one point of contact. [CA-5]

4.3 The scheduled completion date can be no later than: High **30 days** (`P-CA-01`), Moderate **90 days** (`P-CA-02`), Low **180 days** (`P-CA-03`), counted from the date the weakness was identified. Flaws covered by ISP-RA v4.0 keep their shorter windows. [CA-5]

4.4 The ISSO updates the POA&M and reports it to the CIO **monthly** (`P-CA-04`). The report lists overdue items and overdue milestones by name. [CA-5, CA-7]

4.5 An item closes only when there is evidence the fix works, such as a rescan, a re-performed test, or a screenshot of the setting, and the ISSO has checked it. [CA-5]

4.6 A weakness that will not be fixed is a deviation. It may be closed as risk accepted only with the CIO's written approval, which lasts at most **12 months** (`P-CA-05`) before it must be renewed. [CA-5, CA-6]

4.7 The CIO reviews the POA&M before every authorization decision and at the annual security review. [CA-6, CA-7]

## 5. Exceptions

No exceptions to Section 4.6: only the CIO accepts risk.

## 6. Enforcement

A point of contact with two overdue milestones in a row is escalated to the system owner.

## 7. Revision history

| Version | Date | Summary |
|---|---|---|
| 3.0 | 2025-07-01 | Annual review |
| 4.0 | 2026-07-01 | Added the 12-month limit on risk acceptance (4.6) and closure evidence (4.5) |
