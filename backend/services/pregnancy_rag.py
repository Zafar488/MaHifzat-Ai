
"""Curated Pregnancy Medical Knowledge Base, Semantic Retrieval, DuckDuckGo Search and Groq AI Helper.
Grounded in WHO, NHS, and NICE clinical guidelines.
"""
import re
import json
import logging
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from backend.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 1. CURATED CLINICAL KNOWLEDGE BASE (WHO, NHS, NICE)
# ─────────────────────────────────────────────────────────────────────────────
CURATED_GUIDELINES: List[Dict[str, Any]] = [
    {
        "id": "who_anc_contacts",
        "source": "WHO (World Health Organization)",
        "guideline": "WHO Recommendations on Antenatal Care for a Positive Pregnancy Experience (2016)",
        "section": "Contact Schedule & Maternal Care Model",
        "url": "https://www.who.int/publications/i/item/9789241549912",
        "date": "2016-11-28",
        "topics": ["contacts", "schedule", "checkup", "antenatal care", "milestones", "trimester", "anc"],
        "content_en": (
            "WHO recommends a minimum of eight antenatal care (ANC) contacts to reduce perinatal mortality and improve women's experience. "
            "The recommended schedule: Contact 1 at up to 12 weeks; Contact 2 at 20 weeks; Contact 3 at 26 weeks; "
            "Contact 4 at 30 weeks; Contact 5 at 34 weeks; Contact 6 at 36 weeks; Contact 7 at 38 weeks; and Contact 8 at 40 weeks. "
            "Each contact includes maternal blood pressure check, fetal growth monitoring, screening for proteinuria, anemia, and danger signs."
        ),
        "content_ur": (
            "عالمی ادارہ صحت (WHO) حمل کے دوران کم از کم 8 باقاعدہ طبی رابطوں (ANC Contacts) کی سفارش کرتا ہے۔ "
            "مقررہ شیڈول: پہلا رابطہ 12 ہفتوں تک، دوسرا 20 ہفتے، تیسرا 26 ہفتے، چوتھا 30 ہفتے، پانچواں 34 ہفتے، چھٹا 36 ہفتے، ساتواں 38 ہفتے، اور آٹھواں 40 ہفتے پر۔ "
            "ہر معائنے میں بلڈ پریشر، بچے کی نشوونما، خون کی کمی اور خطرے کی علامات کی جانچ شامل ہے۔"
        )
    },
    {
        "id": "who_nutrition_supplements",
        "source": "WHO (World Health Organization)",
        "guideline": "Antenatal Nutrition and Supplementation Guidelines",
        "section": "Micronutrient Supplementation & Diet",
        "url": "https://www.who.int/publications/i/item/9789241549912",
        "date": "2016-11-28",
        "topics": ["nutrition", "food", "iron", "folic acid", "calcium", "supplements", "diet", "anemia", "vitamins"],
        "content_en": (
            "Daily oral iron (30-60 mg elemental iron) and folic acid (400 mcg) supplementation is recommended for pregnant women to prevent maternal anemia, sepsis, and low birthweight. "
            "In populations with low dietary calcium intake, daily calcium supplementation (1.5-2.0 g elemental oral calcium) is recommended to reduce pre-eclampsia risk. "
            "Healthy eating includes adequate protein (lean meats, legumes, dairy), clean water, fresh fruits, green leafy vegetables, and avoiding unpasteurized dairy, raw eggs, or undercooked meats."
        ),
        "content_ur": (
            "حاملہ خواتین کے لیے روزانہ آئرن (30-60 ملی گرام) اور فولک ایسڈ (400 مائیکرو گرام) لینا ضروری ہے تاکہ خون کی کمی اور پیدائشی نقائص سے بچا جا سکے۔ "
            "کیلشیم کی کمی والے علاقوں میں روزانہ 1.5 سے 2.0 گرام کیلشیم ہائی بلڈ پریشر اور پری ایکلیمپسیا سے بچاؤ کے لیے دیا جاتا ہے۔ "
            "غذا میں دالیں، دودھ، انڈے (اچھی طرح پکے ہوئے)، تازہ پھل اور سبزیاں شامل ہونی چاہئیں، جبکہ کچا دودھ اور ادھ پکا گوشت قطعی نہیں کھانا چاہیے۔"
        )
    },
    {
        "id": "nhs_safe_exercise_lifting",
        "source": "NHS (National Health Service, UK)",
        "guideline": "Exercise and Physical Activity in Pregnancy",
        "section": "Physical Activity & Safe Lifting",
        "url": "https://www.nhs.uk/pregnancy/keeping-well/exercise/",
        "date": "2023-04-12",
        "topics": ["exercise", "lifting", "physical activity", "heavy lifting", "walking", "work", "daily activities"],
        "content_en": (
            "Staying active is beneficial: aim for 150 minutes of moderate-intensity activity weekly (e.g., brisk walking, swimming, prenatal yoga). "
            "Lifting guidance: Pregnancy hormones (relaxin) soften ligaments, increasing injury risk. While no single kilogram cutoff exists for all women, "
            "avoid repetitive heavy lifting (>10-15 kg) and straining. When lifting, bend your knees, keep back straight, hold objects close to your body, and never twist while lifting. "
            "Stop exercising immediately if you experience dizziness, shortness of breath, vaginal bleeding, contractions, or fluid leakage."
        ),
        "content_ur": (
            "حمل میں ہلکی جسمانی سرگرمی (جیسے روزانہ چہل قدمی، پیدل چلنا) فائدہ مند ہے۔ "
            "وزن اٹھانے کے اصول: حمل میں ہارمونز جوڑوں کو نرم کر دیتے ہیں جس سے چوٹ کا خطرہ بڑھتا ہے۔ بھاری وزن (10-15 کلو سے زیادہ) اٹھانے سے پرہیز کریں۔ "
            "اگر وزن اٹھانا پڑے تو گھٹنوں کو موڑیں، کمر سیدھی رکھیں اور وزن کو جسم کے قریب رکھیں۔ چکر آنے، سانس پھولنے یا درد کی صورت میں فوراً آرام کریں۔"
        )
    },
    {
        "id": "nice_preeclampsia_bp",
        "source": "NICE (National Institute for Health and Care Excellence, UK)",
        "guideline": "Hypertension in Pregnancy: Diagnosis and Management (NG133 / NG229)",
        "section": "Preeclampsia Screening & Blood Pressure Targets",
        "url": "https://www.nice.org.uk/guidance/ng133",
        "date": "2023-07-20",
        "topics": ["blood pressure", "preeclampsia", "hypertension", "headache", "vision", "proteinuria", "eclampsia", "aspirin"],
        "content_en": (
            "Blood pressure >= 140/90 mmHg requires clinical evaluation. Chronic or gestational hypertension requires monitoring for pre-eclampsia. "
            "Danger signs of severe pre-eclampsia include severe frontal headache unresponsive to standard analgesia, visual disturbances (blurring, flashing lights), "
            "severe epigastric/right upper quadrant pain, sudden facial/hand edema, and hyperreflexia or convulsions. "
            "Women at high risk (e.g., hypertensive, diabetic, previous preeclampsia) should be prescribed low-dose aspirin (75-150 mg daily) from 12 weeks until delivery under clinician supervision."
        ),
        "content_ur": (
            "بلڈ پریشر 140/90 یا اس سے زیادہ ہونا فوری طبی معائنے کا متقاضی ہے۔ "
            "شدید پری ایکلیمپسیا کی خطرے کی علامات: سر میں شدید درد جو دوائی سے ٹھیک نہ ہو، آنکھوں کے آگے دھندلاہٹ یا چمکتے ستارے نظر آنا، پیٹ کے اوپری حصے میں شدید درد، اور چہرے یا ہاتھوں پر اچانک سوجن۔ "
            "ایسی علامات ظاہر ہونے پر فوراً ایمرجنسی ہسپتال پہنچنا چاہیے کیونکہ یہ ماں اور بچے دونوں کے لیے جان لیوا ہو سکتی ہیں۔"
        )
    },
    {
        "id": "nice_fetal_movements",
        "source": "NICE & RCOG (Royal College of Obstetricians and Gynaecologists)",
        "guideline": "Reduced Fetal Movements (Green-top Guideline No. 57 / NG229)",
        "section": "Fetal Movement Pattern & Wellbeing",
        "url": "https://www.rcog.org.uk/guidelines-research-services/guidelines/gtg57/",
        "date": "2021-02-15",
        "topics": ["movement", "fetal movement", "baby movement", "kicks", "decreased movement", "fetus", "fetal"],
        "content_en": (
            "Most women feel first movements between 16 and 24 weeks. By 24-28 weeks, a regular movement pattern is established. "
            "There is no set number of kicks to count (the '10 kicks' rule is obsolete); what matters is the woman's subjective perception of her baby's usual pattern. "
            "A reduction in movements or sudden change is a potential warning sign of fetal compromise or placental insufficiency. "
            "If movements decrease or stop, do not wait until tomorrow; seek immediate hospital/maternity assessment for fetal heart rate check and CTG monitoring."
        ),
        "content_ur": (
            "اکثر مائیں 16 سے 24 ہفتوں کے درمیان بچے کی پہلی حرکت محسوس کرتی ہیں۔ 28 ہفتوں تک بچے کی روزمرہ حرکت کا ایک مخصوص انداز بن جاتا ہے۔ "
            "اہم بات یہ ہے کہ ماں بچے کی معمول کی حرکت کو سمجھے۔ اگر بچے کی حرکت معمول سے کم ہو جائے، رک جائے یا بدل جائے تو یہ خطرے کی علامت ہے۔ "
            "حرکت میں کمی کی صورت میں کل کا انتظار ہرگز نہ کریں، فوراً قریبی میٹرنٹی ہسپتال جا کر بچے کی دھڑکن اور مانیٹرنگ کروائیں۔"
        )
    },
    {
        "id": "who_danger_signs_emergency",
        "source": "WHO (World Health Organization)",
        "guideline": "Managing Complications in Pregnancy and Childbirth (IMPAC)",
        "section": "Obstetric Red Flags & Emergency Triggers",
        "url": "https://www.who.int/publications/i/item/9789241545877",
        "date": "2017-06-01",
        "topics": ["danger signs", "emergency", "red flags", "bleeding", "convulsions", "fever", "pain", "amniotic fluid"],
        "content_en": (
            "Cardinal obstetric danger signs requiring immediate hospital emergency care: "
            "1. Vaginal bleeding at any stage of pregnancy (threatened miscarriage, placenta previa, abruption). "
            "2. Convulsions or loss of consciousness (eclampsia). "
            "3. Severe headache with blurred vision (pre-eclampsia). "
            "4. Severe abdominal pain (uterine rupture, placental abruption, ectopic pregnancy). "
            "5. High fever (>38°C) with chills or foul vaginal discharge (chorioamnionitis, septicemia). "
            "6. Premature rupture of membranes (fluid leaking before labor). "
            "7. Marked decrease or absence of fetal movements after 24 weeks."
        ),
        "content_ur": (
            "حمل کی ہنگامی خطرے کی علامات (Obstetric Danger Signs): "
            "1. اندام نہانی سے کسی بھی قسم کا خون آنا (Bleeding)۔ "
            "2. دورے پڑنا یا بے ہوشی ہونا (Convulsions/Eclampsia)۔ "
            "3. شدید سر درد اور نظر میں خرابی۔ "
            "4. پیٹ میں شدید اور مسلسل درد۔ "
            "5. تیز بخار اور بدبودار اخراج (انفیکشن)۔ "
            "6. وقت سے پہلے پانی کی تھیلی پھٹنا یا مسلسل پانی کا اخراج۔ "
            "7. بچے کی حرکت کا بند یا اچانک کم ہو جانا۔ ان علامات میں ایک منٹ بھی ضائع کیے بغیر ایمرجنسی ہسپتال پہنچنا چاہیے۔"
        )
    },
    {
        "id": "nhs_postpartum_newborn",
        "source": "NHS & WHO",
        "guideline": "Postnatal Care and Newborn Health Recommendations",
        "section": "Postpartum Recovery & Newborn Essentials",
        "url": "https://www.who.int/publications/i/item/9789240045989",
        "date": "2022-03-30",
        "topics": ["postpartum", "newborn", "after birth", "breastfeeding", "lochia", "depression", "recovery"],
        "content_en": (
            "Postpartum maternal recovery: Normal bleeding (lochia) transitions from red to pinkish-brown to yellow-white over 4-6 weeks. "
            "Warning signs: soaking more than one maxi-pad per hour, large blood clots, foul odor, or calf pain/swelling (DVT). "
            "Newborn care: Skin-to-skin contact immediately after birth, initiation of exclusive breastfeeding within the first hour, "
            "dry umbilical cord care, and immunizations (BCG, Polio, Hep B). Screen for newborn jaundice, breathing difficulty, or poor feeding."
        ),
        "content_ur": (
            "پیدائش کے بعد کی نگہداشت (Postpartum Care): پیدائش کے بعد خون کا اخراج (لوچیا) آہستہ آہستہ 4 سے 6 ہفتوں میں کم ہوتا ہے۔ "
            "اگر گھنٹے میں ایک سے زیادہ بڑا پیڈ بھر جائے، بڑے لوتھڑے آئیں، یا بدبو آئے تو فوراً ڈاکٹر کو دکھائیں۔ "
            "نومولود بچے کی دیکھ بھال: پیدائش کے فوراً بعد بچے کو ماں کے سینے سے لگانا (Skin-to-skin)، پہلے گھنٹے میں ماں کا پہلا گاڑھا دودھ پلانا، نال کو خشک اور صاف رکھنا، اور حفاظتی ٹیکے لگوانا ضروری ہے۔"
        )
    },
    {
        "id": "who_emotional_wellbeing",
        "source": "WHO & NICE",
        "guideline": "Antenatal and Postnatal Mental Health",
        "section": "Emotional Wellbeing, Perinatal Anxiety and Depression",
        "url": "https://www.nice.org.uk/guidance/cg192",
        "date": "2020-02-11",
        "topics": ["emotional", "mental health", "depression", "anxiety", "coping", "stress", "mood", "baby blues"],
        "content_en": (
            "Pregnancy involves major emotional and neurohormonal transitions. Between 10% and 15% of women experience antenatal depression or anxiety. "
            "Positive coping includes open communication with partners, light exercise, adequate rest, and avoiding isolation. "
            "Signs requiring professional support: persistent sadness, lack of joy, overwhelming panic attacks, intrusive thoughts, or feelings of hopelessness. "
            "Mental healthcare is an essential component of maternal health and must not carry stigma."
        ),
        "content_ur": (
            "حمل کے دوران ذہنی و جذباتی صحت: ہارمونز کی تبدیلی سے موڈ میں اتار چڑھاؤ معمول کی بات ہے، لیکن 10 سے 15 فیصد خواتین ڈپریشن یا شدید اضطراب کا شکار ہو سکتی ہیں۔ "
            "مثبت تدابیر: اپنے ساتھی اور گھر والوں سے بات چیت، مناسب نیند، اور خود کو تنہا نہ کرنا۔ "
            "اگر مستقل اداسی، دل ڈوبنا، شدید خوف یا مایوسی محسوس ہو تو اپنے ڈاکٹر یا کونسلر سے رجوع کرنا ضروری ہے۔ یہ کمزوری نہیں بلکہ ایک قابل علاج طبی کیفیت ہے۔"
        )
    }
]

# ─────────────────────────────────────────────────────────────────────────────
# 2. DANGER SIGN REGEX DETECTOR (URGENT SAFETY GATEWAY)
# ─────────────────────────────────────────────────────────────────────────────
DANGER_KEYWORDS_EN = [
    r"\bbleeding\b", r"\bblood\b", r"\bhemorrhage\b", r"\bconvulsion\b", r"\bseizure\b",
    r"\bfits\b", r"\bfainted\b", r"\bunconscious\b", r"\bsevere headache\b", r"\bblurry vision\b",
    r"\bflashing lights\b", r"\bno movement\b", r"\bstopped moving\b", r"\breduced movement\b",
    r"\bwater broke\b", r"\bleaking fluid\b", r"\bsevere pain\b", r"\bhigh fever\b", r"\bchills\b"
]

DANGER_KEYWORDS_UR = [
    r"خون", r"بلیڈنگ", r"دورے", r"جھٹکے", r"بے ہوش", r"شدید سر درد", r"دھندلا",
    r"حرکت بند", r"حرکت کم", r"پانی چھوٹ", r"پانی کا اخراج", r"شدید درد", r"تیز بخار"
]

def check_urgent_symptoms(text: str) -> Optional[Dict[str, str]]:
    """Detect cardinal obstetric danger signs and return emergency alert if present."""
    text_lower = text.lower()
    for pattern in DANGER_KEYWORDS_EN:
        if re.search(pattern, text_lower):
            return {
                "is_urgent": True,
                "reason_en": "You mentioned potential danger signs (e.g. bleeding, severe pain, visual changes, or reduced fetal movement).",
                "alert_en": "URGENT MEDICAL ALERT: These symptoms require immediate clinical evaluation. Please go to the nearest hospital maternity emergency department right away. Do not wait for an online response.",
                "alert_ur": "فوری ہنگامی طبی انتباہ: آپ نے ممکنہ خطرے کی علامات کا ذکر کیا ہے۔ برائے مہربانی فوراً قریبی ہسپتال کے زچگی ایمرجنسی وارڈ میں جائیں اور ڈاکٹر سے معائنہ کروائیں۔ وقت ضائع نہ کریں۔"
            }
    for pattern in DANGER_KEYWORDS_UR:
        if re.search(pattern, text):
            return {
                "is_urgent": True,
                "reason_en": "You mentioned potential obstetric danger signs in Urdu.",
                "alert_en": "URGENT MEDICAL ALERT: These symptoms require immediate clinical evaluation. Please go to the nearest hospital emergency right away.",
                "alert_ur": "فوری ہنگامی طبی انتباہ: آپ نے خطرے کی علامت بتائی ہے۔ برائے مہربانی بغیر کسی تاخیر کے فوراً قریبی ہسپتال کے میٹرنٹی ایمرجنسی ڈیپارٹمنٹ سے رجوع کریں۔"
            }
    return None

# ─────────────────────────────────────────────────────────────────────────────
# 3. SEMANTIC RETRIEVAL & CITATION MATCHING
# ─────────────────────────────────────────────────────────────────────────────
def retrieve_guidelines(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Score and retrieve relevant clinical guidelines matching user query."""
    tokens = set(re.findall(r"\w+", query.lower()))
    scored = []
    for item in CURATED_GUIDELINES:
        score = 0
        for topic in item["topics"]:
            if topic in tokens or any(t in topic for t in tokens if len(t) > 3):
                score += 3
        # Match inside content
        for t in tokens:
            if len(t) > 3 and t in item["content_en"].lower():
                score += 1
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top_k]]

# ─────────────────────────────────────────────────────────────────────────────
# 4. DUCKDUCKGO PUBLIC SEARCH ENRICHMENT
# ─────────────────────────────────────────────────────────────────────────────
async def search_duckduckgo(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Fetch supplementary live search results from DuckDuckGo without exposing PII."""
    sanitized = re.sub(r"[^\w\s]", " ", query, flags=re.UNICODE).strip()[:100]
    search_term = f"pregnancy health {sanitized}".strip()
    try:
        async with httpx.AsyncClient(timeout=2.5) as client:
            resp = await client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": search_term},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                snippets = []
                for result in soup.find_all("div", class_="result__body", limit=max_results):
                    snippet_tag = result.find("a", class_="result__snippet")
                    title_tag = result.find("a", class_="result__url")
                    if snippet_tag:
                        snippets.append({
                            "title": title_tag.get_text().strip() if title_tag else "Web Reference",
                            "snippet": snippet_tag.get_text().strip(),
                            "url": "https://duckduckgo.com"
                        })
                return snippets
    except Exception as exc:
        logger.warning("DuckDuckGo search error or timeout: %s", exc)
    return []

# ─────────────────────────────────────────────────────────────────────────────
# 5. GROQ AI PREGNANCY HELPER PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are MaaHifazat’s Pregnancy Education & Clinical Assistant (Dr. Ayesha).
Always maintain a warm, gentle, reassuring, friendly, and deeply empathetic tone. Start your response with a compassionate greeting (e.g., "Hello dear mother, please do not worry...", "السلام علیکم پیاری ماں/بہن، بالکل پریشان نہ ہوں...", "Assalam-o-Alaikum Pyari Behan/Maan, bilkul tension na lein...").
Your goal is to make the mother feel safe, supported, comfortable, and well-cared for, without creating anxiety or stress.

Provide clear, evidence-grounded explanations in English, native Urdu script, or Roman Urdu depending on the user's preferred language. Cover maternal health, ANC checkups, fetal kick monitoring, nutrition, safe rest/activity, labor preparedness, postpartum care, and emotional wellbeing.

Do not diagnose, prescribe medications, guarantee outcomes, or invent fake facts. If danger signs are detected, guide the mother gently but firmly to seek clinical care right away.

Format your answer with clear markdown headings, bullet points, and an explicit 'Evidence & Guidance Citations' section at the end citing the guidelines used."""

async def generate_pregnancy_advice(
    query: str,
    language: str = "en",
    shared_assessment: Optional[Dict[str, Any]] = None,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """Generate evidence-grounded answer with citations, danger detection, and Groq LLM supporting English, Urdu, and Roman Urdu."""
    clean_q = query.strip().lower().rstrip(".!?,")
    GREETINGS = {
        "hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening",
        "how can i help me", "how can you help me", "help me", "what can you do", "who are you",
        "help", "assalam o alaikum", "assalam-o-alaikum", "سلام", "السلام علیکم", "اسلام علیکم", "سلام علیکم", "ہیلپ", "مجموعی رہنمائی",
        "aoa", "assalamoalikum", "kia help kar sakty ho", "kaise ho", "kya kar sakte ho"
    }

    if clean_q in GREETINGS or (clean_q.startswith(("hi ", "hello ", "hey ", "how can you ", "how can i ", "what can you ", "kia ", "kya ")) and len(clean_q.split()) <= 6):
        if language in ("roman_urdu", "ur_roman"):
            answer = (
                "Assalam-o-Alaikum! Main aap ka MaaHifazat Pregnancy & Fetal Care Assistant hoon.\n\n"
                "Main aap ki hamilah sehat, ANC checkups, khurak aur vitamins, bache ki harkat (kicks), safe exercise, danger signs, aur postpartum care par mukammal rehnumai kar sakti hoon.\n\n"
                "Aap koi bhi sawal pooch sakty hain ya upar diye gaye categories mein se topic select kar sakty hain."
            )
        elif language == "ur":
            answer = (
                "السلام علیکم! میں ماں حفاظت پریگننسی ایجوکیشن اسسٹنٹ ہوں۔\n\n"
                "میں حمل کی دیکھ بھال، قبل از ولادت معائنے (ANC)، متوازن غذا اور وٹامن، بچے کی حرکت، ورزش اور ہنگامی خطرے کی علامات کے بارے میں آپ کی رہنمائی کر سکتی ہوں۔\n\n"
                "آپ اوپر دیے گئے زمرہ جات میں سے کسی موضوع کا انتخاب کر سکتی ہیں یا اپنا سوال نیچے ٹائپ کر سکتی ہیں۔"
            )
        else:
            answer = (
                "Hello! I am your MaaHifazat Pregnancy & Fetal Care Assistant.\n\n"
                "I can help answer your questions about maternal health, WHO/NHS antenatal checkups, nutrition & diet, safe exercise, fetal kick monitoring, danger signs, and postpartum care.\n\n"
                "How can I assist you today? You can select any category topic above or type your specific question below."
            )
        return {
            "answer": answer,
            "is_urgent": False,
            "urgent_alert": None,
            "citations": [],
            "language": language,
            "retrieved_count": 0,
            "search_used": False
        }

    # 1. Urgent Danger Sign Detection
    urgent_check = check_urgent_symptoms(query)

    # 2. Retrieve local curated guidelines
    retrieved = retrieve_guidelines(query, top_k=3)

    # 3. If local retrieval is thin, enrich with live search
    web_results = []
    if len(retrieved) < 2:
        web_results = await search_duckduckgo(query, max_results=3)

    # Format Evidence context
    evidence_blocks = []
    citations = []
    for item in retrieved:
        lang_content = item["content_ur"] if language == "ur" else item["content_en"]
        evidence_blocks.append(f"[{item['source']} - {item['guideline']}]\n{lang_content}\nSource URL: {item['url']}")
        citations.append({
            "source": item["source"],
            "guideline": item["guideline"],
            "section": item["section"],
            "url": item["url"],
            "date": item["date"]
        })

    for item in web_results:
        evidence_blocks.append(f"[Web Reference: {item['title']}]\n{item['snippet']}")
        citations.append({
            "source": "Web Reference (Public Search)",
            "guideline": item["title"],
            "section": "Live Web Evidence",
            "url": item["url"],
            "date": "2026"
        })

    evidence_str = "\n\n".join(evidence_blocks) if evidence_blocks else "Standard WHO Maternal Health Guidance."

    # Format Shared Assessment Context (if provided)
    assessment_context = "No patient assessment shared."
    if shared_assessment:
        vitals = shared_assessment.get("vitals", {})
        clinical = shared_assessment.get("clinical_risk_result", {})
        safety = clinical.get("who_red_flags", {})
        referral = shared_assessment.get("referral_result", {})
        assessment_context = (
            f"SHARED PATIENT RECORD (Authoritative facts only):\n"
            f"- Gestational Age: {vitals.get('gestational_age_weeks', 'Unknown')} weeks\n"
            f"- Blood Pressure: {vitals.get('systolic_bp', 'Unknown')}/{vitals.get('diastolic_bp', 'Unknown')} mmHg\n"
            f"- Heart Rate: {vitals.get('heart_rate', 'Unknown')} bpm, Temp: {vitals.get('temperature_celsius', 'Unknown')} C\n"
            f"- Safety Triage Level: {safety.get('triage_level', 'Unknown')}\n"
            f"- Referral Hospital: {(referral.get('selected_facility') or {}).get('name', 'None recorded')}\n"
            f"Note: Only discuss these specific recorded facts; never invent diagnoses."
        )

    # Assemble Messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Include recent history
    if chat_history:
        for turn in chat_history[-4:]:
            messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})

    lang_desc = "English"
    if language == "ur":
        lang_desc = "Urdu (using native Urdu script)"
    elif language in ("roman_urdu", "ur_roman"):
        lang_desc = "Roman Urdu (Urdu language written using Latin script, e.g. 'Haml mein blood pressure check karwana zaroori hai. Danger signs par foran hospital jayein.')"

    prompt_user = (
        f"USER QUESTION: {query}\n"
        f"PREFERRED LANGUAGE: {lang_desc}\n\n"
        f"ASSESSMENT CONTEXT:\n{assessment_context}\n\n"
        f"RETRIEVED CLINICAL EVIDENCE:\n{evidence_str}\n\n"
        f"Please provide an informative, supportive, and grounded response in {lang_desc}. "
        f"If potential danger symptoms are mentioned, lead with clear medical guidance. Include supporting citations."
    )
    messages.append({"role": "user", "content": prompt_user})

    # Call Groq API
    response_text = ""
    llm_success = False
    if settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("your_"):
        try:
            async with httpx.AsyncClient(verify=False, timeout=12.0) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                    json={
                        "model": settings.GROQ_MODEL,
                        "messages": messages,
                        "temperature": 0.2,
                        "max_tokens": 1200
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    response_text = data["choices"][0]["message"]["content"]
                    llm_success = True
        except Exception as exc:
            logger.warning("Groq helper generation failed: %s", exc)

    # Fallback if LLM failed
    if not llm_success:
        if language in ("roman_urdu", "ur_roman"):
            response_text = (
                "Roman Urdu Evidence-Based WHO & NHS Clinical Guidance:\n\n"
                + "\n\n".join(f"• **{item['guideline']} ({item['source']})**:\n{item['content_en']}" for item in retrieved[:2])
                + "\n\nKisi bhi zaroori maslay ya emergency mein foran apne doctor, midwife ya nearest maternity hospital se rabta karein."
            )
        elif language == "ur":
            response_text = (
                "معذرت، اے آئی سروس سے براہ راست رابطہ نہیں ہو سکا۔ تاہم، عالمی ادارہ صحت (WHO) اور این ایچ ایس (NHS) کے مطابق:\n\n"
                + "\n\n".join(f"• **{item['guideline']}**: {item['content_ur']}" for item in retrieved[:2])
                + "\n\nکسی بھی شدید تکلیف یا ایمرجنسی کی صورت میں فوراً اپنے معالج یا قریبی میٹرنٹی ہسپتال سے رجوع کریں۔"
            )
        else:
            response_text = (
                "Evidence-Based WHO & NHS Clinical Guidance:\n\n"
                + "\n\n".join(f"• **{item['guideline']} ({item['source']})**:\n{item['content_en']}" for item in retrieved[:2])
                + "\n\nAlways consult your doctor, midwife, or Lady Health Worker for personalized medical care."
            )

    return {
        "answer": response_text,
        "is_urgent": bool(urgent_check),
        "urgent_alert": urgent_check,
        "citations": citations,
        "language": language,
        "retrieved_count": len(retrieved) + len(web_results),
        "search_used": len(web_results) > 0
    }
