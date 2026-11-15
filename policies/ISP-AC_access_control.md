# ISP-AC: Access Control Policy

> **FICTIONAL.** Acme Defense Fabrication and every person named are invented for study.
> Statements are my own wording; control IDs refer to NIST SP 800-53 Rev 5.

| Field | Value |
|---|---|
| Document ID | ISP-AC |
| Title | Access Control Policy |
| Version | 4.1 |
| Effective date | 2026-11-14 |
| Next review | 2027-11-14 |
| Owner | Priya Natarajan, ISSM |
| Approved by | Morgan Lee, CIO |
| Review cycle | **annually** (`P-PL-01`) |
| Related controls | AC-1, AC-2, AC-2(3), AC-5, AC-6, AC-12, IA-2(1) |

## 1. Purpose

Make sure only authorized people and processes reach Acme systems, with no more access than
they need.

## 2. Scope

All user, privileged, service, and break-glass accounts on every Acme system, including accounts
local to a system that do not come from the Enterprise Identity Service.

## 3. Roles and responsibilities

| Role | Responsibility |
|---|---|
| Manager | Requests and approves access for their staff |
| ISSO | Approves privileged and sensitive-role access, runs access reviews |
| System administrators | Create, change, and disable accounts only from approved tickets |
| HR | Records separations the same day so access can be removed |

## 4. Policy statements

4.1 Access is granted only from a documented request approved by the user's manager and, for privileged or sensitive-data roles, by the ISSO, before the access is given. [AC-1, AC-2]

4.2 Every account has a named owner. Service accounts are owned by a team, and that team answers for them. [AC-2]

4.3 Access is disabled within **1 business day** (`P-AC-03`) of a workforce member's separation. [AC-2]

4.4 Local, service, and break-glass accounts that show no activity for **35 days** (`P-AC-01`) are disabled automatically. Break-glass accounts are exempt only with a documented exception and a sealed credential. [AC-2(3)]

4.5 The ISSO reviews privileged and sensitive-role assignments **quarterly** (`P-AC-02`) and records the review in a ticket. [AC-2, AC-6]

4.6 Users get the least access their job requires. System administrators do not hold application roles that expose business data, and application staff do not get infrastructure access. [AC-5, AC-6]

4.7 Application sessions end after **15 minutes** (`P-AC-04`) of inactivity. [AC-12]

4.8 Every sign-in to a privileged or sensitive-data role uses multi-factor authentication through the Enterprise Identity Service. HR and finance roles use phishing-resistant MFA. [IA-2(1)]

## 5. Exceptions

As set out in ISP-00 v4.0, Section 5.

## 6. Enforcement

Accounts created or kept outside this policy are disabled when found. Repeated violations are
handled under ISP-00 v4.0, Section 6.

## 7. Revision history

| Version | Date | Summary |
|---|---|---|
| 4.0 | 2026-07-01 | Annual review |
| 4.1 | 2026-11-14 | 4.4: inactivity disabling is now automated and covers local and service accounts (SAR finding AHR-2026-001). 4.8: phishing-resistant MFA for HR and finance roles (risk R-01) |
