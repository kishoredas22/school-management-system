"""PDF receipt and salary slip generation."""

from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.branding import SCHOOL_NAME, SCHOOL_SHORT_NAME


def _currency(value: Any) -> str:
    amount = Decimal(str(value))
    return f"Rs {amount:,.2f}"


def _school_seal(size: float = 34 * mm) -> Drawing:
    drawing = Drawing(size, size)
    center = size / 2
    drawing.add(Circle(center, center, size * 0.48, fillColor=colors.HexColor("#efe1b7"), strokeColor=colors.HexColor("#b58d44"), strokeWidth=3))
    drawing.add(Circle(center, center, size * 0.36, fillColor=colors.HexColor("#163b71"), strokeColor=colors.HexColor("#b58d44"), strokeWidth=2))

    for offset in range(-5, 6):
        x = center + (offset * size * 0.035)
        drawing.add(Line(center, center, x, size * 0.78, strokeColor=colors.HexColor("#e0b86a"), strokeWidth=1))

    drawing.add(
        Polygon(
            [
                size * 0.28,
                size * 0.42,
                size * 0.48,
                size * 0.49,
                size * 0.48,
                size * 0.68,
                size * 0.28,
                size * 0.61,
            ],
            fillColor=colors.HexColor("#f4e8c5"),
            strokeColor=colors.HexColor("#7a5524"),
            strokeWidth=1.5,
        )
    )
    drawing.add(
        Polygon(
            [
                size * 0.52,
                size * 0.49,
                size * 0.72,
                size * 0.42,
                size * 0.72,
                size * 0.61,
                size * 0.52,
                size * 0.68,
            ],
            fillColor=colors.HexColor("#f8eed5"),
            strokeColor=colors.HexColor("#7a5524"),
            strokeWidth=1.5,
        )
    )
    drawing.add(Line(size * 0.50, size * 0.48, size * 0.64, size * 0.62, strokeColor=colors.HexColor("#0e233d"), strokeWidth=3))
    drawing.add(Line(size * 0.64, size * 0.62, size * 0.69, size * 0.70, strokeColor=colors.HexColor("#0e233d"), strokeWidth=1.5))
    drawing.add(Rect(size * 0.16, size * 0.06, size * 0.68, size * 0.14, rx=6, ry=6, fillColor=colors.HexColor("#163b71"), strokeColor=colors.HexColor("#b58d44"), strokeWidth=1.5))
    drawing.add(String(center, size * 0.11, SCHOOL_SHORT_NAME, fontName="Helvetica-Bold", fontSize=size * 0.11, fillColor=colors.white, textAnchor="middle"))
    return drawing


def _school_logo_path() -> Path:
    return Path(__file__).resolve().parents[2] / "frontend" / "src" / "assets" / "vsk-logo.webp"


def _school_mark(size: float = 34 * mm):
    logo_path = _school_logo_path()
    if logo_path.exists():
        try:
            ImageReader(str(logo_path))
            return Image(str(logo_path), width=size, height=size)
        except Exception:
            pass
    return _school_seal(size)


def _base_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="SchoolTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#163b71"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocumentLabel",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#26253b"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="MetaCopy",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#555269"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionLabel",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=colors.HexColor("#163b71"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SlipHeroLabel",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#d9e3fb"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="SlipHeroAmount",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=20,
            textColor=colors.white,
        )
    )
    return styles


def _build_document(title: str, tables: list[Table], meta_lines: list[str]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title=title,
    )
    styles = _base_styles()

    story = [
        Table(
            [
                [
                    _school_mark(),
                    [
                        Paragraph(SCHOOL_NAME, styles["SchoolTitle"]),
                        Paragraph(title, styles["DocumentLabel"]),
                        Paragraph("Academic operations and payroll record", styles["MetaCopy"]),
                    ],
                ]
            ],
            colWidths=[42 * mm, 130 * mm],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            ),
        ),
        Spacer(1, 8 * mm),
    ]

    if meta_lines:
        for line in meta_lines:
            story.append(Paragraph(line, styles["MetaCopy"]))
        story.append(Spacer(1, 6 * mm))

    for index, table in enumerate(tables):
        story.append(table)
        if index != len(tables) - 1:
            story.append(Spacer(1, 5 * mm))

    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph("Authorized Signature ____________________", styles["MetaCopy"]))

    doc.build(story)
    return buffer.getvalue()


def _styled_table(rows: list[list[str]], *, header: bool = False, col_widths: list[float] | None = None) -> Table:
    table = Table(rows, colWidths=col_widths, hAlign="LEFT")
    palette = [
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#d2c3a0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.7, colors.HexColor("#e7dcc1")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3eddc") if header else colors.white),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#26253b")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("LEADING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]
    if header:
        palette.append(("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"))
        palette.append(("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#163b71")))
    table.setStyle(TableStyle(palette))
    return table


def generate_fee_receipt(payload: dict[str, Any]) -> bytes:
    """Create a printable fee receipt PDF."""

    details = _styled_table(
        [
            ["Field", "Value"],
            ["Receipt number", str(payload["receipt_number"])],
            ["Student name", str(payload["student_name"])],
            ["Student ID", str(payload["student_id"])],
            ["Academic year", str(payload["academic_year"])],
            ["Class", str(payload["class_name"])],
            ["Paid amount", _currency(payload["paid_amount"])],
            ["Pending balance", _currency(payload["pending_balance"])],
            ["Payment mode", str(payload["payment_mode"])],
        ],
        header=True,
        col_widths=[52 * mm, 110 * mm],
    )
    return _build_document("Student Fee Receipt", [details], [])


def generate_salary_slip(payload: dict[str, Any]) -> bytes:
    """Create a printable teacher salary slip PDF."""

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title="Teacher Salary Slip",
    )
    styles = _base_styles()

    header = Table(
        [
            [
                _school_mark(),
                [
                    Paragraph(SCHOOL_NAME, styles["SchoolTitle"]),
                    Paragraph("Teacher Salary Slip", styles["DocumentLabel"]),
                    Paragraph(
                        "Salary payment record for payroll, attendance, and backoffice review.",
                        styles["MetaCopy"],
                    ),
                ],
            ]
        ],
        colWidths=[42 * mm, 130 * mm],
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        ),
    )

    payout_box = Table(
        [
            [Paragraph("Current payment", styles["SlipHeroLabel"])],
            [Paragraph(_currency(payload["paid_amount"]), styles["SlipHeroAmount"])],
            [Paragraph(f"Receipt {payload['receipt_number']}", styles["SlipHeroLabel"])],
        ],
        colWidths=[58 * mm],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#163b71")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#163b71")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        ),
    )

    employee_table = Table(
        [
            ["Employee name", str(payload["teacher_name"])],
            ["Phone", str(payload.get("teacher_phone") or "-")],
            ["Salary month", str(payload["salary_month"])],
            ["Academic year", str(payload["academic_year"])],
            ["Payment date", str(payload["payment_date"])],
            ["Payment mode", str(payload["payment_mode"])],
        ],
        colWidths=[38 * mm, 66 * mm],
        style=TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#d2c3a0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.7, colors.HexColor("#e7dcc1")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f6f0e1")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#26253b")),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        ),
    )

    compensation_table = Table(
        [
            ["Compensation summary", "Amount"],
            ["Monthly salary", _currency(payload.get("monthly_salary", 0))],
            ["Current payment", _currency(payload["paid_amount"])],
            [f"Paid for {payload['salary_month']}", _currency(payload["paid_for_month"])],
            ["Paid year to date", _currency(payload["paid_year_to_date"])],
            ["Annual contract total", _currency(payload.get("contract_total", 0))],
            ["Remaining annual balance", _currency(payload["remaining_balance"])],
        ],
        colWidths=[96 * mm, 66 * mm],
        style=TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#d2c3a0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.7, colors.HexColor("#e7dcc1")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3eddc")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#26253b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#163b71")),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        ),
    )

    attendance_table = Table(
        [
            ["Attendance reference", "Value"],
            ["Days worked", str(payload["days_worked"])],
            ["Total days in month", str(payload["total_days_in_month"])],
            [
                "Attendance note",
                f"Worked days are counted from PRESENT entries recorded for {payload['salary_month']}.",
            ],
        ],
        colWidths=[48 * mm, 114 * mm],
        style=TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#d2c3a0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.7, colors.HexColor("#e7dcc1")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef4ff")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#163b71")),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#26253b")),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        ),
    )

    declaration = Table(
        [
            [
                Paragraph(
                    "This slip confirms the salary payment recorded in the ERP for the month shown above.",
                    styles["MetaCopy"],
                )
            ]
        ],
        colWidths=[162 * mm],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#faf5ea")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e7dcc1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        ),
    )

    story = [
        header,
        Spacer(1, 8 * mm),
        Table(
            [[employee_table, payout_box]],
            colWidths=[104 * mm, 58 * mm],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            ),
        ),
        Spacer(1, 6 * mm),
        compensation_table,
        Spacer(1, 5 * mm),
        attendance_table,
        Spacer(1, 5 * mm),
        declaration,
        Spacer(1, 14 * mm),
        Paragraph("Employee Signature ____________________", styles["MetaCopy"]),
        Spacer(1, 8 * mm),
        Paragraph("Authorized Signature ____________________", styles["MetaCopy"]),
    ]

    doc.build(story)
    return buffer.getvalue()


def generate_report_card(payload: dict[str, Any]) -> bytes:
    """Create a printable student report card PDF."""

    summary_rows = [
        ["Student", str(payload["student_name"]), "Student ID", str(payload.get("student_code") or "-")],
        ["Exam", str(payload["exam_name"]), "Term", str(payload.get("term_label") or "-")],
        ["Academic year", str(payload["academic_year_name"]), "Class / Section", f"{payload['class_name']}{f' / {payload['section_name']}' if payload.get('section_name') else ''}"],
        ["Total marks", str(payload["total_marks"]), "Obtained", str(payload["obtained_marks"])],
        ["Percentage", f"{payload['percentage']}%", "Overall grade", str(payload.get("overall_grade") or "-")],
        ["Result", str(payload["result"]), "Remark", str(payload.get("overall_remark") or "-")],
    ]
    summary = _styled_table(
        [["Field", "Value", "Field", "Value"], *summary_rows],
        header=True,
        col_widths=[32 * mm, 49 * mm, 32 * mm, 49 * mm],
    )

    subject_rows = [["Subject", "Max", "Pass", "Obtained", "Result"]]
    for row in payload["subject_rows"]:
        subject_rows.append(
            [
                str(row["subject_name"]),
                str(row["max_marks"]),
                str(row["pass_marks"]),
                "ABSENT" if row.get("is_absent") else str(row.get("marks_obtained") or "-"),
                str(row["result"]),
            ]
        )
    subject_table = _styled_table(
        subject_rows,
        header=True,
        col_widths=[72 * mm, 20 * mm, 20 * mm, 25 * mm, 25 * mm],
    )
    return _build_document(
        "Student Report Card",
        [summary, subject_table],
        ["This report card is generated from published exam marks and grade rules configured for the academic year."],
    )
