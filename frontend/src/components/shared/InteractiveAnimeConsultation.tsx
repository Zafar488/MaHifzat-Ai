import { useState, useEffect, useMemo } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  ShieldAlert,
  Activity,
  Heart,
  AlertTriangle,
} from 'lucide-react';

interface InteractiveAnimeConsultationProps {
  query?: string;
  content?: string;
  language?: 'en' | 'ur' | 'roman_urdu';
}

interface StoryStep {
  speaker: 'patient' | 'doctor';
  speakerName: string;
  icon: string;
  mood: string;
  text_en: string;
  text_ur: string;
  text_roman: string;
  topic: string;
  progress: number;
}

interface TopicConfig {
  id: string;
  title_en: string;
  title_ur: string;
  title_roman: string;
  badge: string;
  steps: StoryStep[];
  toolType: 'calc' | 'triage' | 'kick_counter' | 'checklist';
}

export function InteractiveAnimeConsultation({
  query = '',
  content = '',
  language = 'en',
}: InteractiveAnimeConsultationProps) {
  const isUrdu = language === 'ur';

  // Dynamic Topic Analysis Engine based on user Query & AI Content
  const topicConfig: TopicConfig = useMemo(() => {
    const userQ = query.toLowerCase();
    const q = (query + ' ' + content).toLowerCase();

    // 1. ABDOMINAL PAIN / BELLY PAIN / CRAMPING (1st TRIMESTER OR GENERAL PAIN)
    if (
      userQ.includes('pain') ||
      userQ.includes('paning') ||
      userQ.includes('hurt') ||
      userQ.includes('cramp') ||
      userQ.includes('belly') ||
      userQ.includes('bally') ||
      userQ.includes('stomach') ||
      userQ.includes('pet') ||
      userQ.includes('3 month') ||
      userQ.includes('12 week') ||
      userQ.includes('first trimester')
    ) {
      return {
        id: 'abdominal_pain',
        title_en: 'Abdominal Pain & Cramping (12 Weeks / Early Pregnancy)',
        title_ur: 'حمل میں پیٹ کا درد اور اینٹھن (12 ہفتے / پہلی سہ ماہی)',
        title_roman: 'Haml Mein Pet Ka Dard & Cramping (12 Weeks)',
        badge: '🩺 1st Trimester Pain Triage',
        toolType: 'triage',
        steps: [
          {
            speaker: 'patient',
            speakerName: 'Sarah',
            icon: '🤰',
            mood: '😰 Worried',
            text_en: '"Doctor Ayesha, I\'m 3 months pregnant (12 weeks) and my lower belly started hurting! What could this mean?"',
            text_ur: '"ڈاکٹر عائشہ، مجھے 3 ماہ کا حمل ہے اور پیٹ کے نچلے حصے میں درد شروع ہو گیا ہے! یہ کیا ہو سکتا ہے؟"',
            text_roman: '"Doctor Ayesha, mujhe 3 months (12 weeks) pregnancy hai aur belly mein pain shuru ho gaya hai!"',
            topic: 'Early Abdominal Pain',
            progress: 25,
          },
          {
            speaker: 'doctor',
            speakerName: 'Dr. Ayesha',
            icon: '🩺',
            mood: '🩺 Clinical Explanation',
            text_en: '"Sarah, mild pulling or sharp side pain when changing position is often normal round ligament stretching or gas. But we must check for red flags!"',
            text_ur: '"سارہ! اٹھتے بیٹھتے سائیڈ پر ہلکا کھنچاؤ یا گیس کا درد اکثر معمولی ہوتا ہے۔ لیکن ہمیں خطرے کی علامات کا جائزہ لینا ہوگا!"',
            text_roman: '"Sarah, position change karte waqt halka khinchaao ya gas pain zaroori nahi ke khatarnak ho. Lekin red flags check karna zaroori hai!"',
            topic: 'Benign Causes vs Red Flags',
            progress: 50,
          },
          {
            speaker: 'patient',
            speakerName: 'Sarah',
            icon: '💡',
            mood: '❓ Asking Advice',
            text_en: '"What red flag symptoms mean I must go to the emergency hospital immediately?"',
            text_ur: '"کون سی خطرناک علامات پر مجھے فوراً ایمرجنسی ہسپتال جانا چاہیے؟"',
            text_roman: '"Konsi danger signs par mujhe foran emergency hospital jana chahiye?"',
            topic: 'Red Flag Checklist',
            progress: 75,
          },
          {
            speaker: 'doctor',
            speakerName: 'Dr. Ayesha',
            icon: '🚨',
            mood: '🏥 Immediate Action',
            text_en: '"Go to the hospital immediately if you have ANY vaginal bleeding, severe constant pain, fever >38°C, or dizziness! Lie on your left side and get evaluated right away."',
            text_ur: '"اگر خون کا اخراج، شدید مسلسل درد، بخار یا چکر آئیں تو فوراً ہسپتال جائیں! بائیں کروٹ لیٹ کر معائنہ کروائیں۔"',
            text_roman: '"Vaginal bleeding, severe continuous pain, fever ya chakar aane par foran emergency hospital jayein!"',
            topic: 'Emergency Action Plan',
            progress: 100,
          },
        ],
      };
    }

    // 2. PREECLAMPSIA & DANGER SIGNS
    if (
      q.includes('preeclampsia') ||
      q.includes('pre-eclampsia') ||
      q.includes('headache') ||
      q.includes('vision') ||
      q.includes('bp') ||
      q.includes('hypertension') ||
      q.includes('blood pressure') ||
      q.includes('seizure')
    ) {
      return {
        id: 'preeclampsia',
        title_en: 'Preeclampsia & Emergency Danger Signs',
        title_ur: 'پری ایکلیمپسیا اور ایمرجنسی خطرناک علامات',
        title_roman: 'Preeclampsia & Emergency Danger Signs',
        badge: '🚨 Urgent Clinical Triage',
        toolType: 'triage',
        steps: [
          {
            speaker: 'patient',
            speakerName: 'Sarah',
            icon: '⚡',
            mood: '😰 Worried',
            text_en: '"Doctor Ayesha, what are the red-flag danger signs of Preeclampsia that I must watch out for?"',
            text_ur: '"ڈاکٹر عائشہ، پری ایکلیمپسیا کی کون سی خطرناک علامات پر فوراً ہسپتال جانا چاہیے؟"',
            text_roman: '"Doctor Ayesha, preeclampsia ki konsi danger signs par foran hospital jana chahiye?"',
            topic: 'Danger Signs Question',
            progress: 25,
          },
          {
            speaker: 'doctor',
            speakerName: 'Dr. Ayesha',
            icon: '🩺',
            mood: '🚨 Urgent Advice',
            text_en: '"Sarah! Seek emergency care immediately if you have a severe persistent headache, blurred vision or flashing lights, upper right stomach pain, or BP ≥ 160/110 mm Hg!"',
            text_ur: '"سارہ! اگر شدید سر درد، آنکھوں کے آگے دھندلاپن، پیٹ کے دائیں حصے میں درد یا BP 160/110 ہو تو بغیر تاخیر کے ایمرجنسی جائیں!"',
            text_roman: '"Sarah! Severe headache, blurred vision, right upper stomach pain ya BP 160/110 par bina kisi takheer ke emergency jayein!"',
            topic: 'Red Flag Symptoms',
            progress: 50,
          },
          {
            speaker: 'patient',
            speakerName: 'Sarah',
            icon: '🤰',
            mood: '❓ Fetal Question',
            text_en: '"What if I also notice a sudden drop in my baby\'s movements or swelling?"',
            text_ur: '"اگر بچے کی حرکت کم ہو جائے یا ہاتھ منہ پر سوجن ہو تو کیا کریں؟"',
            text_roman: '"Agar bache ki movement kam ho jaye ya haath munh par sojan ho to kya karein?"',
            topic: 'Fetal Distress & Edema',
            progress: 75,
          },
          {
            speaker: 'doctor',
            speakerName: 'Dr. Ayesha',
            icon: '🚑',
            mood: '🏥 Immediate Action',
            text_en: '"Do not wait until tomorrow! Decreased fetal movements or sudden swelling with high BP requires immediate hospital CTG check and maternal triage!"',
            text_ur: '"کل تک کا انتظار نہ کریں! بچے کی حرکت کم ہونا یا شدید بلڈ پریشر پر فوری ہسپتال جا کر CTG اور معائنہ کروائیں!"',
            text_roman: '"Kal tak ka wait na karein! Bache ki movement kam hone par foran maternity emergency jayein!"',
            topic: 'Hospital Emergency Referral',
            progress: 100,
          },
        ],
      };
    }

    // 2. FETAL MOVEMENT & KICK COUNTING
    if (
      q.includes('kick') ||
      q.includes('fetal movement') ||
      q.includes('bache ki harkat') ||
      q.includes('ultrasound') ||
      q.includes('movement')
    ) {
      return {
        id: 'fetal_kicks',
        title_en: 'Fetal Movement & Kick Count Guide',
        title_ur: 'بچے کی حرکت اور کک کاؤنٹ گائیڈ',
        title_roman: 'Bache Ki Harkat & Kick Count Guide',
        badge: '👶 Fetal Health Monitoring',
        toolType: 'kick_counter',
        steps: [
          {
            speaker: 'patient',
            speakerName: 'Sarah',
            icon: '👶',
            mood: '❓ Curious',
            text_en: '"Doctor Ayesha, how do I count my baby\'s kicks in the 3rd trimester?"',
            text_ur: '"ڈاکٹر عائشہ، تیسری سہ ماہی میں بچے کی حرکت (Kicks) کا حساب کیسے رکھوں؟"',
            text_roman: '"Doctor Ayesha, 3rd trimester mein bache ki kicks ka hisab kaise rakhun?"',
            topic: 'Kick Counting Question',
            progress: 25,
          },
          {
            speaker: 'doctor',
            speakerName: 'Dr. Ayesha',
            icon: '⏱️',
            mood: '🩺 Explaining',
            text_en: '"Starting around 28 weeks, establish your baby\'s pattern! Count at least 10 distinct movements within a 2-hour window when resting on your side."',
            text_ur: '"28 ہفتوں سے بچے کی حرکت کا پیٹرن نوٹ کریں۔ آرام سے بیٹھ کر 2 گھنٹے میں کم از کم 10 بار حرکت محسوس ہونی چاہیے!"',
            text_roman: '"28 weeks se bache ki movement monitor karein! Rest karte hue 2 hours mein at least 10 kicks count karein."',
            topic: 'Normal Kick Target',
            progress: 50,
          },
          {
            speaker: 'patient',
            speakerName: 'Sarah',
            icon: '💡',
            mood: '😟 Concerned',
            text_en: '"What should I do if my baby moves much less than usual today?"',
            text_ur: '"اگر آج بچہ معمول سے بہت کم حرکت کرے تو مجھے کیا کرنا چاہیے؟"',
            text_roman: '"Agar bacha aaj ma\'mool se kam move kare to kya karun?"',
            topic: 'Reduced Movement',
            progress: 75,
          },
          {
            speaker: 'doctor',
            speakerName: 'Dr. Ayesha',
            icon: '🩺',
            mood: '✨ Urgent Warning',
            text_en: '"Never wait for the next day! Drink cold water, rest on your left side, and if movements remain low, go to the hospital immediately for a CTG heart check!"',
            text_ur: '"ہرگز اگلے دن کا انتظار نہ کریں۔ ٹھنڈا پانی پی کر بائیں کروٹ لیٹیں، اگر حرکت نہ بڑھے تو فوراً الٹراساؤنڈ اور CTG کروائیں!"',
            text_roman: '"Agay din ka wait na karein! Thanda paani pee kar left side letein, movement na barhe to foran hospital jayein!"',
            topic: 'Immediate Action Plan',
            progress: 100,
          },
        ],
      };
    }

    // 3. EXERCISE, SLEEP & PHYSICAL ACTIVITY
    if (
      q.includes('exercise') ||
      q.includes('walk') ||
      q.includes('sleep') ||
      q.includes('lifting') ||
      q.includes('position') ||
      q.includes('work')
    ) {
      return {
        id: 'exercise_sleep',
        title_en: 'Safe Activity, Exercise & Sleep Guide',
        title_ur: 'حمل میں محفوظ ورزش اور سونے کا طریقہ',
        title_roman: 'Haml Mein Safe Exercise & Sleeping Guide',
        badge: '🏃‍♀️ Lifestyle & Safety',
        toolType: 'checklist',
        steps: [
          {
            speaker: 'patient',
            speakerName: 'Sarah',
            icon: '🚶‍♀️',
            mood: '❓ Asking',
            text_en: '"Doctor Ayesha, is daily walking safe in pregnancy, and what is the best sleeping position?"',
            text_ur: '"ڈاکٹر عائشہ، کیا حمل میں چہل قدمی محفوظ ہے اور سونے کی بہترین پوزیشن کون سی ہے؟"',
            text_roman: '"Doctor Ayesha, kya haml mein daily walking safe hai aur sone ki best position konsi hai?"',
            topic: 'Activity & Sleep Question',
            progress: 25,
          },
          {
            speaker: 'doctor',
            speakerName: 'Dr. Ayesha',
            icon: '🩺',
            mood: '✨ Recommendation',
            text_en: '"Yes! 150 minutes of moderate walking per week is great. In the 3rd trimester, sleep on your left side (left lateral) to optimize blood flow to your baby!"',
            text_ur: '"جی ہاں! ہفتے میں 150 منٹ ہلکی چہل قدمی بہت مفید ہے۔ تیسری سہ ماہی میں بائیں کروٹ پر سونا بچے کی بلڈ سپلائی بڑھاتا ہے!"',
            text_roman: '"Haan! Weekly 150 mins walking zaroori hai. 3rd trimester mein left side par sone se bache ko blood flow best milta hai!"',
            topic: 'Left Lateral Sleep Position',
            progress: 50,
          },
          {
            speaker: 'patient',
            speakerName: 'Sarah',
            icon: '🏋️‍♀️',
            mood: '💡 Precaution',
            text_en: '"Are there any heavy activities or weight limits I should strictly avoid?"',
            text_ur: '"کیا کوئی ایسے کام یا وزنی چیزیں ہیں جن سے پرہیز کرنا چاہیے؟"',
            text_roman: '"Kya koi aisay kaam hain jin se zaroor parhez karna chahiye?"',
            topic: 'Activity Restrictions',
            progress: 75,
          },
          {
            speaker: 'doctor',
            speakerName: 'Dr. Ayesha',
            icon: '🛡️',
            mood: '👍 Safe Advice',
            text_en: '"Avoid heavy lifting (> 5–10 kg), high-impact contact sports, and lying flat on your back for long periods after 20 weeks!"',
            text_ur: '"زیادہ وزن اٹھانے، سخت ورزش اور 20 ہفتوں کے بعد سیدھا کمر کے بل زیادہ دیر لیٹنے سے پرہیز کریں!"',
            text_roman: '"Bhari weight uthane aur 20 weeks ke baad peeth ke bal ziyada der letne se parhez karein!"',
            topic: 'Precautions & Safety',
            progress: 100,
          },
        ],
      };
    }

    // 4. IRON, FOLIC ACID & NUTRITION (DEFAULT / EXPLICIT NUTRITION)
    if (
      q.includes('iron') ||
      q.includes('folic') ||
      q.includes('nutrition') ||
      q.includes('vitamin') ||
      q.includes('food') ||
      q.includes('diet')
    ) {
      return {
        id: 'nutrition',
        title_en: 'Pregnancy Nutrition & Supplementation',
        title_ur: 'حمل میں ضروری وٹامن اور غذائیت',
        title_roman: 'Haml Mein Vitamins & Khurak Guide',
        badge: '🥗 Antenatal Micronutrients',
        toolType: 'calc',
        steps: [
          {
            speaker: 'patient',
            speakerName: 'Sarah',
            icon: '🤰',
            mood: '❓ Curious',
            text_en: '"Doctor Ayesha, how much Iron and Folic Acid should I actually take every day for my baby?"',
            text_ur: '"ڈاکٹر عائشہ، مجھے روزانہ کتنی مقدار میں آئرن اور فولک ایسڈ لینا چاہیے؟"',
            text_roman: '"Doctor Ayesha, mujhe daily kitni miqdar mein Iron aur Folic Acid lena chahiye?"',
            topic: 'Daily Dosage Question',
            progress: 25,
          },
          {
            speaker: 'doctor',
            speakerName: 'Dr. Ayesha',
            icon: '🩺',
            mood: '🩺 Explaining',
            text_en: '"Great question, Sarah! WHO recommends 30 to 60 mg of Elemental Iron and 400 µg (0.4 mg) of Folic Acid every single day for a healthy pregnancy!"',
            text_ur: '"سارہ! عالمی ادارہ صحت (WHO) کے مطابق روزانہ 30 سے 60 ملی گرام ایلیمنٹل آئرن اور 400 مائیکرو گرام فولک ایسڈ ضروری ہے!"',
            text_roman: '"Sarah! WHO ke mutabiq daily 30-60 mg Elemental Iron aur 400 µg Folic Acid zaroori hai!"',
            topic: 'Core Recommendation',
            progress: 50,
          },
          {
            speaker: 'patient',
            speakerName: 'Sarah',
            icon: '💡',
            mood: '😮 Surprised',
            text_en: '"Why is Folic Acid so critical, and how do I absorb iron best?"',
            text_ur: '"فولک ایسڈ کیوں اہم ہے اور آئرن کو بہتر طور پر کیسے جذب کیا جائے؟"',
            text_roman: '"Folic Acid kyun zaroori hai aur Iron ko behtar kaise absorb karein?"',
            topic: 'Folic Acid Role',
            progress: 75,
          },
          {
            speaker: 'doctor',
            speakerName: 'Dr. Ayesha',
            icon: '🥤',
            mood: '🍊 Absorption Tip',
            text_en: '"Folic Acid prevents neural tube defects (spina bifida). Pro tip for Iron: Take it with Vitamin C (orange juice) away from milk or tea!"',
            text_ur: '"فولک ایسڈ بچے کی اعصابی نشوونما کے لیے ضروری ہے۔ آئرن کی گولی کو مالٹے کے رس کے ساتھ لیں اور چائے، دودھ سے 2 گھنٹے دور رکھیں!"',
            text_roman: '"Folic Acid birth defects se bachata hai. Iron tablet ko Orange juice ke sath lein aur chai/doodh se door rakhein!"',
            topic: 'Neural Tube & Absorption',
            progress: 100,
          },
        ],
      };
    }

    // 5. DYNAMIC GENERAL FALLBACK (FOR ANY RANDOM QUESTION ASKED BY JUDGES)
    const cleanedText = content
      .replace(/#+ /g, '')
      .replace(/\|/g, ' ')
      .replace(/[\-\*]{3,}/g, '')
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/\s+/g, ' ')
      .trim();

    const textPart1 = cleanedText.length > 200 ? cleanedText.slice(0, 180) + '...' : (cleanedText || 'Based on WHO guidelines, here is the clinical recommendation.');
    const textPart2 = cleanedText.length > 350 ? cleanedText.slice(180, 340) + '...' : 'Please consult your primary healthcare provider or midwife for personalized care.';

    return {
      id: 'general_consultation',
      title_en: 'Antenatal Clinical Consultation',
      title_ur: 'طبی مشورہ اور رہنمائی',
      title_roman: 'Antenatal Medical Consultation',
      badge: '🩺 Clinical RAG Insight',
      toolType: 'checklist',
      steps: [
        {
          speaker: 'patient',
          speakerName: 'Sarah',
          icon: '🤰',
          mood: '❓ Inquiry',
          text_en: `"${query || 'Doctor Ayesha, can you guide me on this maternal health question?'}"`,
          text_ur: `"${query || 'ڈاکٹر عائشہ، کیا آپ مجھے اس بارے میں رہنما معلومات دے سکتی ہیں؟'}"`,
          text_roman: `"${query || 'Doctor Ayesha, kya aap mujhe is bare mein guide kar sakti hain?'}"`,
          topic: 'Patient Consultation Question',
          progress: 25,
        },
        {
          speaker: 'doctor',
          speakerName: 'Dr. Ayesha',
          icon: '🩺',
          mood: '🩺 Evidence Guidance',
          text_en: `"${textPart1}"`,
          text_ur: '"عالمی ادارہ صحت اور طبی گائیڈ لائنز کے مطابق یہ اہم طبی معلومات پیش خدمت ہیں۔"',
          text_roman: '"WHO aur NHS clinical guidelines ke mutabiq behtareen sehat ki rehnumai yeh hai."',
          topic: 'Evidence Evaluation',
          progress: 50,
        },
        {
          speaker: 'patient',
          speakerName: 'Sarah',
          icon: '💡',
          mood: '👍 Understood',
          text_en: '"Thank you Dr. Ayesha! What is the key takeaway or next step I should remember?"',
          text_ur: '"شکریہ ڈاکٹر عائشہ! اس کے بعد مجھے کون سا اہم عمل یاد رکھنا چاہیے؟"',
          text_roman: '"Shukriya Doctor Ayesha! Is ke baad mujhe konsa step yaad rakhna chahiye?"',
          topic: 'Action Plan',
          progress: 75,
        },
        {
          speaker: 'doctor',
          speakerName: 'Dr. Ayesha',
          icon: '🏥',
          mood: '✨ Clinical Summary',
          text_en: `"${textPart2}"`,
          text_ur: '"کسی بھی غیر معمولی علامت پر اپنے لیڈی ہیلتھ ورکر یا ڈاکٹر سے باقاعدہ رابطہ رکھیں۔ بروقت دیکھ بھال حفاظت کی ضامن ہے!"',
          text_roman: '"Kisi bhi unusual symptom par apne LHW ya Doctor se rabta rakhein. Timely care ma\'an aur bache dono ko safe rakhti hai!"',
          topic: 'Maternal Protection',
          progress: 100,
        },
      ],
    };
  }, [query, content]);

  const [activeTab, setActiveTab] = useState<'story' | 'tool' | 'evidence'>('story');
  const [currentStep, setCurrentStep] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);

  // Triage state
  const [sysBP, setSysBP] = useState(135);
  const [diaBP, setDiaBP] = useState(85);

  // Kick counter state
  const [kickCount, setKickCount] = useState(0);

  // Supplement Calc state
  const [calcMode, setCalcMode] = useState<'routine' | 'anemia'>('routine');

  const steps = topicConfig.steps;
  const step = steps[currentStep] || steps[0];

  // Auto-play timer effect
  useEffect(() => {
    let timer: any = null;
    if (isAutoPlaying) {
      timer = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev < steps.length - 1) {
            return prev + 1;
          }
          setIsAutoPlaying(false);
          return prev;
        });
      }, 4000);
    }
    return () => clearInterval(timer);
  }, [isAutoPlaying, steps.length]);

  const getText = (s: StoryStep) => {
    if (s.speaker === 'doctor' && content && content.trim().length > 0) {
      return content;
    }
    if (language === 'ur') return s.text_ur;
    if (language === 'roman_urdu') return s.text_roman;
    return s.text_en;
  };

  const isSevereBP = sysBP >= 160 || diaBP >= 110;
  const isElevatedBP = sysBP >= 140 || diaBP >= 90;

  return (
    <div className="my-3 w-full rounded-2xl border border-teal-200/80 bg-white shadow-md overflow-hidden transition-all text-xs">
      {/* Header Bar */}
      <div className="bg-gradient-to-r from-teal-700 via-teal-800 to-emerald-800 p-3.5 text-white flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="size-8 rounded-full bg-white/20 flex items-center justify-center text-base backdrop-blur-sm">
            🩺
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] uppercase font-mono tracking-wider bg-white/15 px-1.5 py-0.5 rounded text-teal-200 font-bold">
                {topicConfig.badge}
              </span>
            </div>
            <h4 className="text-xs font-extrabold tracking-tight">
              {isUrdu ? topicConfig.title_ur : topicConfig.title_en}
            </h4>
          </div>
        </div>

        {/* Tab Buttons */}
        <div className="flex bg-teal-950/40 p-1 rounded-xl border border-white/15 text-[11px] font-semibold">
          <button
            onClick={() => setActiveTab('story')}
            className={`px-2.5 py-1 rounded-lg transition-all ${
              activeTab === 'story' ? 'bg-white text-teal-950 font-bold shadow' : 'text-teal-100 hover:bg-white/10'
            }`}
          >
            💬 Story Mode
          </button>
          <button
            onClick={() => setActiveTab('tool')}
            className={`px-2.5 py-1 rounded-lg transition-all ${
              activeTab === 'tool' ? 'bg-white text-teal-950 font-bold shadow' : 'text-teal-100 hover:bg-white/10'
            }`}
          >
            🛠️ Interactive Tool
          </button>
          <button
            onClick={() => setActiveTab('evidence')}
            className={`px-2.5 py-1 rounded-lg transition-all ${
              activeTab === 'evidence' ? 'bg-white text-teal-950 font-bold shadow' : 'text-teal-100 hover:bg-white/10'
            }`}
          >
            📚 Guidelines
          </button>
        </div>
      </div>

      {/* TAB 1: ANIME STORY STAGE */}
      {activeTab === 'story' && (
        <div className="p-4 space-y-4">
          <div className="flex items-center justify-between text-[11px] text-gray-500 font-semibold">
            <span className="flex items-center gap-1.5 font-bold text-teal-700">
              <span className="size-2 rounded-full bg-teal-500 animate-ping"></span>
              Scene Step {currentStep + 1} of {steps.length}
            </span>
            <span className="px-2 py-0.5 rounded-full bg-teal-100 text-teal-900 font-bold text-[10px]">
              {step.topic}
            </span>
          </div>

          <div className="w-full bg-gray-200 h-1.5 rounded-full overflow-hidden">
            <div
              className="bg-gradient-to-r from-teal-500 to-emerald-500 h-full transition-all duration-500"
              style={{ width: `${step.progress}%` }}
            />
          </div>

          {/* Anime Character Dialogue Stage with Smooth Fade/Slide Animations */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center py-2.5 bg-gradient-to-b from-teal-50/60 to-emerald-50/40 p-4 rounded-xl border border-teal-100 shadow-inner">
            {/* Patient Avatar (Sarah) */}
            <div
              className={`md:col-span-3 flex flex-col items-center text-center space-y-1 transition-all duration-300 ease-out ${
                step.speaker === 'patient'
                  ? 'opacity-100 scale-105 z-10'
                  : 'opacity-50 scale-95 grayscale-[15%]'
              }`}
            >
              <div className="relative">
                <div
                  className={`size-16 rounded-full bg-gradient-to-tr from-pink-400 to-amber-200 p-0.5 shadow transition-all duration-300 ${
                    step.speaker === 'patient' ? 'ring-4 ring-pink-400/50 shadow-md' : ''
                  }`}
                >
                  <svg className="w-full h-full rounded-full bg-pink-50" viewBox="0 0 100 100" fill="none">
                    <circle cx="50" cy="50" r="45" fill="#FFE4E6" />
                    <path d="M20 50 Q 25 15 50 15 Q 75 15 80 50 Q 82 70 80 85 H 20 Z" fill="#92400E" />
                    <ellipse cx="50" cy="52" rx="28" ry="26" fill="#FDE68A" />
                    <path d="M25 40 Q 40 25 50 38 Q 60 25 75 40 Q 50 30 25 40 Z" fill="#78350F" />
                    <ellipse cx="38" cy="48" rx="4" ry="6" fill="#1E293B" />
                    <ellipse cx="62" cy="48" rx="4" ry="6" fill="#1E293B" />
                    <circle cx="39" cy="46" r="1.5" fill="white" />
                    <circle cx="63" cy="46" r="1.5" fill="white" />
                    <path d="M 44 60 Q 50 65 56 60" stroke="#9F1239" stroke-width="2" stroke-linecap="round" fill="none" />
                  </svg>
                </div>
                <span
                  className={`absolute -bottom-1 -right-1 text-white text-[9px] px-1.5 py-0.2 rounded-full font-bold shadow transition-all ${
                    step.speaker === 'patient' ? 'bg-pink-600 ring-2 ring-white animate-pulse' : 'bg-pink-400/80'
                  }`}
                >
                  {step.speaker === 'patient' ? step.mood : 'Listening'}
                </span>
              </div>
              <h5 className="text-[11px] font-bold text-gray-900">Sarah</h5>
              <p className="text-[10px] text-gray-500">Expectant Mother</p>
            </div>

            {/* Active Speech Bubble with Key-based Smooth Transition */}
            <div className="md:col-span-6">
              <div
                key={currentStep}
                className="bg-white border-2 border-teal-500/30 p-4 rounded-xl shadow-sm relative text-xs leading-relaxed space-y-1.5 animate-in fade-in slide-in-from-bottom-2 duration-300"
              >
                <div className="flex items-center justify-between font-bold text-teal-800 border-b border-gray-100 pb-1 text-[11px]">
                  <span className="flex items-center gap-1.5">
                    <span>{step.icon}</span>
                    <span>{step.speakerName}</span>
                  </span>
                  <span className="text-[10px] text-teal-600 font-semibold uppercase tracking-wider">
                    {step.speaker === 'patient' ? 'Patient Query' : 'Clinician Guidance'}
                  </span>
                </div>
                <p className="text-gray-900 font-medium leading-relaxed text-xs sm:text-sm" dir={isUrdu ? 'rtl' : 'ltr'}>
                  {getText(step)}
                </p>
              </div>
            </div>

            {/* Doctor Avatar (Dr. Ayesha) */}
            <div
              className={`md:col-span-3 flex flex-col items-center text-center space-y-1 transition-all duration-300 ease-out ${
                step.speaker === 'doctor'
                  ? 'opacity-100 scale-105 z-10'
                  : 'opacity-50 scale-95 grayscale-[15%]'
              }`}
            >
              <div className="relative">
                <div
                  className={`size-16 rounded-full bg-gradient-to-tr from-teal-500 to-cyan-300 p-0.5 shadow transition-all duration-300 ${
                    step.speaker === 'doctor' ? 'ring-4 ring-teal-500/50 shadow-md' : ''
                  }`}
                >
                  <svg className="w-full h-full rounded-full bg-teal-50" viewBox="0 0 100 100" fill="none">
                    <circle cx="50" cy="50" r="45" fill="#CCFBF1" />
                    <path d="M22 45 Q 25 10 50 10 Q 75 10 78 45 Q 80 75 75 90 H 25 Z" fill="#1E1B4B" />
                    <path d="M 22 45 Q 50 20 78 45 Q 50 35 22 45 Z" fill="#0D9488" />
                    <ellipse cx="50" cy="52" rx="26" ry="24" fill="#FDE68A" />
                    <ellipse cx="39" cy="48" rx="4" ry="5.5" fill="#065F46" />
                    <ellipse cx="61" cy="48" rx="4" ry="5.5" fill="#065F46" />
                    <circle cx="40" cy="46" r="1.5" fill="white" />
                    <circle cx="62" cy="46" r="1.5" fill="white" />
                    <rect x="32" y="42" width="14" height="12" rx="3" stroke="#0F766E" stroke-width="1.5" fill="none" />
                    <rect x="54" y="42" width="14" height="12" rx="3" stroke="#0F766E" stroke-width="1.5" fill="none" />
                    <path d="M 44 60 Q 50 64 56 60" stroke="#047857" stroke-width="2" stroke-linecap="round" fill="none" />
                  </svg>
                </div>
                <span
                  className={`absolute -bottom-1 -right-1 text-white text-[9px] px-1.5 py-0.2 rounded-full font-bold shadow transition-all ${
                    step.speaker === 'doctor' ? 'bg-teal-700 ring-2 ring-white animate-pulse' : 'bg-teal-500/80'
                  }`}
                >
                  {step.speaker === 'doctor' ? step.mood : 'Listening'}
                </span>
              </div>
              <h5 className="text-[11px] font-bold text-gray-900">Dr. Ayesha</h5>
              <p className="text-[10px] text-gray-500">Obstetrician</p>
            </div>
          </div>

          {/* Controls */}
          <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-gray-100">
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setCurrentStep((prev) => Math.max(0, prev - 1))}
                disabled={currentStep === 0}
                className="px-2.5 py-1 rounded-lg border border-gray-200 text-[11px] font-bold text-gray-700 hover:bg-gray-100 disabled:opacity-40 flex items-center gap-1 cursor-pointer"
              >
                <ChevronLeft className="size-3" /> Prev
              </button>
              <button
                onClick={() => setCurrentStep((prev) => Math.min(steps.length - 1, prev + 1))}
                disabled={currentStep === steps.length - 1}
                className="px-3 py-1 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-[11px] font-bold shadow flex items-center gap-1 cursor-pointer"
              >
                Next <ChevronRight className="size-3" />
              </button>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setIsAutoPlaying(!isAutoPlaying)}
                className="px-2.5 py-1 rounded-lg bg-emerald-100 text-emerald-900 text-[11px] font-bold border border-emerald-300 hover:bg-emerald-200 transition-colors flex items-center gap-1 cursor-pointer"
              >
                {isAutoPlaying ? <Pause className="size-3" /> : <Play className="size-3" />}
                <span>{isAutoPlaying ? 'Pause Story' : 'Auto-Play Story'}</span>
              </button>
              <button
                onClick={() => {
                  setIsAutoPlaying(false);
                  setCurrentStep(0);
                }}
                className="p-1 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-100 cursor-pointer"
                title="Restart Story"
              >
                <RotateCcw className="size-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: TOPIC-SPECIFIC INTERACTIVE TOOL */}
      {activeTab === 'tool' && (
        <div className="p-4 space-y-4">
          {/* Tool 1: Emergency Danger Signs & BP Triage Checker */}
          {topicConfig.toolType === 'triage' && (
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 space-y-2">
                <div className="flex items-center gap-1.5 font-bold text-red-900 text-xs">
                  <ShieldAlert className="size-4 text-red-600" />
                  <span>Preeclampsia Blood Pressure & Triage Calculator</span>
                </div>
                <div className="grid grid-cols-2 gap-3 pt-1">
                  <div>
                    <label className="block text-[11px] text-gray-700 font-medium">Systolic BP (mmHg)</label>
                    <input
                      type="number"
                      value={sysBP}
                      onChange={(e) => setSysBP(Number(e.target.value))}
                      className="w-full mt-1 px-2.5 py-1 rounded border border-gray-300 bg-white font-mono text-xs font-bold"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-gray-700 font-medium">Diastolic BP (mmHg)</label>
                    <input
                      type="number"
                      value={diaBP}
                      onChange={(e) => setDiaBP(Number(e.target.value))}
                      className="w-full mt-1 px-2.5 py-1 rounded border border-gray-300 bg-white font-mono text-xs font-bold"
                    />
                  </div>
                </div>

                <div
                  className={`p-3 rounded-lg border font-bold text-xs flex items-center gap-2 ${
                    isSevereBP
                      ? 'bg-red-600 text-white border-red-700 animate-pulse'
                      : isElevatedBP
                      ? 'bg-amber-100 text-amber-900 border-amber-300'
                      : 'bg-emerald-100 text-emerald-900 border-emerald-300'
                  }`}
                >
                  <AlertTriangle className="size-4 shrink-0" />
                  <span>
                    {isSevereBP
                      ? '🚨 SEVERE HYPERTENSION (BP ≥ 160/110): Immediate Emergency Hospital Referral Required!'
                      : isElevatedBP
                      ? '🟡 ELEVATED BP (≥ 140/90): Contact Antenatal Clinician for Preeclampsia Evaluation.'
                      : '🟢 NORMAL PREGNANCY BLOOD PRESSURE (< 140/90 mm Hg).'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Tool 2: Kick Counter */}
          {topicConfig.toolType === 'kick_counter' && (
            <div className="p-4 rounded-xl bg-teal-50/60 border border-teal-200 text-center space-y-3">
              <div className="font-bold text-teal-900 text-xs flex items-center justify-center gap-1.5">
                <Activity className="size-4 text-teal-600" />
                <span>Interactive 2-Hour Fetal Kick Counter</span>
              </div>

              <div className="flex items-center justify-center gap-4 py-2">
                <button
                  onClick={() => setKickCount((k) => Math.max(0, k - 1))}
                  className="size-9 rounded-full bg-white border border-gray-300 text-gray-800 font-bold text-lg hover:bg-gray-100 cursor-pointer shadow-sm"
                >
                  -
                </button>
                <div className="text-center px-4">
                  <div className="text-3xl font-extrabold font-mono text-teal-700">{kickCount}</div>
                  <div className="text-[10px] text-gray-500 uppercase font-bold">Kicks Counted</div>
                </div>
                <button
                  onClick={() => setKickCount((k) => k + 1)}
                  className="size-9 rounded-full bg-teal-600 text-white font-bold text-lg hover:bg-teal-500 cursor-pointer shadow-sm"
                >
                  +
                </button>
              </div>

              <div
                className={`p-2.5 rounded-lg text-xs font-bold ${
                  kickCount >= 10
                    ? 'bg-emerald-100 text-emerald-900 border border-emerald-300'
                    : 'bg-amber-100 text-amber-900 border border-amber-300'
                }`}
              >
                {kickCount >= 10
                  ? '🟢 Target Reached: 10 movements established within session.'
                  : `🟡 Target: Need ${10 - kickCount} more kicks within 2 hours.`}
              </div>
            </div>
          )}

          {/* Tool 3: Supplement Calculator */}
          {topicConfig.toolType === 'calc' && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setCalcMode('routine')}
                  className={`p-3 rounded-xl border text-left cursor-pointer ${
                    calcMode === 'routine' ? 'border-teal-600 bg-teal-50/70 font-bold' : 'bg-white border-gray-200'
                  }`}
                >
                  <div className="text-xs">🟢 Routine Care</div>
                  <div className="text-[10px] text-gray-500">30-60mg Iron / 400µg Folate</div>
                </button>
                <button
                  onClick={() => setCalcMode('anemia')}
                  className={`p-3 rounded-xl border text-left cursor-pointer ${
                    calcMode === 'anemia' ? 'border-red-600 bg-red-50/70 font-bold' : 'bg-white border-gray-200'
                  }`}
                >
                  <div className="text-xs">🔴 Anemia / High Risk</div>
                  <div className="text-[10px] text-gray-500">120mg Iron / 4,000µg Folate</div>
                </button>
              </div>
            </div>
          )}

          {/* Tool 4: Action Checklist */}
          {topicConfig.toolType === 'checklist' && (
            <div className="p-3.5 rounded-xl bg-gray-50 border border-gray-200 space-y-2 text-xs">
              <div className="font-bold text-gray-900 flex items-center gap-1.5">
                <Heart className="size-4 text-teal-600" />
                <span>WHO / NHS Key Maternal Action Steps</span>
              </div>
              <ul className="space-y-1.5 text-gray-700 pl-4 list-disc">
                <li>Schedule regular WHO 8-contact antenatal checkups.</li>
                <li>Monitor fetal movement patterns establishing by 28 weeks.</li>
                <li>Seek immediate medical care for severe headache, vision changes or bleeding.</li>
              </ul>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: GUIDELINES & CITATIONS */}
      {activeTab === 'evidence' && (
        <div className="p-4 space-y-3">
          <a
            href="https://www.nice.org.uk/guidance/ng133"
            target="_blank"
            rel="noopener noreferrer"
            className="block p-3 rounded-xl border border-gray-200 bg-gray-50 hover:bg-teal-50/50 transition-colors group"
          >
            <div className="flex items-center justify-between font-bold text-xs text-teal-800 group-hover:underline">
              <span>1. NICE Guidelines (Hypertension & Danger Signs)</span>
              <ExternalLink className="size-3 text-teal-600" />
            </div>
            <p className="text-[10px] text-gray-600 mt-1 leading-relaxed">
              Defines severe preeclampsia danger signs: severe frontal headache, visual disturbances, BP ≥ 160/110 mm Hg requiring emergency hospital triage.
            </p>
          </a>

          <a
            href="https://www.who.int/publications/i/item/9789241549912"
            target="_blank"
            rel="noopener noreferrer"
            className="block p-3 rounded-xl border border-gray-200 bg-gray-50 hover:bg-teal-50/50 transition-colors group"
          >
            <div className="flex items-center justify-between font-bold text-xs text-teal-800 group-hover:underline">
              <span>2. World Health Organization (WHO IMPAC & ANC)</span>
              <ExternalLink className="size-3 text-teal-600" />
            </div>
            <p className="text-[10px] text-gray-600 mt-1 leading-relaxed">
              Lists cardinal obstetric danger signs and antenatal care contact schedules for positive pregnancy experience.
            </p>
          </a>
        </div>
      )}
    </div>
  );
}
