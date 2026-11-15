"""Build the Excel POA&M tracker from the CSV files.

Everything time-based keys off one As-of date cell on the Dashboard. Type =TODAY()
there and the tracker stays current on its own: days open, days to due, overdue
flags, milestone status, and the dashboard counts are all formulas.

    python src/build_tracker.py
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from poam_tracker import DUE_SOON_DAYS, MILESTONES, PARAMS, POAM, RISKS, STATUSES, load_windows, read_csv  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "output" / "acme_hr_portal_poam_tracker.xlsx"
FONT = "Arial"
FIRST, CAP = 5, 100
LAST = FIRST + CAP - 1
ASOF = "Dashboard!$C$4"
DUESOON = "Rules!$C$19"
DATE_FMT = "yyyy-mm-dd"

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
CALC_FILL = PatternFill("solid", fgColor="F2F2F2")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
FLAG_STYLE = {
    "Overdue": ("C00000", "FFFFFF"),
    "Due Soon": ("FFD966", "000000"),
    "On Track": ("B6D7A8", "000000"),
    "Closed": ("D9D9D9", "000000"),
    "Risk Accepted": ("BDD7EE", "000000"),
    "Done": ("D9D9D9", "000000"),
    "Open": ("FFFFFF", "000000"),
}


def font(bold=False, color="000000", size=10, italic=False):
    return Font(name=FONT, bold=bold, color=color, size=size, italic=italic)


def header(cell, text):
    cell.value = text
    cell.font = font(bold=True, color="FFFFFF")
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    cell.border = BORDER


def title(ws, text, sub):
    ws["A1"] = text
    ws["A1"].font = font(bold=True, size=14, color="1F3864")
    ws["A2"] = sub
    ws["A2"].font = font(italic=True, color="595959")


def flag_formatting(ws, rng):
    for flag, (fill, fcolor) in FLAG_STYLE.items():
        ws.conditional_formatting.add(rng, CellIsRule(
            operator="equal", formula=[f'"{flag}"'],
            fill=PatternFill("solid", fgColor=fill), font=Font(name=FONT, bold=True, color=fcolor)))


def as_date(v):
    return date.fromisoformat(v) if v else None


# (header, width, kind, csv column or None)
POAM_COLS = [
    ("POA&M ID", 11, "text", "poam_id"),
    ("Source Ref", 14, "text", "source_ref"),
    ("Source", 22, "text", "source"),
    ("Control", 10, "text", "control"),
    ("Weakness", 42, "text", "weakness"),
    ("Risk", 10, "input", "risk_rating"),
    ("Identified", 12, "date", "identified_date"),
    ("Scheduled Completion", 13, "date", "scheduled_completion_date"),
    ("Resources Required", 24, "text", "resources_required"),
    ("Point of Contact", 22, "text", "point_of_contact"),
    ("Status", 13, "input", "status"),
    ("Completion Date", 12, "date", "completion_date"),
    ("Closure Evidence", 30, "text", "closure_evidence"),
    ("Deviation Type", 16, "text", "deviation_type"),
    ("Deviation Approved By", 22, "text", "deviation_approved_by"),
    ("Deviation Expires", 12, "date", "deviation_expires"),
    ("Comments", 36, "text", "comments"),
    ("Window (days)", 9, "formula", None),
    ("Within Window", 9, "formula", None),
    ("Days Open", 9, "formula", None),
    ("Days to Due", 9, "formula", None),
    ("Flag", 13, "formula", None),
    ("Open Milestones", 10, "formula", None),
    ("Overdue Milestones", 10, "formula", None),
]
PC = {h: get_column_letter(i + 1) for i, (h, *_rest) in enumerate(POAM_COLS)}

MS_COLS = [
    ("POA&M ID", 11, "text", "poam_id"),
    ("Milestone", 10, "text", "milestone"),
    ("Description", 50, "text", "description"),
    ("Due", 12, "date", "due_date"),
    ("Completed", 12, "date", "completed_date"),
    ("Days Late", 9, "formula", None),
    ("Flag", 11, "formula", None),
]
MC = {h: get_column_letter(i + 1) for i, (h, *_rest) in enumerate(MS_COLS)}


def write_rows(ws, cols, rows, formulas):
    for j, (h, w, kind, _) in enumerate(cols):
        header(ws.cell(row=4, column=j + 1), h)
        ws.column_dimensions[get_column_letter(j + 1)].width = w
    ws.row_dimensions[4].height = 32
    for i in range(CAP):
        r = FIRST + i
        data = rows[i] if i < len(rows) else {}
        for j, (h, _, kind, key) in enumerate(cols):
            cell = ws.cell(row=r, column=j + 1)
            if kind == "formula":
                cell.value = formulas[h](r)
                cell.fill = CALC_FILL
            else:
                v = data.get(key) or None
                cell.value = as_date(v) if kind == "date" and v else v
                if kind == "input":
                    cell.fill = INPUT_FILL
            cell.font = font(color="0000FF" if kind == "input" else "000000")
            cell.border = BORDER
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            if kind == "date":
                cell.number_format = DATE_FMT
    ws.freeze_panes = f"B{FIRST}"
    ws.auto_filter.ref = f"A4:{get_column_letter(len(cols))}{LAST}"


def poam_formulas():
    A, C, F, G, H = PC["POA&M ID"], PC["Source"], PC["Risk"], PC["Identified"], PC["Scheduled Completion"]
    K, L = PC["Status"], PC["Completion Date"]
    R = PC["Window (days)"]
    done = lambda r: f'OR({K}{r}="Closed",{K}{r}="Risk Accepted")'  # noqa: E731
    ms_rng = f"Milestones!${MC['POA&M ID']}${FIRST}:${MC['POA&M ID']}${LAST}"
    ms_flag = f"Milestones!${MC['Flag']}${FIRST}:${MC['Flag']}${LAST}"
    return {
        "Window (days)": lambda r: (
            f'=IF({A}{r}="","",IF(LEFT({C}{r},11)="Weekly scan",'
            f'INDEX(Rules!$C$13:$C$16,MATCH({F}{r},Rules!$B$13:$B$16,0)),'
            f'INDEX(Rules!$C$6:$C$8,MATCH({F}{r},Rules!$B$6:$B$8,0))))'),
        "Within Window": lambda r: f'=IF({A}{r}="","",IF({H}{r}-{G}{r}<={R}{r},"Yes","No"))',
        "Days Open": lambda r: f'=IF({A}{r}="","",IF({L}{r}<>"",{L}{r},{ASOF})-{G}{r})',
        "Days to Due": lambda r: f'=IF(OR({A}{r}="",{done(r)}),"",{H}{r}-{ASOF})',
        "Flag": lambda r: (
            f'=IF({A}{r}="","",IF({done(r)},{K}{r},IF({H}{r}<{ASOF},"Overdue",'
            f'IF({H}{r}-{ASOF}<={DUESOON},"Due Soon","On Track"))))'),
        "Open Milestones": lambda r: f'=IF({A}{r}="","",COUNTIFS({ms_rng},{A}{r},{ms_flag},"<>Done"))',
        "Overdue Milestones": lambda r: f'=IF({A}{r}="","",COUNTIFS({ms_rng},{A}{r},{ms_flag},"Overdue"))',
    }


def ms_formulas():
    A, D, E = MC["POA&M ID"], MC["Due"], MC["Completed"]
    return {
        "Days Late": lambda r: f'=IF({A}{r}="","",IF({E}{r}<>"",MAX(0,{E}{r}-{D}{r}),IF({D}{r}<{ASOF},{ASOF}-{D}{r},0)))',
        "Flag": lambda r: (f'=IF({A}{r}="","",IF({E}{r}<>"","Done",IF({D}{r}<{ASOF},"Overdue",'
                           f'IF({D}{r}-{ASOF}<={DUESOON},"Due Soon","Open"))))'),
    }


def build_rules(wb, windows):
    ws = wb.create_sheet("Rules")
    title(ws, "Rules", "Values come from data/parameters.csv, the same register the policies cite.")
    ws["B5"].value = "POA&M completion limits (ISP-CA 4.3)"
    ws["B5"].font = font(bold=True)
    for i, (risk, pid) in enumerate(zip(RISKS, ["P-CA-01", "P-CA-02", "P-CA-03"])):
        ws.cell(row=6 + i, column=2, value=risk).font = font()
        c = ws.cell(row=6 + i, column=3, value=windows["poam"][risk])
        c.font = font(color="0000FF")
        ws.cell(row=6 + i, column=4, value=f"days  ({pid})").font = font(color="595959")
    ws["B12"].value = "Flaw remediation windows for scan items (ISP-RA 4.3)"
    ws["B12"].font = font(bold=True)
    for i, (sev, pid) in enumerate(zip(["Critical", "High", "Moderate", "Low"], ["P-SI-01", "P-SI-02", "P-SI-03", "P-SI-04"])):
        ws.cell(row=13 + i, column=2, value=sev).font = font()
        c = ws.cell(row=13 + i, column=3, value=windows["flaw"][sev])
        c.font = font(color="0000FF")
        ws.cell(row=13 + i, column=4, value=f"days  ({pid})").font = font(color="595959")
    ws["B19"].value = "Due-soon threshold"
    ws["B19"].font = font(bold=True)
    ws["C19"].value = DUE_SOON_DAYS
    ws["C19"].font = font(color="0000FF")
    ws["D19"].value = "days (tracker setting)"
    ws["D19"].font = font(color="595959")
    ws["B22"].value = "Status values"
    ws["B22"].font = font(bold=True)
    for i, s in enumerate(STATUSES):
        ws.cell(row=23 + i, column=2, value=s).font = font()
    ws["C22"].value = "Risk values"
    ws["C22"].font = font(bold=True)
    for i, r in enumerate(RISKS):
        ws.cell(row=23 + i, column=3, value=r).font = font()
    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 50
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 22


def build_dashboard(wb, as_of):
    ws = wb.active
    ws.title = "Dashboard"
    title(ws, "Acme HR Portal: POA&M Dashboard", "FICTIONAL. Every figure is a formula over the POA&M and Milestones sheets.")
    ws["B4"] = "As-of date"
    ws["B4"].font = font(bold=True)
    ws["C4"] = as_of
    ws["C4"].number_format = DATE_FMT
    ws["C4"].fill = INPUT_FILL
    ws["C4"].font = font(bold=True, color="0000FF")
    ws["D4"] = "Change this date, or type =TODAY() for a live tracker."
    ws["D4"].font = font(italic=True, color="595959")

    rng = lambda h: f"'POA&M'!${PC[h]}${FIRST}:${PC[h]}${LAST}"  # noqa: E731
    flag, status, risk = rng("Flag"), rng("Status"), rng("Risk")
    rows = [
        ("Active items", f'=COUNTA({rng("POA&M ID")})-COUNTIF({status},"Closed")-COUNTIF({status},"Risk Accepted")'),
        ("Overdue items", f'=COUNTIF({flag},"Overdue")'),
        ("Due soon", f'=COUNTIF({flag},"Due Soon")'),
        ("On track", f'=COUNTIF({flag},"On Track")'),
        ("Overdue milestones", f'=SUM({rng("Overdue Milestones")})'),
        ("Closed", f'=COUNTIF({flag},"Closed")'),
        ("Risk accepted", f'=COUNTIF({flag},"Risk Accepted")'),
        ("Oldest active item (days open)",
         f'=_xlfn.MAXIFS({rng("Days Open")},{status},"<>Closed",{status},"<>Risk Accepted")'),
        ("Items scheduled past the policy window (should be 0)", f'=COUNTIF({rng("Within Window")},"No")'),
    ]
    header(ws["B6"], "Measure")
    header(ws["C6"], "Count")
    for i, (label, f) in enumerate(rows):
        ws.cell(row=7 + i, column=2, value=label).font = font()
        c = ws.cell(row=7 + i, column=3, value=f)
        c.font = font(bold=True)
        c.border = BORDER
    ws.conditional_formatting.add("C8", CellIsRule(operator="greaterThan", formula=["0"],
                                  fill=PatternFill("solid", fgColor="C00000"), font=Font(name=FONT, bold=True, color="FFFFFF")))
    ws.conditional_formatting.add("C11", CellIsRule(operator="greaterThan", formula=["0"],
                                  fill=PatternFill("solid", fgColor="C00000"), font=Font(name=FONT, bold=True, color="FFFFFF")))
    ws.conditional_formatting.add("C15", CellIsRule(operator="greaterThan", formula=["0"],
                                  fill=PatternFill("solid", fgColor="C00000"), font=Font(name=FONT, bold=True, color="FFFFFF")))

    header(ws["E6"], "Active by risk")
    header(ws["F6"], "Count")
    for i, rk in enumerate(RISKS):
        ws.cell(row=7 + i, column=5, value=rk).font = font()
        ws.cell(row=7 + i, column=6,
                value=f'=COUNTIFS({risk},E{7 + i},{status},"<>Closed",{status},"<>Risk Accepted")').font = font(bold=True)
    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 52
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 3
    ws.column_dimensions["E"].width = 16
    ws.column_dimensions["F"].width = 10
    ws["C4"].alignment = Alignment(horizontal="left")


def build_instructions(wb):
    ws = wb.create_sheet("Instructions")
    title(ws, "How to use this tracker", "Acme HR Portal POA&M. Fictional study material by Peyton Seay.")
    lines = [
        ("As-of date", "Dashboard C4. Every time-based formula uses it. Type =TODAY() to keep the tracker live."),
        ("Inputs (yellow, blue text)", "Risk and Status are dropdowns. Other plain cells are typed entries: dates as YYYY-MM-DD."),
        ("Formulas (grey)", "Window, Within Window, Days Open, Days to Due, Flag, and milestone counts. Do not type over them."),
        ("Add an item", "Fill the next empty row on the POA&M sheet, then add at least one milestone on the Milestones sheet."),
        ("Close an item", "Set Status to Closed, enter the completion date, and describe the evidence that the fix works (ISP-CA 4.5)."),
        ("Accept risk", "Set Status to Risk Accepted, then fill in the deviation type, the CIO approval with its date, and an expiry no more than 12 months out (ISP-CA 4.6)."),
        ("Within Window = No", "The scheduled date is later than policy allows. Pull the date in or get a documented extension."),
        ("Source of truth", "poam/poam.csv and poam/milestones.csv. This workbook is generated from them by src/build_tracker.py."),
    ]
    for i, (k, v) in enumerate(lines):
        ws.cell(row=4 + i, column=1, value=k).font = font(bold=True)
        c = ws.cell(row=4 + i, column=2, value=v)
        c.font = font()
        c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[4 + i].height = 30
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 100


def build(out: Path = DEFAULT_OUT, as_of: date = date(2026, 11, 15),
          poam_path: Path = POAM, ms_path: Path = MILESTONES, params_path: Path = PARAMS) -> Path:
    poam, ms = read_csv(poam_path), read_csv(ms_path)
    if len(poam) > CAP or len(ms) > CAP:
        raise ValueError(f"tracker holds {CAP} items and {CAP} milestones")
    windows = load_windows(params_path)
    wb = Workbook()
    build_dashboard(wb, as_of)

    ws = wb.create_sheet("POA&M")
    title(ws, "Plan of Action and Milestones", "Columns A-Q are the record; R-X are calculated.")
    write_rows(ws, POAM_COLS, poam, poam_formulas())
    flag_formatting(ws, f"{PC['Flag']}{FIRST}:{PC['Flag']}{LAST}")
    ws.conditional_formatting.add(f"{PC['Within Window']}{FIRST}:{PC['Within Window']}{LAST}", CellIsRule(
        operator="equal", formula=['"No"'], fill=PatternFill("solid", fgColor="C00000"), font=Font(name=FONT, color="FFFFFF", bold=True)))
    dv_status = DataValidation(type="list", formula1="Rules!$B$23:$B$26", allow_blank=True)
    dv_risk = DataValidation(type="list", formula1="Rules!$C$23:$C$25", allow_blank=True)
    ws.add_data_validation(dv_status)
    ws.add_data_validation(dv_risk)
    dv_status.add(f"{PC['Status']}{FIRST}:{PC['Status']}{LAST}")
    dv_risk.add(f"{PC['Risk']}{FIRST}:{PC['Risk']}{LAST}")
    ws.page_setup.orientation = "landscape"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToHeight = 0

    wm = wb.create_sheet("Milestones")
    title(wm, "Milestones", "One row per milestone. Leave Completed blank until it is done.")
    write_rows(wm, MS_COLS, ms, ms_formulas())
    flag_formatting(wm, f"{MC['Flag']}{FIRST}:{MC['Flag']}{LAST}")

    build_rules(wb, windows)
    build_instructions(wb)
    wb.calculation.fullCalcOnLoad = True
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Build the Excel POA&M tracker")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--as-of", type=date.fromisoformat, default=date(2026, 11, 15))
    args = p.parse_args(argv)
    print(f"wrote {build(args.out, args.as_of)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
