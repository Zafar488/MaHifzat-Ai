"""
Generate comprehensive, professional PDF technical & viva defense guide for MaaHifazat AI
Team: Algo Titans | Lead: Zafar Ullah
"""
from pathlib import Path
import os
import sys

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = ROOT / "MaaHifazat_AI_Technical_Guide.pdf"


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "MaaHifazat AI — Technical Guide & Viva Defense (Algo Titans)")
            self.setStrokeColor(colors.HexColor("#00897b"))
            self.setLineWidth(0.75)
            self.line(54, 748, 558, 748)
        
        # Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "Confidential — Hackathon Presentation & Technical Defense Document")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=50,
        rightMargin=50,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    
    # Custom color palette
    primary = colors.HexColor("#0e4d64")
    teal = colors.HexColor("#00897b")
    dark_gray = colors.HexColor("#1e293b")
    accent_red = colors.HexColor("#b71c1c")
    slate = colors.HexColor("#475569")
    bg_card = colors.HexColor("#f8fafc")
    border_card = colors.HexColor("#cbd5e1")
    
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=23,
        leading=27,
        textColor=primary,
        alignment=1,
        spaceAfter=8,
    )
    
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=teal,
        alignment=1,
        spaceAfter=15,
    )
    
    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=primary,
        spaceBefore=14,
        spaceAfter=7,
        keepWithNext=True,
    )
    
    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=teal,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    
    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=dark_gray,
        spaceAfter=5,
    )
    
    bold_body_style = ParagraphStyle(
        "BoldBody_Custom",
        parent=body_style,
        fontName="Helvetica-Bold",
    )
    
    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-10,
        spaceAfter=4,
    )
    
    q_style = ParagraphStyle(
        "Question_Style",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13.5,
        textColor=primary,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True,
    )
    
    ans_style = ParagraphStyle(
        "Answer_Style",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=dark_gray,
        spaceAfter=7,
    )

    story = []

    # ─────────────────────────────────────────────────────────────
    # TITLE & METADATA BLOCK
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("MaaHifazat AI — Master Technical & Viva Guide", title_style))
    story.append(Paragraph("Clinical Decision Support & Multi-Agent Platform for Maternal & Fetal Healthcare<br/><b>Team: Algo Titans | Lead: Zafar Ullah</b>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=teal, spaceBefore=2, spaceAfter=10))

    meta_data = [
        [
            Paragraph("<b>Project:</b> MaaHifazat AI (CDSS)", body_style),
            Paragraph("<b>Backend Stack:</b> FastAPI 0.110+, LangGraph 0.2+, Pydantic v2", body_style),
        ],
        [
            Paragraph("<b>Target Audience:</b> Rural BHUs, LHWs & Clinicians", body_style),
            Paragraph("<b>ML Infrastructure:</b> 5 Models, Optuna HPO, Scikit-Learn, LightGBM", body_style),
        ],
        [
            Paragraph("<b>Evaluation Strategy:</b> Group-Split, SMOTE, Macro-F1", body_style),
            Paragraph("<b>LLM Engine:</b> Groq (openai/gpt-oss-120b) Assistive Summaries", body_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[250, 262])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_card),
        ('BOX', (0, 0), (-1, -1), 0.75, border_card),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────────
    # SECTION 1: PROBLEM STATEMENT & CLINICAL CONTEXT
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("1. Problem Statement: The Three Delays Model (Pakistan Context)", h1_style))
    story.append(Paragraph(
        "Pakistan mein Maternal Mortality Ratio (MMR) taqreeban <b>186 per 100,000 live births</b> hai. Har ghantay mein 3 maayein pregnancy aur childbirth ki preventable complications ki wajah se jaan gawa deti hain. Dehaat aur remote Basic Health Units (BHUs) mein specialist gynecologists, continuous CTG machines, aur advanced labs mojood nahi hotein. World Health Organization (WHO) ke mutabiq yeh amwaat <b>'The Three Delays'</b> ki wajah se hoti hain:",
        body_style
    ))

    delays_data = [
        [
            Paragraph("<b>Delay Stage</b>", bold_body_style),
            Paragraph("<b>Ground Reality (Root Cause)</b>", bold_body_style),
            Paragraph("<b>MaaHifazat AI Solution</b>", bold_body_style),
        ],
        [
            Paragraph("<b>Delay 1: Faisla lene mein dair</b><br/>(Seeking Care)", body_style),
            Paragraph("Khatre ki alamat (severe eclampsia, antepartum hemorrhage, reduced fetal movement) ka bar-waqt idraak na hona.", body_style),
            Paragraph("<b>MaternalGuard & FetalWatch:</b> Sirf 6 vitals ya basic CTG se foran high-risk detect karta hai aur WHO Red Flags alert bajata hai.", body_style),
        ],
        [
            Paragraph("<b>Delay 2: Haspataal pohanchne mein dair</b><br/>(Reaching Care)", body_style),
            Paragraph("Yeh na pata hona ke qareebi kis hospital mein ICU, Blood Bank ya C-Section surgeon dastyab hai; ghalat center jana.", body_style),
            Paragraph("<b>Smart Referral Agent:</b> GPS coordinates aur facility capabilities ki base par verified hospital select karta hai aur routing deta hai.", body_style),
        ],
        [
            Paragraph("<b>Delay 3: Ilaj shuru hone mein dair</b><br/>(Receiving Care)", body_style),
            Paragraph("Emergency room pohanch kar paperwork, manual triage aur doctor ke aane tak qeemti golden minutes zaya hona.", body_style),
            Paragraph("<b>Clinician Review & LLM Reporting:</b> Doctor ke pohanchte hi structured clinical summary, risk factors aur actions ready milte hain.", body_style),
        ],
    ]
    t_delays = Table(delays_data, colWidths=[115, 195, 202])
    t_delays.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e0f2f1")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#b2dfdb")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_delays)
    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────────
    # SECTION 2: THE 5 MACHINE LEARNING MODELS
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("2. In-Depth Technical Breakdown of the 5 ML Models", h1_style))
    story.append(Paragraph(
        "Project mein total 5 specialized machine learning models design aur train kiye gaye hain:",
        body_style
    ))

    models_data = [
        [
            Paragraph("<b>Model Name</b>", bold_body_style),
            Paragraph("<b>Clinical Task</b>", bold_body_style),
            Paragraph("<b>Dataset & Features</b>", bold_body_style),
            Paragraph("<b>Algorithm & Performance</b>", bold_body_style),
        ],
        [
            Paragraph("<b>1. FetalWatch</b><br/><i>(Live Served)</i>", body_style),
            Paragraph("Fetal Distress classification (Normal, Suspect, Pathological)", body_style),
            Paragraph("<b>UCI Cardiotocography (2,126 records)</b><br/><b>21 Features:</b> LB (Baseline FHR), AC, FM, UC, DL, DS, DP, ASTV, MSTV, ALTV, MLTV, Histogram metrics (Width, Min, Max, Mode, Mean, Median, Variance, Tendency)", body_style),
            Paragraph("Random Forest / LightGBM / XGBoost<br/><b>Macro-F1: ~0.912</b><br/>AUROC: 0.986<br/>Pre-processed with RobustScaler", body_style),
        ],
        [
            Paragraph("<b>2. MaternalGuard</b><br/><i>(Live Served)</i>", body_style),
            Paragraph("Maternal Health Risk triage (Low, Mid, High Risk)", body_style),
            Paragraph("<b>UCI Maternal Health Risk (1,014 records)</b><br/><b>6 Vitals:</b> Age, SystolicBP (mmHg), DiastolicBP (mmHg), BS (Blood Sugar mmol/L), BodyTemp (F/C), HeartRate (bpm)", body_style),
            Paragraph("Random Forest + LightGBM<br/>Group-split partitioning<br/><b>Macro-F1: ~0.688</b><br/>AUROC: 0.89", body_style),
        ],
        [
            Paragraph("<b>3. PretermGuard</b><br/><i>(Pipeline Ready)</i>", body_style),
            Paragraph("Qabal az waqt paidaish (Preterm Labor) risk assessment", body_style),
            Paragraph("<b>UCI CTG Class Labels</b><br/><b>21 Features:</b> Uterine Contractions (UC), Decelerations, FHR Variability (ASTV/ALTV)", body_style),
            Paragraph("LightGBM + Optuna HPO<br/>SMOTE balancing<br/><b>Macro-F1: ~0.89</b>", body_style),
        ],
        [
            Paragraph("<b>4. CareReach</b><br/><i>(Pipeline Ready)</i>", body_style),
            Paragraph("Antenatal Care (ANC) missed appointment / no-show prediction", body_style),
            Paragraph("<b>Kaggle Medical No-Shows (110,527 records)</b><br/><b>20 Features:</b> Age, Scholarship, Hypertension, Diabetes, booking delta days, dow, comorbidity count", body_style),
            Paragraph("LightGBM + SMOTE-Tomek<br/>SHAP explainability<br/><b>AUROC: ~0.73</b>", body_style),
        ],
        [
            Paragraph("<b>5. GestationInsight</b><br/><i>(Pipeline Ready)</i>", body_style),
            Paragraph("Gestational Diabetes & Metabolic Complications", body_style),
            Paragraph("<b>Gestation Dataset (768 records)</b><br/><b>17 Features:</b> Glucose, MAP (Mean Arterial Pressure), BMI, Insulin-Glucose ratio, estimated SBP", body_style),
            Paragraph("XGBoost + Optuna HPO<br/>SMOTE-Tomek<br/><b>Macro-F1: ~0.78</b>", body_style),
        ],
    ]
    t_models = Table(models_data, colWidths=[90, 115, 175, 132])
    t_models.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0e4d64")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_models)
    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────────
    # SECTION 3: 9-AGENT LANGGRAPH PIPELINE
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("3. 9-Agent LangGraph Multi-Agent Orchestration Workflow", h1_style))
    story.append(Paragraph(
        "MaaHifazat AI mein LangGraph ka <b>StateGraph</b> architecture use kiya gaya hai jahan 9 autonomous agents ek digital clinical board ki tarah step-by-step collaborate karte hain:",
        body_style
    ))

    agent_details = [
        ("1. Clinical Risk Agent (Entry Point)", "<b>Kyu Entry Point hai?</b> WHO emergency protocol ke mutabiq dangerous signs (bleeding, BP >= 160/110, convulsions) aane par mareez ko intazar nahi karwaya jata. Yeh agent sab se pehle WHO Red Flags aur ML models (MaternalGuard) run karta hai. Emergency detect hote hi override flag set karta hai."),
        ("2. Patient Intake Agent", "Mareez ki demographic maloomat (Umar, Gestational Week, GPS Coordinates) aur raw vitals ko medical standards mein normalize karta hai. Fahrenheit ko Celsius mein defend karta hai."),
        ("3. Data Quality Agent", "Checks integrity: Missing vitals scan karta hai, physically impossible vitals (e.g., Systolic < Diastolic ya zero heart rate) ko flag karta hai taake garbage data model tak na jaye."),
        ("4. Fetal Monitoring Agent", "Agar Cardiotocography (CTG) readings provide ki gayi hon, to yeh FetalWatch model invoke karta hai aur fetal distress (Normal / Suspect / Pathological) classify karta hai."),
        ("5. ANC Follow-up Agent", "Risk tier aur gestational age ki bunyad par mandatory antenatal checkups ka clinical timeline plan karta hai."),
        ("6. Smart Referral Agent", "Emergency ya High Risk case mein mareez ke latitude/longitude se verified healthcare centers calculate karta hai jahan ICU, Blood Bank aur C-Section operation theater active hon."),
        ("7. Communication Agent", "Mareez aur frontline Lady Health Worker (LHW) ke liye localized SMS/WhatsApp messages Roman Urdu aur English mein formulate karta hai."),
        ("8. Clinician Review Agent", "Doctor ke liye comprehensive clinical board summary compile karta hai jisme vital trends, risk rationales aur recommended clinical actions structured hotay hain."),
        ("9. Reporting Agent", "Ultra-fast Groq LLM (openai/gpt-oss-120b) ki madad se doctor aur patient-friendly clinical report produce karta hai (strictly non-hallucinatory, assistive only)."),
    ]

    for title, desc in agent_details:
        story.append(Paragraph(f"• <b>{title}:</b> {desc}", bullet_style))

    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────────
    # SECTION 4: ARCHITECTURE & TECHNICAL STACK
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("4. System Architecture & Technical Stack", h1_style))
    
    stack_data = [
        [Paragraph("<b>Layer</b>", bold_body_style), Paragraph("<b>Technology</b>", bold_body_style), Paragraph("<b>Architectural Responsibility</b>", bold_body_style)],
        [Paragraph("REST API", body_style), Paragraph("FastAPI 0.110+", body_style), Paragraph("Asynchronous endpoints, OpenAPI docs, CORS security, sub-10ms response time.", body_style)],
        [Paragraph("Validation", body_style), Paragraph("Pydantic v2", body_style), Paragraph("Strict clinical schema validation (systolic > diastolic, valid temperature bounds).", body_style)],
        [Paragraph("Agent Workflow", body_style), Paragraph("LangGraph 0.2+ / LangChain", body_style), Paragraph("StateGraph state persistence, conditional branch routing, fault-tolerant execution.", body_style)],
        [Paragraph("Machine Learning", body_style), Paragraph("Scikit-Learn, LightGBM, XGBoost", body_style), Paragraph("Pipelines encapsulating Imputer + RobustScaler + Model, preventing data leakage.", body_style)],
        [Paragraph("LLM Engine", body_style), Paragraph("Groq Cloud (gpt-oss-120b)", body_style), Paragraph("Ultra low-latency clinical narratives; temperature 0.3; deterministic fallbacks.", body_style)],
        [Paragraph("Serving Pipeline", body_style), Paragraph("Versioned joblib artifacts", body_style), Paragraph("Parity verification: Known input/output checks; classes matching guarantee.", body_style)],
        [Paragraph("Database", body_style), Paragraph("SQLAlchemy 2.0 (async) + SQLite", body_style), Paragraph("Durable clinical case histories, patient logs, audit trail compliance.", body_style)],
        [Paragraph("Frontend Interfaces", body_style), Paragraph("Streamlit + React 19 / Tailwind", body_style), Paragraph("Dual-mode: Lady Health Worker field tablet UI + Hospital Clinical Dashboard.", body_style)],
    ]
    t_stack = Table(stack_data, colWidths=[90, 165, 257])
    t_stack.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_stack)
    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────────
    # SECTION 5: VIVA & HACKATHON DEFENSE BANK (ROMAN URDU)
    # ─────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("5. Master Technical Q&A Bank for Judges & Viva (Roman Urdu)", h1_style))
    story.append(Paragraph(
        "Jab judges ya technical evaluators aapse deep technical sawalaat poochein, to in answers ko confidently bolna hai. Har sawal aur jawab clinical aur machine learning depth ke sath tayar kiya gaya hai:",
        body_style
    ))

    qa_list = [
        (
            "Q1: Aap ne models train karte waqt Data Leakage se kaise bachaya?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "Humne simple train_test_split use karne ke bajaye <b>GroupShuffleSplit</b> aur <b>StratifiedGroupKFold</b> use kiya. Medical datasets (maternal aur CTG) mein duplicate vitals ya repeated recordings hoti hain. Agar same patient ya identical feature group train aur test dono mein divide ho jaye, to model test set ko 'yaad' kar leta hai aur artificially 99% accuracy dikhata hai jo production mein fail ho jati hai. Humne feature grouping ke zariye test set ko completely unseen rakha, aur preprocessing steps (scaling, imputing) sirf train split par fit kiye."
        ),
        (
            "Q2: Imbalanced Datasets (jaise Pathological CTG cases bohot kam hain) ko kaise handle kiya?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "CTG dataset mein ~78% cases Normal hote hain, aur sirf 8% Pathological hote hain. Is severe imbalance ko resolve karne ke liye do cheezein keen:<br/>"
            "1. <b>SMOTE (Synthetic Minority Over-sampling Technique)</b> aur <b>SMOTE-Tomek</b> training folds par apply kiya taake synthetic minority examples create hon.<br/>"
            "2. Algorithms ke andar <b>class_weight='balanced'</b> configure kiya, jis se model ko Pathological case miss karne par heavy loss penalty milti hai."
        ),
        (
            "Q3: Evaluation ke liye simple Accuracy kyu nahi, Macro-F1 aur AUROC kyu use kiya?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "Medical triage mein simple 'Accuracy' aik khatarnak aur misleading metric hai. Agar 100 pregnant aurton mein se 95 theek hon aur 5 high-risk hon, to agar model har aurat ko 'Normal' keh de to uski accuracy 95% hogi, lekin wo 5 high-risk aurtein beghair ilaj ke mar sakti hain! Is liye humne <b>Macro-F1 Score</b> use kiya jo minority classes ki Precision aur Recall ko equal weightage deta hai, aur <b>AUROC</b> use kiya jo discrimination capability verify karta hai."
        ),
        (
            "Q4: LangGraph kyu use kiya? Simple linear Python script ya If-Else kyu nahi?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "LangGraph aik <b>StateGraph</b> provide karta hai jo cyclic, conditional aur fault-tolerant workflows support karta hai. Clinical pathways linear nahi hote. Agar Data Quality agent ko koi vital missing ya anomalous mile, to wo wapas intake ya clinician par loop-back kar sakta hai. Agar WHO Red Flag trigger ho, to conditional edges normal steps ko bypass karke direct emergency referral trigger karti hain. Iske ilawa har node ka immutable audit trail banta hai jo medical compliance ke liye lazmi hai."
        ),
        (
            "Q5: Entry point 'patient_intake' ke bajaye 'clinical_risk' kyu banaya?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "Yeh aik critical medical design decision hai: Emergency Medicine mein jab mareez bleeding ya fits ke sath aaye, to pehle paperwork nahi bhara jata, pehle triage hota hai! Is liye hamara graph sab se pehle <b>clinical_risk</b> node run karta hai. Agar koi life-threatening WHO red-flag mojood ho, to system foran emergency flag raise kar deta hai chahe baqi intake incomplete hi kyu na ho."
        ),
        (
            "Q6: LLM Hallucination se mareez ko khatra ho sakta hai — aapne isko kaise prevent kiya?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "Hamare architecture mein <b>LLM ko kabhi bhi clinical diagnosis ya prescription dene ki ijazat nahi di gayi</b>. Tamam clinical classification Scikit-learn/LightGBM models aur WHO deterministic safety rules se hoti hai. Groq LLM (gpt-oss-120b) sirf verified numbers aur clinical facts ko simple Urdu aur English sentences mein convert karta hai (temperature 0.3). Agar Groq offline bhi ho jaye, to system template-based text par fallback karta hai."
        ),
        (
            "Q7: Agar gaon/dehaat mein internet connection na ho to yeh system kaise chalega?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "Core ML models Scikit-Learn aur LightGBM pipelines hain jo local CPU par execute hoti hain aur unka inference time under 15 milliseconds hai. Pura triage, risk scoring aur WHO red flag engine <b>100% Offline Edge Device</b> (low-cost laptop ya tablet) par run hota hai. Internet sirf tab zaroori hota hai jab central hospital ko SMS/data sync bhejna ho."
        ),
        (
            "Q8: FetalWatch mein 21 CTG features kaunse hain aur unka clinical role kya hai?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "Cardiotocography (CTG) bache ki dil ki dharkan aur ma ke reham ke dabao ko record karti hai. 21 features mein shamil hain:<br/>"
            "• <b>LB (Baseline FHR):</b> Normal 110-160 bpm hota hai; barhna tachycardia aur girna bradycardia hai.<br/>"
            "• <b>AC (Accelerations):</b> Bache ke move karne par dharkan barhna (healthy sign).<br/>"
            "• <b>UC (Uterine Contractions):</b> Dard-e-zeh ki shiddat aur frequency.<br/>"
            "• <b>DL / DS / DP (Decelerations):</b> Dharkan ka achanak girna. DP (Prolonged deceleration) fetal hypoxia (oxygen ki kami) ka sign hai.<br/>"
            "• <b>ASTV & ALTV:</b> Short-term aur Long-term variability; zero variability brain death ya severe distress show karti hai."
        ),
        (
            "Q9: MaternalGuard mein 6 vitals kaunse hain aur normal thresholds kya hain?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "MaternalGuard 6 non-invasive vitals use karta hai:<br/>"
            "1. <b>Age:</b> Teenager (<18) ya advanced maternal age (>35) high risk hoti hai.<br/>"
            "2. <b>Systolic BP & Diastolic BP:</b> Normal <120/80 mmHg; >=140/90 Gestational Hypertension; >=160/110 Severe Pre-eclampsia Emergency.<br/>"
            "3. <b>Blood Sugar (BS):</b> Normal fasting <5.6 mmol/L; elevated levels Gestational Diabetes indicate karti hain.<br/>"
            "4. <b>Body Temperature:</b> >=38C (100.4F) maternal sepsis ya chorioamnionitis ka khatra hai.<br/>"
            "5. <b>Heart Rate:</b> Resting >100 bpm maternal tachycardia ya hemorrhage show karta hai."
        ),
        (
            "Q10: Serving Pipeline mein 'Parity Check' aur validation kyu rakha gaya hai?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "Serving pipeline bare pickle files ko blind load nahi karti. <b>inference.py</b> mein har load par contract check hota hai: schema version, sklearn version parity, exact feature list, aur aik <b>known_input/known_output check</b>. Agar runtime par model ka result training-time reference prediction se 1e-10 bhi deviate kare, to artifact reject ho jata hai taake silent model drift na ho."
        ),
        (
            "Q11: Agar Machine Learning model kahe 'Low Risk' lekin mareez ko vaginal bleeding ho rahi ho, to kaun jeetega?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "<b>WHO Deterministic Safety Rules hamesha ML model ko override karti hain!</b> Hamare system mein safety rule hardcoded hai: agar vaginal bleeding, convulsions ya BP >= 160/110 ho, to system <b>override_ml_scores = True</b> set karta hai aur triage ko 'HIGH_RISK_EMERGENCY' bana deta hai. Medical software mein statistical probability kabhi bhi clinical red flags ko suppress nahi kar sakti."
        ),
        (
            "Q12: Agar mareez ke vitals incomplete hon to model kya karta hai?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "System kabhi bhi missing features par 'tukka' (silent default zero) nahi lagata. Agar zaroori vitals missing hon, to inference status <b>INSUFFICIENT_DATA</b> return karta hai aur Lady Health Worker ko prompt deta hai ke wo pehle vital signs complete karein."
        ),
        (
            "Q13: CareReach model clinic aur government ke liye kaise beneficial hai?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "Pakistan mein dehaat ki aurtein follow-up visits (ANC checkups) miss kar deti hain jis se hidden complications barh jati hain. CareReach 110,000 records par train hua model hai jo lead time, comorbidities aur past attendance se predict karta hai ke kaunsi mareez visit miss karegi, taake LHW uske ghar ja kar timely follow-up kar sake."
        ),
        (
            "Q14: GestationInsight model metabolic complications kaise pakarta hai?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "Yeh model Mean Arterial Pressure (MAP), Glucose Tolerance Index, aur Insulin-Glucose Ratio calculate karta hai. Yeh early pregnancy mein hi Gestational Diabetes Mellitus (GDM) aur metabolic syndrome ke khatrat ko highlight karta hai."
        ),
        (
            "Q15: Backend architecture mein FastAPI aur Pydantic v2 ka kya advantage hai?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "FastAPI asynchronous concurrency provide karta hai jisse hazaron field workers ek sath requests bhej sakte hain. Pydantic v2 Rust-based validation engine hai jo payload ko parse karta hai — maslan agar kisi vital mein Systolic BP Diastolic se kam ho, to API turant validation error deti hai aur invalid data database ya model tak nahi pohanchta."
        ),
        (
            "Q16: SHAP (SHapley Additive exPlanations) values kyu calculate kiye gaye?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "Doctors machine learning ko 'black-box' hone ki wajah se reject kar dete hain. SHAP values har feature ka mathematical contribution show karti hain — maslan doctor dekh sakta hai ke risk score 85% is liye hua kyunke Systolic BP ne +40% aur Blood Sugar ne +30% push kiya. Yeh transparency clinical trust barhati hai."
        ),
        (
            "Q17: Kya yeh tool doctor ko replace kar raha hai?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "Bilkul nahi! MaaHifazat AI aik <b>Clinical Decision Support System (CDSS)</b> hai — aik AI Co-pilot jo frontline worker aur doctor ke darmiyan bridge banata hai. Final clinical authority hamesha qualified doctor ke paas rehti hai (Human-in-the-Loop)."
        ),
        (
            "Q18: Patient Privacy aur Medical Data Security kaise handle ho rahi hai?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "System HIPAA aur local data protection guidelines follow karta hai. Patient identifiable information (PII) ko models mein feature ke tor par use nahi kiya jata. Database mein case IDs pseudonymous hoti hain aur exception logs mein clinical inputs ko sanitize kiya jata hai."
        ),
        (
            "Q19: Agar judges poochein ke market mein mojood doosre AI apps se aapka project kaise behtar hai?",
            "<b>Answer (Roman Urdu):</b><br/>"
            "Doosre projects sirf aik generic ChatGPT wrapper hote hain jo hallucinations se bhare hote hain. MaaHifazat AI aik <b>Enterprise-Grade, Safety-First CDSS</b> hai jisme:<br/>"
            "1. 5 trained Scikit-learn/LightGBM pipelines hain.<br/>"
            "2. Deterministic WHO red-flag guardrails hain jo ML se zyada authoritative hain.<br/>"
            "3. 9-Agent LangGraph orchestration hai with complete audit trails.<br/>"
            "4. Edge-ready offline capability hai jo rural Pakistan ke BHUs ke liye tailor-made hai."
        ),
    ]

    for q, a in qa_list:
        p_q = Paragraph(f"<b>{q}</b>", q_style)
        p_a = Paragraph(a, ans_style)
        story.append(KeepTogether([p_q, p_a]))

    # ─────────────────────────────────────────────────────────────
    # SECTION 6: DETAILED BREAKDOWN OF ALL 5 MODELS (ROMAN URDU)
    # Kaunsa model kya kya kaam karega, inputs, outputs & clinical value
    # ─────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("6. Har Model Ka Kaam, Inputs, Predictions Aur Clinical Role (In-Depth Guide)", h1_style))
    story.append(Paragraph(
        "Is section mein system ke <b>tamam 5 machine learning models</b> ka mukammal post-mortem diya gaya hai: kaunsa model kya kaam karta hai, uske inputs kya hain, wo kya predict karega, aur real-world BHUs aur hospitals mein uski clinical value kya hai:",
        body_style
    ))
    story.append(Spacer(1, 6))

    model_cards_data = [
        {
            "header": "1. FetalWatch — Fetal Distress & Cardiotocography Classifier (Live Served)",
            "kaam": "Cardiotocography (CTG) sensor data se bache (fetus) ki dil ki dharkan aur ma ke uterus ke dabao ko analyze karke <b>Fetal Distress, Hypoxia (oxygen ki kami)</b> aur intra-uterine asphyxia ko detect karta hai.",
            "inputs": "<b>21 CTG Features:</b><br/>"
                      "• <b>LB (Baseline FHR):</b> Fetal baseline heart rate (110-160 bpm normal).<br/>"
                      "• <b>AC:</b> Accelerations (bache ki movement par dharkan barhna — healthy sign).<br/>"
                      "• <b>FM & UC:</b> Fetal Movements aur Uterine Contractions frequency.<br/>"
                      "• <b>DL, DS, DP:</b> Decelerations (halki, shadeed, aur prolonged >30s drops — acute hypoxia sign).<br/>"
                      "• <b>ASTV / MSTV / ALTV / MLTV:</b> Short-term aur long-term heart rate variability metrics.<br/>"
                      "• <b>Histogram Features:</b> Width, Min, Max, Mode, Mean, Median, Variance, Tendency.",
            "predictions": "<b>3 Clinical Classes Predict Karta Hai:</b><br/>"
                           "• <b>Normal (Class 0):</b> Bache ki heartbeat aur oxygen level bilkul mehfooz hai; routine antenatal checkup continue karein.<br/>"
                           "• <b>Suspect (Class 2):</b> FHR variability kam ya abnormal patterns shuru ho rahe hain; continuous monitoring aur doctor ka re-assessment lazmi hai.<br/>"
                           "• <b>Pathological (Class 1):</b> Severe Fetal Distress! Bache ko oxygen nahi mil rahi; foran emergency C-Section ya immediate obstetric intervention required!",
            "clinical_value": "Pakistan ke 80% dehaati aur taluka hospitals mein specialized fetal medicine expert mojood nahi hota jo complex CTG graph ko parh sake. FetalWatch real-time par alert bajata hai jis se <b>intra-partum stillbirth (murda paidaish)</b> aur neonatal brain damage (hypoxic-ischemic encephalopathy) se bacha ja sakta hai.",
            "pipeline": "<b>Algorithm:</b> Random Forest / LightGBM / XGBoost with Optuna HPO.<br/>"
                        "<b>Dataset:</b> UCI Cardiotocography (2,126 records).<br/>"
                        "<b>Preprocessing:</b> RobustScaler + Zero-division guardrails.<br/>"
                        "<b>Performance:</b> Macro-F1: ~0.912 | AUROC: 0.986 | Parity Verified.",
        },
        {
            "header": "2. MaternalGuard — Maternal Health Risk Triage Classifier (Live Served)",
            "kaam": "Pregnant aurat ke basic non-invasive vitals se maternal health risk ko classify karta hai taake <b>Severe Pre-eclampsia, Eclampsia</b>, Gestational Hypertension, aur Sepsis ko bar-waqt pakra ja sake.",
            "inputs": "<b>6 Non-Invasive Vitals:</b><br/>"
                      "• <b>Age:</b> Mother ki umar (saal) — teenager (<18) ya advanced maternal age (>35) high risk.<br/>"
                      "• <b>Systolic BP (mmHg):</b> Normal <120, Danger >=140 (Hypertension), Emergency >=160 (Severe Pre-eclampsia).<br/>"
                      "• <b>Diastolic BP (mmHg):</b> Normal <80, Danger >=90, Emergency >=110.<br/>"
                      "• <b>Blood Sugar (BS):</b> Blood glucose (mmol/L) — Fasting >5.6 mmol/L Gestational Diabetes risk.<br/>"
                      "• <b>Body Temp:</b> Body temperature (°F/°C) — >=38°C (100.4°F) Maternal Sepsis ya chorioamnionitis.<br/>"
                      "• <b>Heart Rate:</b> Dil ki dharkan (bpm) — >100 bpm Maternal Tachycardia ya hemorrhage risk.",
            "predictions": "<b>3 Risk Tiers Predict Karta Hai:</b><br/>"
                           "• <b>Low Risk:</b> Vitals safe limits mein hain; normal ANC timeline follow karein.<br/>"
                           "• <b>Mid Risk:</b> Borderline BP ya high blood glucose; dietary monitoring aur frequent checkup zaroori.<br/>"
                           "• <b>High Risk:</b> Critical BP, high sugar ya fever; foran secondary/tertiary hospital referral.<br/>"
                           "• <i>WHO Safety Override:</i> Agar BP >=160/110 ya bleeding/convulsions hon, to system model score ko override karke foran <b>HIGH_RISK_EMERGENCY</b> declare karta hai.",
            "clinical_value": "Gaon ki Lady Health Workers (LHWs) aur BHU dispensers ke paas advanced laboratory nahi hoti. Sirf digital BP apparatus, thermometer aur glucometer ki reading se yeh model unhein bata deta hai ke kaunsi aurat ko emergency hospital shift karna zaroori hai.",
            "pipeline": "<b>Algorithm:</b> Scaled Random Forest + LightGBM pipeline.<br/>"
                        "<b>Dataset:</b> UCI Maternal Health Risk (1,014 records).<br/>"
                        "<b>Validation:</b> GroupShuffleSplit (patient leakage-free).<br/>"
                        "<b>Performance:</b> Macro-F1: ~0.688 | AUROC: 0.89 | Strict calibration.",
        },
        {
            "header": "3. PretermGuard — Preterm Birth (Premature Labor) Risk Classifier",
            "kaam": "Qabal az waqt paidaish (Preterm Labor, <37 gestational weeks) ke risk ko detect karta hai taake waqt se pehle honay wali delivery ko manage kiya ja sake.",
            "inputs": "<b>Uterine Contraction & CTG Telemetry:</b><br/>"
                      "• <b>Uterine Contractions (UC):</b> Contractions ki frequency, duration aur intensity.<br/>"
                      "• <b>Baseline FHR & Decelerations:</b> Dharkan ka pattern jab uterus contract hota hai.<br/>"
                      "• <b>Fetal Heart Rate Variability (ASTV/ALTV):</b> Premature delivery stress indicators.",
            "predictions": "<b>Preterm Risk Categories Predict Karta Hai:</b><br/>"
                           "• <b>Low Risk:</b> Contractions harmless physiological Braxton Hicks hain, preterm delivery ka khatra nahi.<br/>"
                           "• <b>Suspect / Moderate:</b> Irregular uterine contractions; bed rest, hydration aur LHW surveillance ki zaroorat hai.<br/>"
                           "• <b>Pathological / High Risk:</b> Active Preterm Labor! Uterine contractions bache ko waqt se pehle deliver karne ke marhalay mein hain.",
            "clinical_value": "Pakistan mein premature birth newborn babies ki maut ki sab se bari wajah hai. PretermGuard waqt rehte alert karta hai taake doctor maa ko <b>Antenatal Corticosteroids</b> (Dexamethasone) de sakein jis se bache ke phepde (lungs) mature ho jayein, aur bache ko Neonatal ICU (NICU) pohanchaya ja sake.",
            "pipeline": "<b>Algorithm:</b> LightGBM Classifier with Optuna HPO.<br/>"
                        "<b>Dataset:</b> UCI CTG Class Labels.<br/>"
                        "<b>Balancing:</b> SMOTE oversampling.<br/>"
                        "<b>Performance:</b> Macro-F1: ~0.89.",
        },
        {
            "header": "4. CareReach — Antenatal Care (ANC) Missed Visit & No-Show Predictor",
            "kaam": "Predict karta hai ke kaunsi pregnant aurat apni agli scheduled Antenatal Care (ANC) appointment miss karegi (no-show) taake high-risk cases drop out na hon.",
            "inputs": "<b>20 Demographic & Operational Features:</b><br/>"
                      "• <b>Age & Scholarship:</b> Mareez ki umar aur welfare / financial aid status.<br/>"
                      "• <b>Comorbidities:</b> Hypertension, Diabetes, Alcoholism, Handicap status, comorbidity count.<br/>"
                      "• <b>SMS_received:</b> Kya mareez ko appointment reminder SMS receive hua tha.<br/>"
                      "• <b>booking_delta_days:</b> Appointment book karwane aur actual tareekh ke darmiyan kitne din thay.<br/>"
                      "• <b>appointment_dow:</b> Hafte ka din (Monday, Tuesday, etc.).",
            "predictions": "<b>No-Show Probability & Actionable Insights:</b><br/>"
                           "• <b>Missed Visit Risk:</b> 0% se 100% risk probability score.<br/>"
                           "• <b>Binary Prediction:</b> Will Attend (Show) vs Likely to Miss (No-Show).<br/>"
                           "• <b>SHAP Attribution:</b> Model batata hai ke miss karne ki wajah kya hai (e.g. 25 din ka booking gap aur reminder na milna).",
            "clinical_value": "Dehaat mein 60% se zyada aurtein pehli visit ke baad hospital jana chor deti hain jis se unka high-risk un-monitored reh jata hai. CareReach hospital aur LHW ko pehle se list de deta hai taake wo un aurton ke ghar ja kar ya call karke unhein clinic le aayein.",
            "pipeline": "<b>Algorithm:</b> LightGBM + SMOTE-Tomek.<br/>"
                        "<b>Dataset:</b> Medical Appointment No-Shows (110,527 records).<br/>"
                        "<b>Explainability:</b> TreeSHAP feature importance.<br/>"
                        "<b>Performance:</b> AUROC: ~0.73.",
        },
        {
            "header": "5. GestationInsight — Gestational Complications & Metabolic Risk Classifier",
            "kaam": "Pregnancy ke doran <b>Gestational Diabetes Mellitus (GDM)</b> aur metabolic syndrome ke khatrat ko early trimesters mein identify karta hai.",
            "inputs": "<b>17 Clinical & Derived Metabolic Features:</b><br/>"
                      "• <b>Glucose:</b> Fasting blood glucose concentration.<br/>"
                      "• <b>MAP (Mean Arterial Pressure):</b> Calculate kiya gaya blood pressure: (2*DBP + SBP)/3.<br/>"
                      "• <b>BMI:</b> Body Mass Index (weight in kg / height in m²).<br/>"
                      "• <b>DiabetesPedigreeFunction:</b> Khandani diabetes ki tareekh ka genetic score.<br/>"
                      "• <b>Insulin & SkinThickness:</b> Insulin secretion level aur triceps skin thickness.<br/>"
                      "• <b>Derived Features:</b> glucose_tolerance_idx, insulin_glucose_ratio, estimated SBP.",
            "predictions": "<b>3-Class Metabolic Risk Level:</b><br/>"
                           "• <b>Low:</b> Normal insulin metabolism; routine antenatal follow-up.<br/>"
                           "• <b>Moderate:</b> Impaired glucose tolerance; Oral Glucose Tolerance Test (OGTT) aur dietary guidance recommended.<br/>"
                           "• <b>High:</b> Active Gestational Diabetes aur metabolic dysfunction! Insulin protocol aur regular fetal growth ultrasound scans lazmi.<br/>",
            "clinical_value": "Agar ma ki gestational diabetes unmanaged rahe to bacha over-sized (Macrosomia) ho jata hai, delivery ke waqt bache ka shoulder phans sakta hai (shoulder dystocia), aur ma ko baad mein permanent Type-2 diabetes ho sakti hai. GestationInsight early detection se in tamam khatrat se bachata hai.",
            "pipeline": "<b>Algorithm:</b> XGBoost Classifier with Optuna HPO.<br/>"
                        "<b>Dataset:</b> Gestation Dataset (768 records).<br/>"
                        "<b>Balancing:</b> SMOTE-Tomek.<br/>"
                        "<b>Performance:</b> Macro-F1: ~0.78.",
        },
    ]

    card_label_style = ParagraphStyle(
        "CardLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=primary,
    )
    
    card_val_style = ParagraphStyle(
        "CardVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=dark_gray,
    )

    card_head_style = ParagraphStyle(
        "CardHead",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12.5,
        textColor=colors.white,
    )

    for card in model_cards_data:
        table_rows = [
            [Paragraph(f"<b>{card['header']}</b>", card_head_style), ""],
            [Paragraph("<b>Kaam (Function):</b>", card_label_style), Paragraph(card["kaam"], card_val_style)],
            [Paragraph("<b>Input Features:</b>", card_label_style), Paragraph(card["inputs"], card_val_style)],
            [Paragraph("<b>Predictions & Actions:</b>", card_label_style), Paragraph(card["predictions"], card_val_style)],
            [Paragraph("<b>Clinical Role (BHU):</b>", card_label_style), Paragraph(card["clinical_value"], card_val_style)],
            [Paragraph("<b>Technical Pipeline:</b>", card_label_style), Paragraph(card["pipeline"], card_val_style)],
        ]
        
        t_card = Table(table_rows, colWidths=[110, 402])
        t_card.setStyle(TableStyle([
            ('SPAN', (0, 0), (1, 0)),
            ('BACKGROUND', (0, 0), (1, 0), primary),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
            ('GRID', (0, 0), (-1, -1), 0.5, border_card),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        story.append(KeepTogether([t_card]))
        story.append(Spacer(1, 7))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Generated comprehensive PDF guide with Section 6: {PDF_PATH}")


if __name__ == "__main__":
    build_pdf()
