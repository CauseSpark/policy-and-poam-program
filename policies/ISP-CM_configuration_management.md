# ISP-CM: Configuration Management Policy

> **FICTIONAL.** Acme Defense Fabrication and every person named are invented for study.
> Statements are my own wording; control IDs refer to NIST SP 800-53 Rev 5.

| Field | Value |
|---|---|
| Document ID | ISP-CM |
| Title | Configuration Management Policy |
| Version | 4.0 |
| Effective date | 2026-07-01 |
| Next review | 2027-07-01 |
| Owner | Priya Natarajan, ISSM |
| Approved by | Morgan Lee, CIO |
| Review cycle | **annually** (`P-PL-01`) |
| Related controls | CM-1, CM-2, CM-3, CM-6, CM-7, SC-8 |

## 1. Purpose

Keep systems in a known, secure state and control how that state changes.

## 2. Scope

Servers, network devices, cloud resources, and applications that make up Acme systems.

## 3. Roles and responsibilities

| Role | Responsibility |
|---|---|
| Change Advisory Board | Approves normal changes |
| ISSO | Approves emergency changes and reviews security impact |
| System administrators | Build from approved baselines and implement approved changes |

## 4. Policy statements

4.1 Each system has a documented baseline configuration, based on a recognized hardening benchmark, reviewed **annually** (`P-CM-03`) and after major upgrades. [CM-1, CM-2]

4.2 Changes are approved and tested before they are implemented. Emergency changes may be approved by the ISSO and are reviewed by the Change Advisory Board afterward. [CM-3]

4.3 Configuration compliance scans run **monthly** (`P-CM-02`). Drift is fixed or approved as an exception. [CM-6]

4.4 Data in transit uses **TLS 1.2** (`P-CM-01`) or higher. Older protocol versions are disabled on every endpoint. [CM-6, SC-8]

4.5 Systems run only the services, ports, and software their function needs. [CM-7]

4.6 Cloud storage blocks public access at the account level, and any change to a storage access policy alerts the SOC. [CM-6, CM-7]

## 5. Exceptions

As set out in ISP-00 v4.0, Section 5.

## 6. Enforcement

As set out in ISP-00 v4.0, Section 6.

## 7. Revision history

| Version | Date | Summary |
|---|---|---|
| 3.0 | 2025-07-01 | Annual review |
| 4.0 | 2026-07-01 | Added 4.6 on cloud storage public access |
