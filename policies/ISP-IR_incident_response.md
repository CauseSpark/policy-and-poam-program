# ISP-IR: Incident Response Policy

> **FICTIONAL.** Acme Defense Fabrication and every person named are invented for study.
> Statements are my own wording; control IDs refer to NIST SP 800-53 Rev 5.

| Field | Value |
|---|---|
| Document ID | ISP-IR |
| Title | Incident Response Policy |
| Version | 4.0 |
| Effective date | 2026-07-01 |
| Next review | 2027-07-01 |
| Owner | Priya Natarajan, ISSM |
| Approved by | Morgan Lee, CIO |
| Review cycle | **annually** (`P-PL-01`) |
| Related controls | IR-1, IR-3, IR-4, IR-6, IR-8 |

## 1. Purpose

Detect, contain, and recover from security incidents quickly, and meet every notification duty
that applies.

## 2. Scope

All Acme systems, data, and workforce members.

## 3. Roles and responsibilities

| Role | Responsibility |
|---|---|
| All users | Report suspected incidents |
| SOC | Takes reports, triages, and leads technical response |
| ISSM | Incident commander for significant incidents; decides on outside notification with Legal |
| Legal | Decides whether breach-notification laws or contract terms apply |

## 4. Policy statements

4.1 Acme keeps an incident response plan that covers preparation, detection and analysis, containment, eradication, recovery, and post-incident review. [IR-1, IR-8]

4.2 Anyone who suspects an incident reports it to the SOC within **1 hour** (`P-IR-01`). [IR-6]

4.3 The SOC records every reported incident in a ticket, from first report to closure. [IR-4]

4.4 For any incident that may involve personal data, the ISSM brings in Legal right away. Legal decides whether breach notification is required and sets the timeline. [IR-6]

4.5 Incident response is tested **annually** (`P-IR-02`) through a tabletop or functional exercise. Lessons learned go on the POA&M under ISP-CA v4.0. [IR-3]

## 5. Exceptions

As set out in ISP-00 v4.0, Section 5.

## 6. Enforcement

As set out in ISP-00 v4.0, Section 6.

## 7. Revision history

| Version | Date | Summary |
|---|---|---|
| 3.0 | 2025-07-01 | Annual review |
| 4.0 | 2026-07-01 | Added 4.4 on personal data and Legal |
