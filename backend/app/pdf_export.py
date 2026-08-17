from datetime import datetime
import tempfile
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph


NAVY = colors.HexColor("#1F3864")
LIGHT_GRAY = colors.HexColor("#F2F2F2")


def _fmt_time(dt):
    if not dt:
        return ""
    return dt.strftime("%H:%M")


def _fmt_duration(seconds):
    if not seconds:
        return ""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h{m:02d}"


def _fmt_date(dt):
    if not dt:
        return ""
    return dt.strftime("%d/%m/%Y")


def build_timesheet_pdf(pointages, date_from=None, date_to=None, period_label=None):
    tmp_path = tempfile.mktemp(suffix=".pdf")

    try:
        doc = SimpleDocTemplate(
            tmp_path,
            pagesize=landscape(A4),
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=20 * mm,
            bottomMargin=15 * mm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=16,
            textColor=NAVY,
            spaceAfter=4 * mm,
        )
        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.gray,
            spaceAfter=8 * mm,
        )

        elements = []

        period_label = period_label or ""
        if not period_label:
            if date_from and date_to:
                period_label = f"Du {date_from} au {date_to}"
            elif date_from:
                period_label = f"Depuis le {date_from}"
            elif date_to:
                period_label = f"Jusqu'au {date_to}"
            else:
                period_label = "Toutes les periodes"

        elements.append(Paragraph("Feuille de pointage", title_style))
        elements.append(Paragraph(
            f"Periode : {period_label} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Genere le {_fmt_date(datetime.utcnow())} a {_fmt_time(datetime.utcnow())}",
            subtitle_style,
        ))

        header = [
            "Employe",
            "Matricule",
            "Date",
            "Arrivee",
            "Depart",
            "Pause",
            "Duree totale",
            "Statut",
        ]
        data = [header]

        for p in pointages:
            duration = None
            if p.clock_in and p.clock_out:
                total = int((p.clock_out - p.clock_in).total_seconds()) - (p.total_break_seconds or 0)
                duration = max(total, 0)

            status_map = {
                "in_progress": "En cours",
                "on_break": "En pause",
                "completed": "Termine",
                "flagged": "Anomalie",
            }

            data.append([
                p.employee_name if hasattr(p, "employee_name") else "",
                p.employee_matricule if hasattr(p, "employee_matricule") else "",
                _fmt_date(p.clock_in),
                _fmt_time(p.clock_in),
                _fmt_time(p.clock_out) if p.clock_out else "En cours",
                _fmt_duration(p.total_break_seconds) if p.total_break_seconds else "-",
                _fmt_duration(duration) if duration else "-",
                status_map.get(p.status, p.status),
            ])

        if len(data) == 1:
            data.append(["", "", "", "", "", "", "", "Aucun pointage"])

        col_widths = [55 * mm, 25 * mm, 25 * mm, 22 * mm, 22 * mm, 22 * mm, 25 * mm, 25 * mm]

        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))

        elements.append(table)
        doc.build(elements)

        with open(tmp_path, "rb") as f:
            pdf_bytes = f.read()

        return pdf_bytes
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
