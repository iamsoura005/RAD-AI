import os
import html
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm


def _safe_text(value: object) -> str:
    text = "" if value is None else str(value)
    return html.escape(text).replace("\n", "<br/>")


def generate_report(data: dict, filename: str) -> str:
    """
    Build a clean, professional PDF report.
    data keys: prediction, confidence, modality, gemini, model_status
    Returns the output path.
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    doc = SimpleDocTemplate(filename, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("Title", parent=styles["Title"],
                                 fontSize=20, spaceAfter=6)
    subtitle_style = ParagraphStyle("Sub", parent=styles["Normal"],
                                    fontSize=10, textColor=colors.grey)
    section_style = ParagraphStyle("Section", parent=styles["Heading2"],
                                   fontSize=13, spaceBefore=14, spaceAfter=4,
                                   textColor=colors.HexColor("#4f46e5"))
    body_style = ParagraphStyle("Body", parent=styles["Normal"],
                                fontSize=10, leading=15)
    bullet_style = ParagraphStyle("Bullet", parent=body_style,
                                  leftIndent=16, bulletIndent=0)

    gemini = data.get("gemini", {})
    prediction = data.get("prediction")
    if isinstance(prediction, dict):
        pred_label = prediction.get("label", "—")
        pred_conf = prediction.get("confidence", 0)
    else:
        pred_label = prediction or "—"
        pred_conf = data.get("confidence", 0)
    risk = str(gemini.get("risk_level", "Unknown"))
    risk_color = {"High": colors.red, "Medium": colors.orange,
                  "Low": colors.green}.get(risk, colors.grey)

    story = [
        Paragraph("RadiAI — Medical Analysis Report", title_style),
        Paragraph(f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}", subtitle_style),
        Spacer(1, 0.4*cm),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb")),
        Spacer(1, 0.4*cm),

        # --- Summary Table ---
        Paragraph("Scan Summary", section_style),
        Table(
            [
                ["Modality",    _safe_text(data.get("modality", "—").replace("_", " ").title())],
                ["Prediction",  _safe_text(pred_label)],
                ["Confidence",  f"{round(float(pred_conf) * 100, 1)}%"],
                ["Risk Level",  _safe_text(risk)],
                ["Model Status", _safe_text(data.get("model_status", "—"))],
            ],
            colWidths=[5*cm, 11*cm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1),
                 [colors.white, colors.HexColor("#f9fafb")]),
                ("TEXTCOLOR", (1, 3), (1, 3), risk_color),
                ("FONTNAME", (1, 3), (1, 3), "Helvetica-Bold"),
            ])
        ),
        Spacer(1, 0.5*cm),

        # --- AI Explanation ---
        Paragraph("AI Explanation (Gemini)", section_style),
        Paragraph(_safe_text(gemini.get("report", "Not available.")), body_style),
        Spacer(1, 0.3*cm),

        # --- Key Findings ---
        # --- Short Summary ---
        Paragraph("Summary for Patient", section_style),
        Paragraph(_safe_text(gemini.get("summary", "Not available.")), body_style),
        Spacer(1, 0.5*cm),

        HRFlowable(width="100%", thickness=0.5, color=colors.grey),
        Spacer(1, 0.2*cm),
        Paragraph(
            "<font size='8' color='grey'>⚠ This report is AI-generated and is intended for informational "
            "purposes only. It is NOT a substitute for professional medical diagnosis.</font>",
            body_style
        ),
    ]

    doc.build(story)
    return filename
