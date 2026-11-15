# ISP-00: Information Security Program Policy

> **FICTIONAL.** Acme Defense Fabrication and every person named are invented for study.
> Statements are my own wording; control IDs refer to NIST SP 800-53 Rev 5.

| Field | Value |
|---|---|
| Document ID | ISP-00 |
| Title | Information Security Program Policy |
| Version | 4.0 |
| Effective date | 2026-07-01 |
| Next review | 2027-07-01 |
| Owner | Priya Natarajan, ISSM |
| Approved by | Morgan Lee, CIO |
| Review cycle | **annually** (`P-PL-01`) |
| Related controls | PL-1, PL-4, PM-1, PM-9, AT-2 |

## 1. Purpose

This policy sets up Acme's information security program. It names who is accountable, how
policies are written and kept current, and how exceptions are approved. The topic policies
listed in Section 4 sit underneath it.

## 2. Scope

All Acme information systems and everyone who uses them: employees, contractors, and vendors
with system access.

## 3. Roles and responsibilities

| Role | Responsibility |
|---|---|
| CIO (Authorizing Official) | Approves policies, sets risk tolerance, accepts risk that exceeds it |
| ISSM | Owns the policy set, runs the program, tracks exceptions |
| ISSO (per system) | Applies the policies to a system, maintains its SSP and POA&M |
| System owner | Funds and staffs the controls for their system |
| Managers | Approve their staff's access and make sure training is done |
| All users | Follow the policies and the rules of behavior, and report incidents |

## 4. Policy statements

4.1 Acme keeps an information security program, documented in this policy and the topic policies ISP-AC, ISP-AU, ISP-CM, ISP-CP, ISP-IR, ISP-RA, and ISP-CA. The current version of each is listed in the policy index (`policies/README.md`). [PL-1, PM-1]

4.2 Policies state what must happen. Standards set specific values, procedures say how to do it, and each must agree with the policy above it. Where they conflict, the policy wins until the lower document is fixed. [PL-1]

4.3 Every organization-defined value in a policy is recorded once in the parameter register (`data/parameters.csv`) and cited by its ID, so a value cannot differ between documents. [PL-1]

4.4 The ISSM reviews every policy **annually** (`P-PL-01`), and after any major assessment finding that shows a policy gap. [PL-1]

4.5 The CIO sets Acme's risk tolerance. Risk above that tolerance may be accepted only by the CIO, in writing, under ISP-CA v4.0. [PM-9]

4.6 Every user signs the rules of behavior before getting access and again after any significant change to them. [PL-4]

4.7 Every workforce member completes security awareness training before getting access and **annually** (`P-AT-01`) after that. Access is suspended if training lapses by more than 30 days. [AT-2]

## 5. Exceptions

Exceptions to any ISP policy are requested through the ISSM. Each request names the control,
the reason, the compensating measures, and an end date. The CIO approves exceptions that raise
risk above tolerance. Approved exceptions are tracked as deviations under ISP-CA v4.0.

## 6. Enforcement

Violations may lead to loss of access and disciplinary action, up to and including termination
of employment or contract.

## 7. Revision history

| Version | Date | Summary |
|---|---|---|
| 3.0 | 2025-07-01 | Annual review |
| 4.0 | 2026-07-01 | Split into topic policies; added the parameter register (4.3) |
