from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
import os

def create_presentation():
    prs = Presentation()
    
    teal = RGBColor(15, 118, 110)
    dark_gray = RGBColor(55, 65, 81)
    
    def style_title(title_shape):
        if title_shape.text_frame:
            for paragraph in title_shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    run.font.color.rgb = teal
                    run.font.bold = True
                    run.font.name = 'Calibri'
                    
    def style_body(body_shape):
        if body_shape.text_frame:
            for paragraph in body_shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    run.font.color.rgb = dark_gray
                    run.font.name = 'Calibri'

    # Slide layouts
    TITLE_SLIDE = 0
    BULLET_SLIDE = 1
    BLANK_SLIDE = 6
    TITLE_ONLY = 5

    # --- Slide 1: Title Slide ---
    slide = prs.slides.add_slide(prs.slide_layouts[TITLE_SLIDE])
    title = slide.shapes.title
    subtitle = slide.placeholders[1]

    title.text = "MaaHifazat AI"
    subtitle.text = "AI-Powered Maternal Health & Multi-Agent Orchestration\n\nGroup Name: Algo Titans\n1. Zafar Ullah (Leader)\n2. Muhammad Ali\n3. Muhammad Younus Khan"
    style_title(title)

    # --- Slide 2: The Problem We Are Solving ---
    slide = prs.slides.add_slide(prs.slide_layouts[BULLET_SLIDE])
    title_shape = slide.shapes.title
    body_shape = slide.placeholders[1]
    
    title_shape.text = "The Problem: Why MaaHifazat?"
    
    tf = body_shape.text_frame
    tf.text = "In rural areas, mothers and babies face critical risks due to 'The Three Delays':"
    p = tf.add_paragraph()
    p.text = "1. Delay in Decision: Unrecognized symptoms leading to late action."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "2. Delay in Reaching Help: Unknown hospital capabilities and distances."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "3. Delay in Care: Overcrowded facilities and slow triage."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Our Goal: Eliminate these delays using advanced Machine Learning and AI Agents."
    
    style_title(title_shape)
    style_body(body_shape)

    # --- Slide 3: System Architecture (Programming Perspective) ---
    slide = prs.slides.add_slide(prs.slide_layouts[BULLET_SLIDE])
    title_shape = slide.shapes.title
    body_shape = slide.placeholders[1]
    
    title_shape.text = "System Architecture & Tech Stack"
    
    tf = body_shape.text_frame
    tf.text = "A full-stack, scalable application built for clinical environments:"
    p = tf.add_paragraph()
    p.text = "Backend: FastAPI (Python) for asynchronous, high-performance REST APIs."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Frontend: React 19 + TypeScript + Vite + Tailwind CSS for a highly responsive UI."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Database: SQLite with SQLAlchemy (asyncio) for persistent clinical records."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "AI Infrastructure: 5 custom ML models (XGBoost, Random Forest) loaded into a Model Registry."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Orchestration: LangGraph StateGraph connecting 9 AI sub-agents."
    p.level = 1
    
    style_title(title_shape)
    style_body(body_shape)

    # --- Slide 4: Frontend Dashboard (User Perspective) ---
    slide = prs.slides.add_slide(prs.slide_layouts[TITLE_ONLY])
    title_shape = slide.shapes.title
    title_shape.text = "The MaaHifazat Dashboard"
    style_title(title_shape)
    
    if os.path.exists("01_main_page.png"):
        slide.shapes.add_picture("01_main_page.png", Inches(1), Inches(1.5), width=Inches(8))
    
    txBox = slide.shapes.add_textbox(Inches(1), Inches(6.5), Inches(8), Inches(1))
    tf = txBox.text_frame
    tf.text = "A clean, clinical UI designed for Lady Health Workers (LHWs) and Doctors to manage patient records and alerts easily."
    for p in tf.paragraphs:
        for r in p.runs:
            r.font.size = Pt(18)
            r.font.color.rgb = dark_gray

    # --- Slide 5: The 5 Specialized ML Models ---
    slide = prs.slides.add_slide(prs.slide_layouts[TITLE_ONLY])
    title_shape = slide.shapes.title
    title_shape.text = "5 Specialized ML Models in Action"
    style_title(title_shape)
    
    if os.path.exists("03_form_filled.png"):
        slide.shapes.add_picture("03_form_filled.png", Inches(0.5), Inches(1.5), width=Inches(4.2))
        
    if os.path.exists("04_results_top.png"):
        slide.shapes.add_picture("04_results_top.png", Inches(5), Inches(1.5), width=Inches(4.5))
        
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(6.3), Inches(9), Inches(1))
    tf = txBox.text_frame
    tf.text = "1. MaternalGuard (Maternal Risk)   |   2. FetalWatch (Fetal Distress)\n3. PretermGuard (Preterm Risk)   |   4. GestationInsight   |   5. CareReach (ANC Dropout)\nPatient vitals and CTG features are processed simultaneously to provide a unified diagnostic view."
    for p in tf.paragraphs:
        for r in p.runs:
            r.font.size = Pt(16)
            r.font.bold = True
            r.font.color.rgb = dark_gray

    # --- Slide 6: 9-Agent LangGraph Orchestration ---
    slide = prs.slides.add_slide(prs.slide_layouts[TITLE_ONLY])
    title_shape = slide.shapes.title
    title_shape.text = "9-Agent LangGraph Orchestration"
    style_title(title_shape)
    
    if os.path.exists("02_agent_page.png"):
        slide.shapes.add_picture("02_agent_page.png", Inches(1), Inches(1.5), width=Inches(8))
        
    txBox = slide.shapes.add_textbox(Inches(1), Inches(6.5), Inches(8), Inches(1))
    tf = txBox.text_frame
    tf.text = "When an emergency is detected, a state graph of 9 autonomous AI agents kicks in. They handle Data Quality, WHO Triage, Smart Referrals, and automated SMS Communications."
    for p in tf.paragraphs:
        for r in p.runs:
            r.font.size = Pt(18)
            r.font.color.rgb = dark_gray

    # --- Slide 7: Clinical Reporting & Workflow Results ---
    slide = prs.slides.add_slide(prs.slide_layouts[TITLE_ONLY])
    title_shape = slide.shapes.title
    title_shape.text = "Live Workflow & Clinical Reporting"
    style_title(title_shape)
    
    if os.path.exists("07_results_clinician.png"):
        slide.shapes.add_picture("07_results_clinician.png", Inches(0.5), Inches(1.5), width=Inches(4.2))
        
    if os.path.exists("08_results_bottom.png"):
        slide.shapes.add_picture("08_results_bottom.png", Inches(5), Inches(1.5), width=Inches(4.5))
        
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(6.3), Inches(9), Inches(1))
    tf = txBox.text_frame
    tf.text = "The 'Reporting Agent' generates a complete clinical summary for the doctor. The 'Smart Referral Agent' calculates optimal facility routes, and the 'Communication Agent' dispatches SMS alerts."
    for p in tf.paragraphs:
        for r in p.runs:
            r.font.size = Pt(16)
            r.font.color.rgb = dark_gray

    # --- Slide 8: WHO Safety Guardrails ---
    slide = prs.slides.add_slide(prs.slide_layouts[BULLET_SLIDE])
    title_shape = slide.shapes.title
    body_shape = slide.placeholders[1]
    
    title_shape.text = "Strict WHO Safety Guardrails"
    
    tf = body_shape.text_frame
    tf.text = "AI must be reliable. We implemented deterministic safety rules:"
    p = tf.add_paragraph()
    p.text = "Rule-Based Overrides: If vitals show severe hypertension (BP > 160/110) or eclampsia symptoms, the system IGNORES the ML prediction."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "High-Risk Emergency: It instantly triggers an emergency triage level, forcing the orchestration agents to route the patient to an ICU."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "This hybrid approach (ML + Deterministic Rules) guarantees 100% safety."
    p.level = 1
    
    style_title(title_shape)
    style_body(body_shape)

    # --- Slide 9: Conclusion ---
    slide = prs.slides.add_slide(prs.slide_layouts[BULLET_SLIDE])
    title_shape = slide.shapes.title
    body_shape = slide.placeholders[1]
    
    title_shape.text = "Conclusion & Impact"
    
    tf = body_shape.text_frame
    tf.text = "MaaHifazat AI is not just a prediction tool; it is a full clinical workflow:"
    p = tf.add_paragraph()
    p.text = "It identifies the problem early using 5 distinct ML models."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "It coordinates the solution using a 9-Agent architecture."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "It connects the patient to the right facility instantly."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "By eliminating the 'Three Delays', Algo Titans aims to drastically reduce maternal mortality."
    p.level = 1
    
    style_title(title_shape)
    style_body(body_shape)

    prs.save('Algo_Titans_Professional_Presentation.pptx')
    print("Professional PPT with images saved.")

if __name__ == '__main__':
    create_presentation()
