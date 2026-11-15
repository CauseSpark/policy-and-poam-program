# Policy index: Acme Information Security Policy v4

> **FICTIONAL.** This is the enterprise policy set the
> [Acme HR Portal SSP](https://github.com/CauseSpark/rmf-ato-package-templates/blob/main/examples/acme-hr-portal/ssp.md)
> cites as "Acme Information Security Policy v4". The Engineering Enclave documents in
> [ssp-document-consistency-review](https://github.com/CauseSpark/ssp-document-consistency-review)
> are a separate, enclave-specific set with deliberately planted errors.

| Document | Title | Version | Effective | Next review | Controls |
|---|---|---|---|---|---|
| [ISP-00](ISP-00_information_security_program.md) | Information Security Program Policy | 4.0 | 2026-07-01 | 2027-07-01 | PL-1, PL-4, PM-1, PM-9, AT-2 |
| [ISP-AC](ISP-AC_access_control.md) | Access Control Policy | 4.1 | 2026-11-14 | 2027-11-14 | AC-1, AC-2, AC-2(3), AC-5, AC-6, AC-12, IA-2(1) |
| [ISP-AU](ISP-AU_audit_and_accountability.md) | Audit and Accountability Policy | 4.1 | 2026-11-14 | 2027-11-14 | AU-1, AU-2, AU-6, AU-9, AU-11, AU-12, SI-4 |
| [ISP-CA](ISP-CA_assessment_and_poam.md) | Assessment, Authorization, and POA&M Policy | 4.0 | 2026-07-01 | 2027-07-01 | CA-1, CA-2, CA-5, CA-6, CA-7 |
| [ISP-CM](ISP-CM_configuration_management.md) | Configuration Management Policy | 4.0 | 2026-07-01 | 2027-07-01 | CM-1, CM-2, CM-3, CM-6, CM-7, SC-8 |
| [ISP-CP](ISP-CP_contingency_planning.md) | Contingency Planning Policy | 4.0 | 2026-07-01 | 2027-07-01 | CP-1, CP-2, CP-4, CP-9, CP-10 |
| [ISP-IR](ISP-IR_incident_response.md) | Incident Response Policy | 4.0 | 2026-07-01 | 2027-07-01 | IR-1, IR-3, IR-4, IR-6, IR-8 |
| [ISP-RA](ISP-RA_risk_and_vulnerability_management.md) | Risk Assessment and Vulnerability Management Policy | 4.0 | 2026-07-01 | 2027-07-01 | RA-1, RA-3, RA-5, SI-2 |

New policies start from [POLICY_TEMPLATE.md](POLICY_TEMPLATE.md). Run `python src/policy_lint.py`
before submitting one for approval.

## Changes made after the October 2026 assessment

| Finding or risk | Policy change |
|---|---|
| AHR-2026-001: inactive accounts not disabled | ISP-AC 4.4: disabling is automated and explicitly covers local and service accounts |
| AHR-2026-004: weekly log reviews not recorded | ISP-AU 4.4: every review leaves a ticket, even when nothing is found |
| R-01: phishing of HR accounts | ISP-AC 4.8: phishing-resistant MFA for HR and finance roles |
