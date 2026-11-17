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

from poam_tracker import AS_OF, DUE_SOON_DAYS, MILESTONES, PARAMS, POAM, RISKS, STATUSES, load_windows, read_csv

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "output" / "acme_hr_portal_poam_tracker.xlsx"
FONT = "Arial"
FIRST, CAP = 5, 100
LAST = FIRST + CAP - 1
ASOF_CELL = "Dashboard!$C$4"
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


def put(ws, ref, value, **style):
    """Write a value in the workbook font and return the cell."""
    cell = ws[ref]
    cell.value = value
    cell.font = font(**style)
    return cell


def header(cell, text):
    cell.value = text
    cell.font = font(bold=True, color="FFFFFF")
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    cell.border = BORDER


def title(ws, text, sub):
    put(ws, "A1", text, bold=True, size=14, color="1F3864")
    put(ws, "A2", sub, italic=True, color="595959")


def widths(ws, **columns):
    for letter, width in columns.items():
        ws.column_dimensions[letter].width = width


def span(letter):
    return f"{letter}{FIRST}:{letter}{LAST}"


def highlight(operator, value, fill="C00000", color="FFFFFF"):
    return CellIsRule(operator=operator, formula=[value],
                      fill=PatternFill("solid", fgColor=fill), font=Font(name=FONT, bold=True, color=color))


def flag_formatting(ws, rng):
    for flag, (fill, fcolor) in FLAG_STYLE.items():
        ws.conditional_formatting.add(rng, highlight("equal", f'"{flag}"', fill, fcolor))


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
        "Days Open": lambda r: f'=IF({A}{r}="","",IF({L}{r}<>"",{L}{r},{ASOF_CELL})-{G}{r})',
        "Days to Due": lambda r: f'=IF(OR({A}{r}="",{done(r)}),"",{H}{r}-{ASOF_CELL})',
        "Flag": lambda r: (
            f'=IF({A}{r}="","",IF({done(r)},{K}{r},IF({H}{r}<{ASOF_CELL},"Overdue",'
            f'IF({H}{r}-{ASOF_CELL}<={DUESOON},"Due Soon","On Track"))))'),
        "Open Milestones": lambda r: f'=IF({A}{r}="","",COUNTIFS({ms_rng},{A}{r},{ms_flag},"<>Done"))',
        "Overdue Milestones": lambda r: f'=IF({A}{r}="","",COUNTIFS({ms_rng},{A}{r},{ms_flag},"Overdue"))',
    }


def ms_formulas():
    A, D, E = MC["POA&M ID"], MC["Due"], MC["Completed"]
    return {
        "Days Late": lambda r: f'=IF({A}{r}="","",IF({E}{r}<>"",MAX(0,{E}{r}-{D}{r}),IF({D}{r}<{ASOF_CELL},{ASOF_CELL}-{D}{r},0)))',
        "Flag": lambda r: (f'=IF({A}{r}="","",IF({E}{r}<>"","Done",IF({D}{r}<{ASOF_CELL},"Overdue",'
                           f'IF({D}{r}-{ASOF_CELL}<={DUESOON},"Due Soon","Open"))))'),
    }


def build_rules(wb, windows):
    ws = wb.create_sheet("Rules")
    title(ws, "Rules", "Values come from data/parameters.csv, the same register the policies cite.")
    tables = [  # (heading row, heading, days by rating, parameter IDs)
        (5, "POA&M completion limits (ISP-CA 4.3)", windows["poam"], ["P-CA-01", "P-CA-02", "P-CA-03"]),
        (12, "Flaw remediation windows for scan items (ISP-RA 4.3)", windows["flaw"],
         ["P-SI-01", "P-SI-02", "P-SI-03", "P-SI-04"]),
    ]
    for top, heading, days, pids in tables:
        put(ws, f"B{top}", heading, bold=True)
        for r, (rating, pid) in enumerate(zip(days, pids), start=top + 1):
            put(ws, f"B{r}", rating)
            put(ws, f"C{r}", days[rating], color="0000FF")
            put(ws, f"D{r}", f"days  ({pid})", color="595959")
    put(ws, "B19", "Due-soon threshold", bold=True)
    put(ws, "C19", DUE_SOON_DAYS, color="0000FF")
    put(ws, "D19", "days (tracker setting)", color="595959")
    for col, heading, values in (("B", "Status values", STATUSES), ("C", "Risk values", RISKS)):
        put(ws, f"{col}22", heading, bold=True)
        for r, value in enumerate(values, start=23):
            put(ws, f"{col}{r}", value)
    widths(ws, A=3, B=50, C=12, D=22)


def build_dashboard(wb, as_of):
    ws = wb.active
    ws.title = "Dashboard"
    title(ws, "Acme HR Portal: POA&M Dashboard", "FICTIONAL. Every figure is a formula over the POA&M and Milestones sheets.")
    put(ws, "B4", "As-of date", bold=True)
    c = put(ws, "C4", as_of, bold=True, color="0000FF")
    c.number_format, c.fill, c.alignment = DATE_FMT, INPUT_FILL, Alignment(horizontal="left")
    put(ws, "D4", "Change this date, or type =TODAY() for a live tracker.", italic=True, color="595959")

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
    for ref, text in (("B6", "Measure"), ("C6", "Count"), ("E6", "Active by risk"), ("F6", "Count")):
        header(ws[ref], text)
    for r, (label, formula) in enumerate(rows, start=7):
        put(ws, f"B{r}", label)
        put(ws, f"C{r}", formula, bold=True).border = BORDER
    for ref in ("C8", "C11", "C15"):   # overdue items, overdue milestones, items past the window
        ws.conditional_formatting.add(ref, highlight("greaterThan", "0"))
    for r, rk in enumerate(RISKS, start=7):
        put(ws, f"E{r}", rk)
        put(ws, f"F{r}", f'=COUNTIFS({risk},E{r},{status},"<>Closed",{status},"<>Risk Accepted")', bold=True)
    widths(ws, A=3, B=52, C=12, D=3, E=16, F=10)


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
    for r, (k, v) in enumerate(lines, start=4):
        put(ws, f"A{r}", k, bold=True)
        put(ws, f"B{r}", v).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[r].height = 30
    widths(ws, A=26, B=100)


def build(out: Path = DEFAULT_OUT, as_of: date = AS_OF,
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
    flag_formatting(ws, span(PC["Flag"]))
    ws.conditional_formatting.add(span(PC["Within Window"]), highlight("equal", '"No"'))
    for column, choices in (("Status", "Rules!$B$23:$B$26"), ("Risk", "Rules!$C$23:$C$25")):
        dv = DataValidation(type="list", formula1=choices, allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(span(PC[column]))
    ws.page_setup.orientation = "landscape"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToHeight = 0

    wm = wb.create_sheet("Milestones")
    title(wm, "Milestones", "One row per milestone. Leave Completed blank until it is done.")
    write_rows(wm, MS_COLS, ms, ms_formulas())
    flag_formatting(wm, span(MC["Flag"]))

    build_rules(wb, windows)
    build_instructions(wb)
    wb.calculation.fullCalcOnLoad = True
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Build the Excel POA&M tracker")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--as-of", type=date.fromisoformat, default=AS_OF)
    args = p.parse_args(argv)
    print(f"wrote {build(args.out, args.as_of)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
