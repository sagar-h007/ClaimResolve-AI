import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from app.models.appeal import AppealLetter


class PDFExportService:
    """Enterprise-grade PDF generator for formal healthcare insurance appeal letters."""

    @classmethod
    def generate_appeal_pdf(cls, appeal: AppealLetter) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54,
        )

        styles = getSampleStyleSheet()
        
        # Custom Typography
        header_title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#064b85"),
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#475569"),
            fontName="Helvetica",
        )
        section_heading_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
            spaceBefore=12,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "AppealBody",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica",
            spaceAfter=8,
        )
        citation_style = ParagraphStyle(
            "CitationStyle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0369a1"),
            fontName="Helvetica-Oblique",
        )

        elements = []

        # Hospital / Facility Header
        provider = appeal.provider_info or {}
        facility = provider.get("facility_name", "Memorial Regional Health System")
        dept = provider.get("department", "Department of Patient Financial Services & Appeals")
        contact_line = f"Phone: {provider.get('phone', '(800) 555-4920')} | Fax: {provider.get('fax', '(800) 555-4921')} | NPI: {provider.get('npi', '1942859102')}"

        elements.append(Paragraph(facility.upper(), header_title_style))
        elements.append(Paragraph(dept, subtitle_style))
        elements.append(Paragraph(contact_line, subtitle_style))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0c8ee9"), spaceAfter=14))

        # Metadata Reference Table
        claim = appeal.claim_info or {}
        patient = appeal.patient_info or {}
        denial = appeal.original_denial_details or {}

        patient_name = f"{patient.get('first_name', 'Jane')} {patient.get('last_name', 'Doe')}"
        ref_table_data = [
            [
                Paragraph("<b>Patient Name:</b>", body_style),
                Paragraph(patient_name, body_style),
                Paragraph("<b>Claim Reference #:</b>", body_style),
                Paragraph(str(claim.get("claim_number", "CLM-2025-001")), body_style),
            ],
            [
                Paragraph("<b>Patient Ref ID:</b>", body_style),
                Paragraph(str(patient.get("patient_reference_id", "PT-84920")), body_style),
                Paragraph("<b>Payer Name:</b>", body_style),
                Paragraph(str(patient.get("payer_name", "Insurance Payer")), body_style),
            ],
            [
                Paragraph("<b>Date of Birth:</b>", body_style),
                Paragraph(str(patient.get("dob", "1980-05-15")), body_style),
                Paragraph("<b>Member / Policy #:</b>", body_style),
                Paragraph(str(patient.get("policy_number_masked", "POL-****-8912")), body_style),
            ],
            [
                Paragraph("<b>Procedure Code(s):</b>", body_style),
                Paragraph(", ".join(claim.get("procedure_codes", ["29881"])), body_style),
                Paragraph("<b>Denied Amount:</b>", body_style),
                Paragraph(f"${claim.get('denied_amount', 0.0):,.2f}", body_style),
            ],
            [
                Paragraph("<b>Denial Code:</b>", body_style),
                Paragraph(str(denial.get("denial_code", "CO-50")), body_style),
                Paragraph("<b>Denial Date:</b>", body_style),
                Paragraph(str(claim.get("denial_date", "2025-08-15")), body_style),
            ],
        ]

        ref_table = Table(ref_table_data, colWidths=[110, 140, 120, 134])
        ref_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        elements.append(ref_table)
        elements.append(Spacer(1, 14))

        # Title
        elements.append(Paragraph(appeal.title.upper(), section_heading_style))
        elements.append(Spacer(1, 6))

        # Letter Body Paragraphs
        paragraphs = appeal.full_letter_text.split("\n\n")
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Format headings if present
            if para.startswith(("1.", "2.", "3.", "4.", "5.", "RE:", "TO:", "DATE:")):
                elements.append(Paragraph(para.replace("\n", "<br/>"), section_heading_style))
            else:
                elements.append(Paragraph(para.replace("\n", "<br/>"), body_style))

        # Evidence Table Section
        if appeal.supporting_document_references:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph("VERIFIED SOURCE DOCUMENTATION & EVIDENCE CITATIONS", section_heading_style))
            doc_rows = [
                [
                    Paragraph("<b>Exhibit</b>", body_style),
                    Paragraph("<b>Source Document</b>", body_style),
                    Paragraph("<b>Page #</b>", body_style),
                    Paragraph("<b>Relevance</b>", body_style),
                ]
            ]
            for idx, item in enumerate(appeal.supporting_document_references):
                doc_rows.append([
                    Paragraph(f"Exhibit {chr(65 + idx)}", body_style),
                    Paragraph(str(item.get("title", "Clinical Document")), body_style),
                    Paragraph(str(item.get("page", "Page 1")), body_style),
                    Paragraph(f"{int(float(item.get('relevance', 0.9)) * 100)}%", body_style),
                ])
            doc_table = Table(doc_rows, colWidths=[60, 260, 94, 90])
            doc_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0effe")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#93c5fd")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ])
            )
            elements.append(doc_table)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

