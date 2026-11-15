# POA&M lifecycle

How a weakness becomes a POA&M item, moves through milestones, and leaves the list. The rules
come from [ISP-CA](../policies/ISP-CA_assessment_and_poam.md) (fictional Acme policy). The POA&M
itself is SP 800-53 control CA-5, and the RMF uses it at the Assess, Authorize, and Monitor steps
of SP 800-37 Rev 2.

```
 Source                 Open → In Progress → Closed
 ─────────              │                    ▲
 SAR finding  ──┐       │                    │ evidence the fix works, checked by the ISSO
 Risk register ─┼──►  Open                   │
 Weekly scan   ─┤       │
 Incident/test ─┘       └──► Risk Accepted   (deviation approved by the CIO, max 12 months)
```

## 1. Where items come from

| Source | Example in this repo | Due date rule |
|---|---|---|
| Security Assessment Report | POAM-0001 to 0004 (AHR-2026-001 to 004) | ISP-CA 4.3: High 30, Moderate 90, Low 180 days from identification |
| Risk assessment | POAM-0005 to 0007 (R-01, R-08, R-04) | Same as above |
| Weekly vulnerability scan | POAM-0008, POAM-0010 | ISP-RA 4.3: severity window from first detection (High 30, Moderate 60, Low 90) |
| Assessment observation | POAM-0009 (SOC holiday on-call) | Same as SAR findings |

A finding corrected during the assessment (AHR-2026-005) does not get an item. It is reported in
the SAR as corrected, and the rescan is the evidence.

## 2. What every item needs

| Field | Why |
|---|---|
| Weakness | In plain words, what's wrong. Not the control name |
| Source and source reference | So anyone can trace it back to the finding, risk, or scan result |
| Control | The SP 800-53 control that isn't working |
| Risk rating | Sets the deadline and the order of work |
| Identified and scheduled completion dates | The tracker checks the gap against the policy window |
| Milestones | At least one, all due on or before the completion date |
| Resources | Hours or dollars, so the system owner can fund it |
| One point of contact | A named person, not a team |

## 3. Status values

| Status | Meaning |
|---|---|
| Open | Accepted onto the POA&M; work not started |
| In Progress | At least one milestone underway or done |
| Closed | Fixed, with closure evidence checked by the ISSO (ISP-CA 4.5) |
| Risk Accepted | Will not be fixed; deviation approved by the CIO with an expiry (ISP-CA 4.6) |

The **flag** is calculated, never typed: Overdue, Due Soon (14 days or less), On Track, Closed, or
Risk Accepted. Typing "On Track" by hand hides problems. Calculating it from dates doesn't.

## 4. Deviations

| Type | When to use it | Example |
|---|---|---|
| Operational requirement | The fix would break something the business needs, or the platform can't do it | POAM-0010: the managed load balancer can't hide its product header |
| False positive | The weakness doesn't actually exist; attach proof | (none in this POA&M) |
| Risk adjustment | Compensating controls lower the risk rating; the item stays open at the new rating | (none in this POA&M) |

Only an operational requirement leads to Risk Accepted. Acceptances expire after 12 months at
most, and the tracker flags one that has expired.

## 5. Monthly reporting

The ISSO runs `python src/poam_tracker.py --as-of <date> --write reports/poam_status_<yyyy-mm>.md`
and sends it to the CIO (ISP-CA 4.4). The report puts **overdue items and overdue milestones first,
by name and owner**, because that's what leadership can act on. Next come items due in the next
two weeks, then the full list.

## 6. Closing an item

1. The point of contact finishes the last milestone and attaches proof: a rescan, a re-run test,
   or a configuration export.
2. The ISSO checks the proof. For assessment findings, the ISSO re-performs the original test
   where possible. For AHR-2026-001, that means re-running the AC-2(3) test in
   [control-audit-evidence-kit](https://github.com/CauseSpark/control-audit-evidence-kit).
3. Set Status to Closed, record the completion date and evidence, and re-score the matching
   risk in the [risk register](https://github.com/CauseSpark/risk-assessment-800-30).

## Sources

- [NIST SP 800-53 Rev 5, CA-5 Plan of Action and Milestones](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)
- [NIST SP 800-37 Rev 2, Risk Management Framework](https://csrc.nist.gov/pubs/sp/800/37/r2/final)
