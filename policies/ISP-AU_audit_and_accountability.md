# ISP-AU: Audit and Accountability Policy

> **FICTIONAL.** Acme Defense Fabrication and every person named are invented for study.
> Statements are my own wording; control IDs refer to NIST SP 800-53 Rev 5.

| Field | Value |
|---|---|
| Document ID | ISP-AU |
| Title | Audit and Accountability Policy |
| Version | 4.1 |
| Effective date | 2026-11-14 |
| Next review | 2027-11-14 |
| Owner | Priya Natarajan, ISSM |
| Approved by | Morgan Lee, CIO |
| Review cycle | **annually** (`P-PL-01`) |
| Related controls | AU-1, AU-2, AU-6, AU-9, AU-11, AU-12, SI-4 |

## 1. Purpose

Make system activity traceable to individuals, and make sure someone looks at it.

## 2. Scope

All Acme systems that store or process sensitive data, and the central SOC log platform.

## 3. Roles and responsibilities

| Role | Responsibility |
|---|---|
| SOC | Runs central detections and triages alerts around the clock |
| ISSO | Reviews system-specific events that central detections do not cover |
| System administrators | Keep logging turned on and forwarding |

## 4. Policy statements

4.1 Each system logs at least sign-ins, privilege use, account and role changes, access to sensitive records, and changes to security settings. Each SSP lists the system's event types. [AU-1, AU-2, AU-12]

4.2 Logs are forwarded to the SOC log platform in near real time. [AU-12, SI-4]

4.3 The SOC runs detections for each system and triages alerts within its published SLA. [SI-4]

4.4 The ISSO reviews system-specific audit logs **weekly** (`P-AU-01`). Each review is recorded in a ticket with the review checklist attached, **even when nothing is found**. [AU-6]

4.5 Audit records are kept for **12 months** (`P-AU-02`). [AU-11]

4.6 Only the SOC platform team can change log retention or delete logs, and those changes are themselves logged and alerted on. [AU-9]

## 5. Exceptions

As set out in ISP-00 v4.0, Section 5.

## 6. Enforcement

As set out in ISP-00 v4.0, Section 6.

## 7. Revision history

| Version | Date | Summary |
|---|---|---|
| 4.0 | 2026-07-01 | Annual review |
| 4.1 | 2026-11-14 | 4.4: every weekly review must leave a record, even with no findings (SAR finding AHR-2026-004) |
