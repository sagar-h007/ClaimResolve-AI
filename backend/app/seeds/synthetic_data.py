import os
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.claim import Claim, ClaimStatus
from app.models.document import Document, DocumentChunk, DocumentCategory, DocumentStatus
from app.models.analysis import ClaimAnalysis, EvidenceReference, AnalysisStatus, EvidenceStrength
from app.models.appeal import AppealLetter, AppealVersion, AppealStatus
from app.services.auth_service import get_password_hash
from app.ai.embedding_provider import get_embedding_provider
from app.config import settings

PATIENTS_DATA = [
    {"first": "Eleanor", "last": "Vance", "dob": "1974-03-12", "gender": "Female", "policy": "POL-****-1029", "payer": "United Healthcare"},
    {"first": "Marcus", "last": "Chen", "dob": "1982-11-25", "gender": "Male", "policy": "POL-****-8391", "payer": "Anthem Blue Cross"},
    {"first": "Sophia", "last": "Rodriguez", "dob": "1968-07-09", "gender": "Female", "policy": "POL-****-4920", "payer": "Aetna"},
    {"first": "James", "last": "Thorne", "dob": "1955-01-30", "gender": "Male", "policy": "POL-****-9482", "payer": "Cigna"},
    {"first": "Hannah", "last": "Kim", "dob": "1991-09-14", "gender": "Female", "policy": "POL-****-3019", "payer": "Humana"},
    {"first": "Robert", "last": "Taylor", "dob": "1963-04-18", "gender": "Male", "policy": "POL-****-5521", "payer": "United Healthcare"},
    {"first": "Olivia", "last": "Brown", "dob": "1988-12-03", "gender": "Female", "policy": "POL-****-7182", "payer": "Anthem Blue Cross"},
    {"first": "David", "last": "Wilson", "dob": "1971-08-22", "gender": "Male", "policy": "POL-****-2910", "payer": "Aetna"},
    {"first": "Emily", "last": "Davis", "dob": "1995-05-17", "gender": "Female", "policy": "POL-****-6391", "payer": "Cigna"},
    {"first": "Michael", "last": "Miller", "dob": "1959-10-05", "gender": "Male", "policy": "POL-****-8472", "payer": "Humana"},
    {"first": "Sarah", "last": "Martinez", "dob": "1985-02-14", "gender": "Female", "policy": "POL-****-1928", "payer": "United Healthcare"},
    {"first": "William", "last": "Anderson", "dob": "1978-06-29", "gender": "Male", "policy": "POL-****-9381", "payer": "Anthem Blue Cross"},
    {"first": "Jessica", "last": "Thomas", "dob": "1992-11-11", "gender": "Female", "policy": "POL-****-4820", "payer": "Aetna"},
    {"first": "Christopher", "last": "Jackson", "dob": "1965-03-08", "gender": "Male", "policy": "POL-****-7561", "payer": "Cigna"},
    {"first": "Amanda", "last": "White", "dob": "1983-09-21", "gender": "Female", "policy": "POL-****-3109", "payer": "Humana"},
    {"first": "Daniel", "last": "Harris", "dob": "1976-12-19", "gender": "Male", "policy": "POL-****-6821", "payer": "United Healthcare"},
    {"first": "Ashley", "last": "Martin", "dob": "1989-04-02", "gender": "Female", "policy": "POL-****-2490", "payer": "Anthem Blue Cross"},
    {"first": "Matthew", "last": "Thompson", "dob": "1961-07-27", "gender": "Male", "policy": "POL-****-8172", "payer": "Aetna"},
    {"first": "Jennifer", "last": "Garcia", "dob": "1994-01-16", "gender": "Female", "policy": "POL-****-5390", "payer": "Cigna"},
    {"first": "Anthony", "last": "Robinson", "dob": "1972-08-31", "gender": "Male", "policy": "POL-****-9018", "payer": "Humana"},
]

SCENARIOS = [
    {
        "title": "Scenario 1: Medical Necessity Dispute (Failed Conservative Therapy Exists)",
        "payer": "United Healthcare",
        "cpt": ["29881"],
        "icd": ["M23.22"],
        "denial_code": "CO-50",
        "denial_reason": "Denied citing CO-50: Procedure deemed not medically necessary due to absence of documented 6-week conservative physical therapy regimen.",
        "claim_amount": 5400.0,
        "denied_amount": 4850.0,
        "clinical_note": (
            "PHYSICAL THERAPY DISCHARGE SUMMARY & CLINICAL PROGRESS NOTE\n"
            "Patient: Eleanor Vance | DOB: 1974-03-12 | Attending: Dr. Keith Armstrong, MD\n"
            "Diagnosis: Right knee complex posterior horn medial meniscus tear (ICD-10 M23.22).\n"
            "Clinical Course: Patient completed 16 structured physical therapy sessions between May 14, 2025 and July 09, 2025 (8 consecutive weeks). "
            "Treatment included quad strengthening, hamstring stretching, proprioception training, and ultrasound modalities. "
            "Outcome: Persistent mechanical locking, antalgic gait, and refractory pain (VAS 8/10). Failed trial of oral Meloxicam 15mg daily.\n"
            "Conclusion: Patient has exhausted conservative care exceeding payer 6-week threshold. Arthroscopic meniscectomy is medically necessary."
        ),
        "policy_text": (
            "UNITED HEALTHCARE CLINICAL POLICY BULLETIN: KNEE ARTHROSCOPY (SECTION 4.2)\n"
            "Coverage Criteria for CPT 29881 (Arthroscopic Partial Meniscectomy):\n"
            "1. Objective physical exam confirming joint line tenderness, positive McMurray's sign, or locking.\n"
            "2. MRI confirmation of structural meniscal tear.\n"
            "3. Completion of at least 6 weeks of supervised conservative physical therapy without meaningful functional recovery."
        ),
        "denial_letter": (
            "EXPLANATION OF BENEFITS & DENIAL REMITTANCE NOTICE\n"
            "Claim #: CLM-2025-0814 | Member: Eleanor Vance | Policy: POL-****-1029\n"
            "Denied Code: CO-50 (Non-covered service deemed not medically necessary).\n"
            "Explanation: Documentation submitted with prior authorization request did not establish compliance with CPB Section 4.2 conservative trial duration."
        )
    },
    {
        "title": "Scenario 2: Missing Clinical Documentation (Operative Notes Available in EHR)",
        "payer": "Anthem Blue Cross",
        "cpt": ["22551", "22853"],
        "icd": ["M50.20"],
        "denial_code": "CO-16",
        "denial_reason": "Denied citing CO-16: Claim lacks required clinical operative report and certified neuro-monitoring logs for spinal fusion instrumentation.",
        "claim_amount": 24800.0,
        "denied_amount": 19200.0,
        "clinical_note": (
            "OPERATIVE REPORT & INTRAOPERATIVE NEUROMONITORING CERTIFICATION\n"
            "Patient: Marcus Chen | Procedure: Anterior Cervical Discectomy & Fusion (ACDF) C5-C6 with intervertebral cage insertion.\n"
            "Surgeon: Dr. Allison Bradley, MD, FACS | Facility: Memorial Regional Surgery Pavilion.\n"
            "Findings: Severe cervical disc extrusion with severe cord compression and intractable radiculopathy. "
            "Continuous multi-channel SSEP and MEP intraoperative monitoring was maintained throughout the procedure without signal latency compromise."
        ),
        "policy_text": (
            "ANTHEM BLUE CROSS CLINICAL GUIDELINE CG-SURG-73: CERVICAL SPINE INTERVENTIONS\n"
            "Reimbursement for CPT 22551 and 22853 requires submission of full transcribed operative report detailing hardware placement and certified intraoperative neuro-monitoring logs."
        ),
        "denial_letter": (
            "ANTHEM BLUE CROSS REMITTANCE ADVICE\n"
            "Claim Reference: CLM-2025-0922 | Denial Code: CO-16\n"
            "Reason: Claim lacks information needed for adjudication. Attached operative reports were illegible or missing pages 3-4."
        )
    },
    {
        "title": "Scenario 3: Incorrect Billing Code / Unbundling Dispute",
        "payer": "Aetna",
        "cpt": ["43239", "43235"],
        "icd": ["K21.9"],
        "denial_code": "CO-4",
        "denial_reason": "Denied citing CO-4: Procedure code unbundling. Diagnostic endoscopy (43235) was billed simultaneously with upper GI endoscopy biopsy (43239).",
        "claim_amount": 3200.0,
        "denied_amount": 1450.0,
        "clinical_note": (
            "ENDOSCOPY OPERATIVE LOG & CLINICAL DOCUMENTATION\n"
            "Patient: Sophia Rodriguez | Procedure: EGD with targeted cold forceps biopsy of gastroesophageal junction.\n"
            "Endoscopist: Dr. Raymond Vance, MD | Indication: Refractory GERD with dysphagia.\n"
            "Operative Details: Biopsy was performed on suspicious Barrett's mucosa at 36cm. Diagnostic evaluation preceded biopsy. Coding correction: CPT 43239 represents the comprehensive service; CPT 43235 should be adjusted or appended with distinct site modifier if separate anatomical lesion."
        ),
        "policy_text": (
            "AETNA REIMBURSEMENT POLICY: NCCI EDITS & ENDOSCOPY BUNDLING\n"
            "Under CMS National Correct Coding Initiative guidelines, CPT 43235 is a component of comprehensive code CPT 43239 and is mutually exclusive unless distinct anatomic site or session is substantiated with Modifier -59 or -X{EPSU}."
        ),
        "denial_letter": (
            "AETNA HEALTH INSURANCE CLAIM DETERMINATION\n"
            "Claim #: CLM-2025-0104 | Denial Code: CO-4\n"
            "Explanation: The procedure code is inconsistent with the modifier used or a required modifier is missing. Unbundled component."
        )
    },
    {
        "title": "Scenario 4: Procedure Did Not Meet Payer Coverage Criteria",
        "payer": "Cigna",
        "cpt": ["64483"],
        "icd": ["M54.5"],
        "denial_code": "CO-197",
        "denial_reason": "Denied citing CO-197: Transforaminal lumbar epidural steroid injection did not satisfy criteria regarding prior fluoroscopic documentation and diagnostic imaging timeline within 12 months.",
        "claim_amount": 2900.0,
        "denied_amount": 2400.0,
        "clinical_note": (
            "PAIN MANAGEMENT INTERVENTIONAL SUITE NOTE\n"
            "Patient: James Thorne | Attending: Dr. Elena Rostova, MD\n"
            "Procedure: L4-L5 Right Transforaminal Epidural Steroid Injection under Continuous Fluoroscopic Guidance.\n"
            "Clinical Details: High-resolution fluoroscopy utilized with non-ionic Isovue contrast confirming right L4 nerve root epidurogram. Lumbar MRI dated 02/10/2025 (within 6 months of date of service) demonstrates neuroforaminal stenosis."
        ),
        "policy_text": (
            "CIGNA MEDICAL COVERAGE POLICY 0514: SPINAL INJECTIONS\n"
            "Coverage Criteria for Transforaminal Epidural Steroid Injections (CPT 64483):\n"
            "1. Imaging study (MRI or CT) of the lumbar spine performed within the preceding 12 months confirming nerve root impingement.\n"
            "2. Injection performed under continuous fluoroscopic or CT guidance with contrast documentation.\n"
            "3. Pain persistence despite at least 4 weeks of comprehensive conservative therapy."
        ),
        "denial_letter": (
            "CIGNA HEALTHCARE ADVERSE BENEFIT DETERMINATION\n"
            "Claim #: CLM-2025-0551 | Denial Code: CO-197\n"
            "Determination: Precertification criteria not met. Records submitted did not reflect fluoroscopic imaging verification."
        )
    }
]


async def seed_synthetic_data(db: AsyncSession, organization_id: str, admin_user_id: str):
    """Seed comprehensive synthetic healthcare dataset into the specified organization."""
    embedder = get_embedding_provider()

    # 1. Create 20 synthetic patients
    patient_records = []
    for i, p in enumerate(PATIENTS_DATA):
        ext_id = f"PT-{10000 + i}"
        pat = Patient(
            organization_id=organization_id,
            external_patient_id=ext_id,
            first_name=p["first"],
            last_name=p["last"],
            dob=p["dob"],
            gender=p["gender"],
            insurance_policy_number=p["policy"],
            payer_name=p["payer"],
        )
        db.add(pat)
        patient_records.append(pat)

    await db.flush()

    # 2. Seed 4 detailed scenario claims with documents, analysis, and appeal letters
    for s_idx, sc in enumerate(SCENARIOS):
        pat = patient_records[s_idx % len(patient_records)]
        claim_num = f"CLM-2025-0{814 + s_idx * 108}"

        claim = Claim(
            organization_id=organization_id,
            patient_id=pat.id,
            claim_number=claim_num,
            payer_name=sc["payer"],
            policy_number_masked=pat.insurance_policy_number or "POL-****-8812",
            procedure_codes=sc["cpt"],
            diagnosis_codes=sc["icd"],
            claim_amount=sc["claim_amount"],
            denied_amount=sc["denied_amount"],
            denial_date="2025-08-15",
            denial_reason=sc["denial_reason"],
            denial_code=sc["denial_code"],
            claim_status=ClaimStatus.APPEAL_DRAFTED if s_idx < 2 else ClaimStatus.ANALYSIS_COMPLETE,
            notes=f"Synthetic Evaluation Scenario #{s_idx + 1}: {sc['title']}",
        )
        db.add(claim)
        await db.flush()

        # Ingest Denial Letter Document
        denial_doc = Document(
            organization_id=organization_id,
            claim_id=claim.id,
            category=DocumentCategory.DENIAL_LETTER,
            filename=f"Denial_Notice_{claim_num}.txt",
            original_filename=f"Denial_Letter_{claim_num}.pdf",
            file_path=os.path.join(settings.UPLOAD_DIR, "synthetic", f"denial_{claim_num}.txt"),
            file_size_bytes=len(sc["denial_letter"]),
            mime_type="text/plain",
            page_count=1,
            status=DocumentStatus.PROCESSED,
            metadata_json={"scenario": s_idx + 1},
        )
        db.add(denial_doc)
        await db.flush()

        # Ingest Clinical Notes Document
        clinical_doc = Document(
            organization_id=organization_id,
            claim_id=claim.id,
            category=DocumentCategory.CLINICAL_RECORD,
            filename=f"Clinical_Notes_{pat.external_patient_id}.txt",
            original_filename=f"Patient_EHR_Records_{pat.external_patient_id}.pdf",
            file_path=os.path.join(settings.UPLOAD_DIR, "synthetic", f"clinical_{pat.external_patient_id}.txt"),
            file_size_bytes=len(sc["clinical_note"]),
            mime_type="text/plain",
            page_count=3,
            status=DocumentStatus.PROCESSED,
            metadata_json={"scenario": s_idx + 1},
        )
        db.add(clinical_doc)
        await db.flush()

        # Ingest Payer Policy Document
        policy_doc = Document(
            organization_id=organization_id,
            claim_id=claim.id,
            category=DocumentCategory.PAYER_POLICY,
            filename=f"Payer_Policy_{sc['payer'].replace(' ', '_')}.txt",
            original_filename=f"{sc['payer']}_Clinical_Policy_Bulletin.pdf",
            file_path=os.path.join(settings.UPLOAD_DIR, "synthetic", f"policy_{sc['payer']}.txt"),
            file_size_bytes=len(sc["policy_text"]),
            mime_type="text/plain",
            page_count=8,
            status=DocumentStatus.PROCESSED,
            metadata_json={"scenario": s_idx + 1},
        )
        db.add(policy_doc)
        await db.flush()

        # Create Chunks & Embeddings for Clinical Doc
        c_emb = await embedder.get_embedding(sc["clinical_note"])
        chunk_c = DocumentChunk(
            document_id=clinical_doc.id,
            chunk_index=0,
            page_number=2,
            content=sc["clinical_note"],
            token_count=len(sc["clinical_note"].split()),
            embedding=c_emb,
            metadata_json={"page": 2, "source": clinical_doc.original_filename},
        )
        db.add(chunk_c)

        # Create Chunks & Embeddings for Policy Doc
        p_emb = await embedder.get_embedding(sc["policy_text"])
        chunk_p = DocumentChunk(
            document_id=policy_doc.id,
            chunk_index=0,
            page_number=4,
            content=sc["policy_text"],
            token_count=len(sc["policy_text"].split()),
            embedding=p_emb,
            metadata_json={"page": 4, "source": policy_doc.original_filename},
        )
        db.add(chunk_p)
        await db.flush()

        # Create AI Claim Analysis Record
        analysis = ClaimAnalysis(
            claim_id=claim.id,
            organization_id=organization_id,
            status=AnalysisStatus.COMPLETED,
            denial_reason=sc["denial_reason"],
            denial_code=sc["denial_code"],
            payer_explanation=f"Payer remittance assertion: {sc['denial_reason']}",
            policy_section="Clinical Policy Bulletin Section 4: Coverage Requirements",
            policy_requirements_summary=f"Mandatory prerequisites according to {sc['payer']} policy: documented conservative regimen and diagnostic findings.",
            clinical_findings_summary=f"EHR verified for {pat.first_name} {pat.last_name}: Documented treatment timeline and operative findings directly refute denial grounds.",
            evidence_strength=EvidenceStrength.STRONG if s_idx < 2 else EvidenceStrength.MODERATE,
            missing_evidence=[] if s_idx < 3 else ["Fluoroscopic contrast confirmation printout"],
            conflicting_information=[
                f"Payer asserted lack of conservative care; however, {clinical_doc.original_filename} Page 2 contains certified discharge documentation."
            ] if s_idx == 0 else [],
            potential_appeal_arguments=[
                "Direct factual rebuttal of denial grounds using certified medical records.",
                "Compliance with all prerequisites outlined under Payer Clinical Policy Bulletin.",
                "Request for Level 1 expedited clinical reconsideration by board-certified specialist."
            ],
            recommended_next_steps=[
                "Dispatch formal written appeal letter with Exhibit A & B attached.",
                "Follow up with Payer Appeals Coordinator within 14 calendar days."
            ],
            risk_indicators=[
                "Confirm physician signature stamp is visible on submitted attachments."
            ],
            raw_llm_output={},
        )
        db.add(analysis)
        await db.flush()

        # Create Evidence Reference Citations
        ev_ref = EvidenceReference(
            analysis_id=analysis.id,
            chunk_id=chunk_c.id,
            document_id=clinical_doc.id,
            document_type="clinical_record",
            source_document_title=clinical_doc.original_filename,
            page_number="Page 2",
            citation_text=sc["clinical_note"][:220] + "...",
            extracted_text=sc["clinical_note"][:220] + "...",
            relevance_score=0.96,
            is_supporting=True,
        )
        db.add(ev_ref)

        # Create Appeal Letter for Scenarios 1 & 2
        if s_idx < 2:
            appeal = AppealLetter(
                claim_id=claim.id,
                organization_id=organization_id,
                analysis_id=analysis.id,
                title=f"Formal Level 1 Appeal — Claim #{claim_num}",
                status=AppealStatus.DRAFT if s_idx == 1 else AppealStatus.APPROVED,
                current_version=1,
                provider_info={
                    "facility_name": "Memorial Regional Health System",
                    "department": "Department of Patient Financial Services & Utilization Review",
                    "address": "1000 Medical Center Parkway, Suite 400",
                    "phone": "(800) 555-4920",
                    "fax": "(800) 555-4921",
                    "npi": "1942859102",
                },
                patient_info={
                    "patient_reference_id": pat.external_patient_id,
                    "first_name": pat.first_name,
                    "last_name": pat.last_name,
                    "dob": pat.dob,
                    "policy_number_masked": pat.insurance_policy_number,
                    "payer_name": sc["payer"],
                },
                claim_info={
                    "claim_number": claim_num,
                    "procedure_codes": sc["cpt"],
                    "diagnosis_codes": sc["icd"],
                    "claim_amount": sc["claim_amount"],
                    "denied_amount": sc["denied_amount"],
                    "denial_date": "2025-08-15",
                },
                original_denial_details={
                    "denial_code": sc["denial_code"],
                    "denial_reason": sc["denial_reason"],
                    "policy_section": "Section 4.2: Coverage Guidelines",
                },
                clinical_justification=(
                    f"The medical record establishes clear medical necessity for {', '.join(sc['cpt'])}. "
                    f"As verified in {clinical_doc.original_filename} (Page 2), patient completed all necessary prerequisites."
                ),
                policy_references=f"Under {sc['payer']} Clinical Policy Bulletin, coverage is explicitly authorized upon meeting clinical criteria.",
                supporting_evidence=f"• {clinical_doc.original_filename} (Page 2): Verified clinical care and diagnostic findings.",
                request_for_reconsideration=(
                    f"We respectfully request that the adverse determination for Claim #{claim_num} in the amount of "
                    f"${sc['denied_amount']:,.2f} be overturned and paid in full."
                ),
                supporting_document_references=[
                    {
                        "title": clinical_doc.original_filename,
                        "page": "Page 2",
                        "relevance": 0.96,
                    }
                ],
                full_letter_text=(
                    f"FORMAL MEDICAL NECESSITY APPEAL — LEVEL 1 RECONSIDERATION\n"
                    f"DATE: November 14, 2025\n\n"
                    f"TO: {sc['payer']} Appeals and Grievances Department\n\n"
                    f"RE: APPEAL OF CLAIM DENIAL #{claim_num}\n"
                    f"    Patient: {pat.first_name} {pat.last_name} | DOB: {pat.dob} | Member ID: {pat.insurance_policy_number}\n"
                    f"    Billed Codes: {', '.join(sc['cpt'])} | Diagnosis: {', '.join(sc['icd'])}\n"
                    f"    Denied Amount: ${sc['denied_amount']:,.2f}\n\n"
                    f"Dear Medical Director:\n\n"
                    f"We are formally appealing the denial of Claim #{claim_num} citing Denial Code {sc['denial_code']}.\n\n"
                    f"1. FACTUAL REBUTTAL OF DENIAL GROUNDS\n"
                    f"The denial explanation stated that the patient failed to meet criteria. This assertion is factually refuted by the clinical medical record:\n"
                    f"As documented in {clinical_doc.original_filename} (Page 2): \"{sc['clinical_note'][:220]}...\"\n\n"
                    f"2. GOVERNING POLICY SATISFACTION\n"
                    f"Under {sc['payer']} guidelines, all required conservative trials and diagnostic exams were verified prior to surgical intervention.\n\n"
                    f"3. REQUEST FOR RECONSIDERATION\n"
                    f"In light of the enclosed evidence, please reverse this denial and process reimbursement of ${sc['denied_amount']:,.2f} at contracted rates.\n\n"
                    f"Sincerely,\nUtilization Review Committee\nMemorial Regional Health System"
                ),
                approved_by_user_id=admin_user_id if s_idx == 0 else None,
                approved_at=datetime.now(timezone.utc) if s_idx == 0 else None,
            )
            db.add(appeal)
            await db.flush()

            ver = AppealVersion(
                appeal_id=appeal.id,
                version_number=1,
                full_letter_text=appeal.full_letter_text,
                edited_by_user_id=admin_user_id,
                change_summary="Initial AI-generated evidence appeal draft",
            )
            db.add(ver)

    # 3. Create remaining 26 claims across the cohort to reach 30 claims total
    payers = ["United Healthcare", "Anthem Blue Cross", "Aetna", "Cigna", "Humana"]
    denial_codes = ["CO-50", "CO-16", "CO-4", "CO-197", "CO-97", "CO-18"]
    cpt_pools = [["99214"], ["73721"], ["29881"], ["27447"], ["99285"], ["45380"]]
    icd_pools = [["M25.561"], ["M23.22"], ["M17.11"], ["R10.9"], ["K21.9"]]

    for c_i in range(len(SCENARIOS), 30):
        pat = patient_records[c_i % len(patient_records)]
        denied_amt = round(800.0 + (c_i * 370.0) % 9500.0, 2)
        total_amt = round(denied_amt * 1.25, 2)
        code = denial_codes[c_i % len(denial_codes)]

        stat = (
            ClaimStatus.APPROVED if c_i % 4 == 0 else
            ClaimStatus.APPEAL_DRAFTED if c_i % 3 == 0 else
            ClaimStatus.ANALYSIS_COMPLETE if c_i % 2 == 0 else
            ClaimStatus.UPLOADED
        )

        c = Claim(
            organization_id=organization_id,
            patient_id=pat.id,
            claim_number=f"CLM-2025-0{700 + c_i}",
            payer_name=payers[c_i % len(payers)],
            policy_number_masked=pat.insurance_policy_number or "POL-****-9102",
            procedure_codes=cpt_pools[c_i % len(cpt_pools)],
            diagnosis_codes=icd_pools[c_i % len(icd_pools)],
            claim_amount=total_amt,
            denied_amount=denied_amt,
            denial_date="2025-09-01",
            denial_reason=f"Claim rejected under code {code} during automated payer adjudication.",
            denial_code=code,
            claim_status=stat,
            notes=f"Cohort claim #{c_i + 1}",
        )
        db.add(c)

    await db.commit()

