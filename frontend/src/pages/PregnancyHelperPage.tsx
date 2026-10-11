import { useState, useRef, useEffect } from 'react';
import {
  Send,
  Loader2,
  AlertTriangle,
  BookOpen,
  Globe,
  Sparkles,
  Bot,
  User,
  ExternalLink,
  Trash2,
  Heart,
  ShieldAlert,
  Apple,
  Baby,
  Activity,
  Calendar,
  Smile,
} from 'lucide-react';
import { api } from '@/lib/api-client';
import { getErrorMessage } from '@/lib/utils';
import { InteractiveAnimeConsultation } from '@/components/shared/InteractiveAnimeConsultation';
import { FormattedMarkdown } from '@/components/shared/FormattedMarkdown';

interface Citation {
  source: string;
  guideline: string;
  section?: string;
  url?: string;
}

interface UrgentAlert {
  alert_en?: string;
  alert_ur?: string;
  action_en?: string;
  action_ur?: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  is_urgent?: boolean;
  urgent_alert?: UrgentAlert;
  search_used?: boolean;
}

interface TopicCategory {
  id: string;
  name_en: string;
  name_ur: string;
  name_roman: string;
  icon: any;
  prompts_en: string[];
  prompts_ur: string[];
  prompts_roman: string[];
}

const CATEGORIES: TopicCategory[] = [
  {
    id: 'danger_signs',
    name_en: 'Danger Signs & Emergency',
    name_ur: 'خطرے کی ہنگامی علامات',
    name_roman: 'Danger Signs & Emergency',
    icon: ShieldAlert,
    prompts_en: [
      'What are the danger signs of pre-eclampsia?',
      'What should I do if fetal movements decrease?',
      'What are warning signs requiring immediate hospital care?',
    ],
    prompts_ur: [
      'پری ایکلیمپسیا (ہائی بلڈ پریشر) کی خطرے کی علامات کیا ہیں؟',
      'اگر بچے کی حرکت کم ہو جائے تو کیا کرنا چاہیے؟',
      'حمل میں ہنگامی ہسپتال جانے کی اہم علامات کون سی ہیں؟',
    ],
    prompts_roman: [
      'Preeclampsia aur high BP ki danger signs kya hain?',
      'Bache ki harkat (kicks) kam hone par kya karna chahiye?',
      'Severe headache ya vision issue par foran kya karein?',
    ],
  },
  {
    id: 'nutrition',
    name_en: 'Nutrition & Supplements',
    name_ur: 'غذائیت اور ضروری وٹامن',
    name_roman: 'Khurak & Vitamins',
    icon: Apple,
    prompts_en: [
      'Which foods and nutrients are essential during pregnancy?',
      'How much iron and folic acid should I take daily?',
      'Which foods should be strictly avoided in pregnancy?',
    ],
    prompts_ur: [
      'حاملہ خواتین کے لیے آئرن اور متوازن غذا کی کیا اہمیت ہے؟',
      'روزانہ آئرن اور فولک ایسڈ کی کتنی مقدار ضروری ہے؟',
      'حمل کے دوران کن غذاؤں سے پرہیز کرنا چاہیے؟',
    ],
    prompts_roman: [
      'Haml mein iron aur folic acid kitni zaroori hai?',
      'Daily diet mein konsi khurak shamil karein?',
      'Hamilah khawateen ko konsi cheezon se parhez karna chahiye?',
    ],
  },
  {
    id: 'fetal_care',
    name_en: 'Fetal Growth & Kicks',
    name_ur: 'بچے کی حرکت اور نشوونما',
    name_roman: 'Bache ki Harkat & Kicks',
    icon: Baby,
    prompts_en: [
      'What are normal fetal movements in the 3rd trimester?',
      'How do I monitor my baby’s kick pattern establishing by 28 weeks?',
      'When is the first ultrasound recommended?',
    ],
    prompts_ur: [
      'حمل کی تیسری سہ ماہی میں بچے کی حرکت کیسی ہونی چاہیے؟',
      '28 ہفتوں پر بچے کی حرکت کے پیٹرن کو کیسے سمجھیں؟',
      'پہلا الٹراساؤنڈ کب کروانا چاہیے؟',
    ],
    prompts_roman: [
      '28 weeks par bache ki kick count kaise monitor karein?',
      'Third trimester mein bache ki normal movement kitni hoti hai?',
      'Pehla ultrasound kab karwana chahiye?',
    ],
  },
  {
    id: 'exercise_activity',
    name_en: 'Safe Activity & Rest',
    name_ur: 'ورزش، آرام اور احتیاط',
    name_roman: 'Safe Activity & Rest',
    icon: Activity,
    prompts_en: [
      'Is light walking or lifting safe during pregnancy?',
      'What are safe sleeping positions in the 3rd trimester?',
      'How much physical activity is recommended weekly?',
    ],
    prompts_ur: [
      'کیا حمل کے دوران ہلکی ورزش یا وزن اٹھانا محفوظ ہے؟',
      'تیسری سہ ماہی میں سونے کی بہترین پوزیشن کون سی ہے؟',
      'حمل کے دوران ہفتہ وار کتنی چہل قدمی کرنی چاہیے؟',
    ],
    prompts_roman: [
      'Haml mein light walking aur exercise safe hai?',
      'Sone ki behtareen position konsi hai (Left lateral)?',
      'Weight uthane ki safe limit kya hai?',
    ],
  },
  {
    id: 'anc_schedule',
    name_en: 'Antenatal Visits (ANC)',
    name_ur: 'قبل از ولادت معائنے (ANC)',
    name_roman: 'ANC Checkup Schedule',
    icon: Calendar,
    prompts_en: [
      'What happens during routine antenatal checkups (ANC)?',
      'What is the WHO recommended 8-contact schedule?',
      'Which blood tests and vaccines are needed in pregnancy?',
    ],
    prompts_ur: [
      'قبل از ولادت باقاعدہ معائنے (ANC) کا کیا شیڈول ہے؟',
      'عالمی ادارہ صحت (WHO) کے 8 طبی رابطوں کا مقصد کیا ہے؟',
      'حمل میں کون سے بلڈ ٹیسٹ اور ٹیکے (Vaccines) ضروری ہیں؟',
    ],
    prompts_roman: [
      'WHO ke 8 antenatal checkups ka kya schedule hai?',
      'Haml mein konsay blood tests aur vaccines zaroori hain?',
      'Regular ANC visit par kya checkup hota hai?',
    ],
  },
  {
    id: 'postpartum_newborn',
    name_en: 'Postpartum & Baby Care',
    name_ur: 'پیدائش کے بعد کی دیکھ بھال',
    name_roman: 'Delivery ke baad ki dekh bhal',
    icon: Heart,
    prompts_en: [
      'What are essential newborn care and breastfeeding tips?',
      'What is normal postpartum bleeding (lochia)?',
      'What are warning signs in a newborn baby?',
    ],
    prompts_ur: [
      'نومولود بچے کی دیکھ بھال اور دودھ پلانے کے اہم اصول؟',
      'پیدائش کے بعد خون کے اخراج (لوچیا) کے معمول کی علامات؟',
      'نومولود بچے میں کن علامات پر ڈاکٹر کو دکھانا چاہیے؟',
    ],
    prompts_roman: [
      'Newborn baby care aur breastfeeding ke zaroori tareeqay?',
      'Normal postpartum bleeding (lochia) ki alamat?',
      'Delivery ke baad ma\'an ki dekh bhal kaise karein?',
    ],
  },
  {
    id: 'mental_health',
    name_en: 'Mental Health & Wellbeing',
    name_ur: 'ذہنی صحت اور جذباتی دیکھ بھال',
    name_roman: 'Zehni Sehat & Stress',
    icon: Smile,
    prompts_en: [
      'How to manage pregnancy mood swings and anxiety?',
      'What are signs of postpartum depression?',
      'How can family members support a pregnant mother?',
    ],
    prompts_ur: [
      'حمل کے دوران ذہنی تناؤ اور موڈ کی تبدیلیوں سے کیسے نمٹیں؟',
      'پیدائش کے بعد ڈپریشن (Postpartum Depression) کی علامات؟',
      'گھر والے حاملہ خاتون کی کس طرح مدد کر سکتے ہیں؟',
    ],
    prompts_roman: [
      'Haml ke dauran mood swings aur anxiety ko kaise manage karein?',
      'Postpartum depression ki alamat kya hain?',
      'Ghar walay hamilah khatoon ki madad kaise karein?',
    ],
  },
];

export default function PregnancyHelperPage() {
  const [language, setLanguage] = useState<'en' | 'ur' | 'roman_urdu'>('en');
  const [selectedCategory, setSelectedCategory] = useState<string>('danger_signs');
  const [query, setQuery] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeStoryIndex, setActiveStoryIndex] = useState<number | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory, isLoading]);

  const handleSendMessage = async (textToSend?: string) => {
    const messageText = textToSend || query;
    if (!messageText.trim() || isLoading) return;

    const userMsg: ChatMessage = { role: 'user', content: messageText };
    setChatHistory((prev) => [...prev, userMsg]);
    setQuery('');
    setError(null);
    setIsLoading(true);

    try {
      const historyPayload = chatHistory.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await api.post('/helper/chat', {
        query: messageText,
        language: language,
        chat_history: historyPayload,
      });

      const data = res.data;
      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: data.advice || data.answer || 'No response generated.',
        citations: data.citations || [],
        is_urgent: data.is_urgent || false,
        urgent_alert: data.urgent_alert || null,
        search_used: data.search_used || false,
      };

      setChatHistory((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setError(getErrorMessage(err, 'Failed to consult medical guidance assistant.'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = () => {
    setChatHistory([]);
    setError(null);
  };

  const isUrdu = language === 'ur';
  const activeCategoryObj = CATEGORIES.find((c) => c.id === selectedCategory) || CATEGORIES[0];
  const activePrompts = language === 'ur'
    ? activeCategoryObj.prompts_ur
    : language === 'roman_urdu'
    ? activeCategoryObj.prompts_roman
    : activeCategoryObj.prompts_en;

  const getCategoryName = (cat: TopicCategory) => {
    if (language === 'ur') return cat.name_ur;
    if (language === 'roman_urdu') return cat.name_roman;
    return cat.name_en;
  };

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:px-8 space-y-6">
      {/* Header & Language Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900 flex items-center gap-2.5">
            <Sparkles className="size-6 text-teal-600" />
            {language === 'ur'
              ? 'رہنما برائے حمل (Pregnancy Helper AI)'
              : language === 'roman_urdu'
              ? 'Pregnancy Helper Assistant (Roman Urdu)'
              : 'Pregnancy Education & Clinical Assistant'}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {language === 'ur'
              ? 'عالمی ادارہ صحت (WHO) اور این ایچ ایس (NHS) کی طبی گائیڈ لائنز پر مبنی ہر قسم کے سوالات کا حل۔'
              : language === 'roman_urdu'
              ? 'WHO aur NHS guidelines par mabni pregnancy ke tamam sawalat ka Roman Urdu mein jawab.'
              : 'Evidence-based WHO, NHS & NICE maternal healthcare assistant supporting all clinical and daily care questions.'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="inline-flex rounded-lg bg-gray-100 p-1 border border-gray-200 text-xs font-medium">
            <button
              onClick={() => setLanguage('en')}
              className={`px-3 py-1.5 rounded-md transition-colors ${
                language === 'en' ? 'bg-white text-teal-900 font-bold shadow-sm' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              English
            </button>
            <button
              onClick={() => setLanguage('ur')}
              className={`px-3 py-1.5 rounded-md transition-colors ${
                language === 'ur' ? 'bg-white text-teal-900 font-bold shadow-sm' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              اردو (Urdu)
            </button>
            <button
              onClick={() => setLanguage('roman_urdu')}
              className={`px-3 py-1.5 rounded-md transition-colors ${
                language === 'roman_urdu' ? 'bg-white text-teal-900 font-bold shadow-sm' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Roman Urdu
            </button>
          </div>

          {chatHistory.length > 0 && (
            <button
              onClick={handleClearHistory}
              className="p-2 text-gray-400 hover:text-red-600 transition-colors rounded-lg border border-gray-200 bg-white"
              title="Clear Chat History"
            >
              <Trash2 className="size-4" />
            </button>
          )}
        </div>
      </div>

      {/* Categorized Knowledge Topics */}
      <div className="bg-teal-50/50 rounded-2xl border border-teal-100 p-5 space-y-4 shadow-sm">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-teal-900 uppercase tracking-wider flex items-center gap-1.5">
            <BookOpen className="size-4 text-teal-600" />
            {language === 'ur'
              ? 'طبی زمرہ جات اور عام سوالات:'
              : language === 'roman_urdu'
              ? 'Categories aur Aam Sawalat:'
              : 'Clinical Topic Categories & Quick Prompts:'}
          </h3>
        </div>

        {/* Category Tabs */}
        <div className="flex flex-wrap gap-2 border-b border-teal-200/60 pb-3">
          {CATEGORIES.map((cat) => {
            const Icon = cat.icon;
            const isSelected = cat.id === selectedCategory;
            return (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`inline-flex items-center gap-1.5 text-xs px-3 py-2 rounded-lg font-medium transition-all ${
                  isSelected
                    ? 'bg-teal-700 text-white shadow-sm'
                    : 'bg-white text-teal-900 border border-teal-200 hover:bg-teal-100'
                }`}
              >
                <Icon className="size-3.5" />
                <span>{getCategoryName(cat)}</span>
              </button>
            );
          })}
        </div>

        {/* Category Prompts */}
        <div className="flex flex-wrap gap-2 pt-1">
          {activePrompts.map((promptText, idx) => (
            <button
              key={idx}
              onClick={() => handleSendMessage(promptText)}
              disabled={isLoading}
              className="text-xs px-3 py-1.5 rounded-full bg-white border border-teal-300 text-teal-950 hover:bg-teal-600 hover:text-white transition-all shadow-sm disabled:opacity-50 text-left"
            >
              {promptText}
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Conversation Container */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden flex flex-col h-[540px]">
        {/* Thread Box */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {chatHistory.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-8 space-y-3">
              <div className="size-12 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center">
                <Bot className="size-6" />
              </div>
              <h3 className="text-sm font-bold text-gray-900">
                {language === 'ur'
                  ? 'حمل اور نومولود کی دیکھ بھال کا کوئی بھی سوال پوچھیں'
                  : language === 'roman_urdu'
                  ? 'Haml aur newborn baby care ka koi bhi sawal poochein'
                  : 'Ask Any Maternal, Fetal & Postpartum Question'}
              </h3>
              <p className="text-xs text-gray-500 max-w-lg leading-relaxed">
                {language === 'ur'
                  ? 'ہمارا جدید RAG گائیڈنس ماڈیول WHO اور NHS کی مستند طبی گائیڈ لائنز کے ذریعے مکمل رہنمائی اور خطرے کی علامات کا خودکار پتہ لگاتا ہے۔'
                  : language === 'roman_urdu'
                  ? 'WHO aur NHS clinical guidelines par mabni AI assistant emergency danger signs aur hamilah sehat par mukammal rehnumai karta hai.'
                  : 'Grounded in WHO, NHS & NICE clinical guidelines. Connects directly to backend medical search with emergency danger-sign screening.'}
              </p>
            </div>
          ) : (
            chatHistory.map((msg, index) => (
              <div
                key={index}
                className={`flex gap-3.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="size-8 rounded-full bg-teal-600 text-white flex items-center justify-center shrink-0 shadow-sm mt-0.5">
                    <Bot className="size-4" />
                  </div>
                )}

                <div className={`space-y-3 max-w-2xl ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  {/* Urgent Danger Sign Banner */}
                  {msg.is_urgent && (
                    <div className="p-4 rounded-xl bg-red-50 border-2 border-red-200 text-red-950 space-y-1 shadow-sm">
                      <div className="flex items-center gap-2 font-bold text-xs uppercase text-red-900">
                        <AlertTriangle className="size-4 text-red-600 shrink-0" />
                        <span>🚨 {isUrdu ? (msg.urgent_alert?.alert_ur || 'خطرناک علامات کا پتہ چلا') : (msg.urgent_alert?.alert_en || 'URGENT DANGER SIGN DETECTED')}</span>
                      </div>
                      <p className="text-xs text-red-800 leading-relaxed font-medium">
                        {isUrdu
                          ? (msg.urgent_alert?.action_ur || 'فوری طور پر نزدیکی اسپتال یا لیڈی ہیلتھ ورکر سے رابطہ کریں۔')
                          : (msg.urgent_alert?.action_en || 'Seek immediate emergency hospital evaluation.')}
                      </p>
                    </div>
                  )}

                  {/* User Message Bubble */}
                  {msg.role === 'user' && (
                    <div className="p-4 rounded-2xl bg-teal-700 text-white rounded-br-none shadow-sm text-xs sm:text-sm leading-relaxed" dir={isUrdu ? 'rtl' : 'ltr'}>
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  )}

                  {/* Assistant Message Card */}
                  {msg.role === 'assistant' && (
                    <div className="w-full space-y-3">
                      <div className="rounded-2xl border border-teal-100 bg-white p-5 shadow-sm space-y-3" dir={isUrdu ? 'rtl' : 'ltr'}>
                        {/* Header Badge */}
                        <div className="flex items-center justify-between border-b border-teal-100/70 pb-3">
                          <div className="flex items-center gap-2">
                            <span className="flex size-7 items-center justify-center rounded-lg bg-teal-600 text-white font-bold text-xs">
                              🩺
                            </span>
                            <div>
                              <h4 className="text-xs font-bold text-teal-950">
                                {isUrdu ? 'ڈاکٹر عائشہ (طبی اسسٹنٹ AI)' : 'Dr. Ayesha (Clinical AI Assistant)'}
                              </h4>
                              <p className="text-[10px] text-teal-700 font-medium">
                                {isUrdu ? 'مستند گائیڈ لائنز پر مبنی طبی جواب' : 'WHO, NHS & NICE Evidence-Based Response'}
                              </p>
                            </div>
                          </div>
                          <span className="inline-flex items-center gap-1 rounded-full bg-teal-50 px-2.5 py-1 text-[10px] font-bold text-teal-700 border border-teal-200">
                            <Sparkles className="size-3 text-teal-600" />
                            {isUrdu ? 'لائیو RAG جواب' : 'Grounded AI'}
                          </span>
                        </div>

                        {/* Real LLM Response Body */}
                        <div className="pt-1">
                          <FormattedMarkdown content={msg.content} isRtl={isUrdu} />
                        </div>
                      </div>

                      {/* Story Mode Toggle Button */}
                      <button
                        type="button"
                        onClick={() => setActiveStoryIndex(activeStoryIndex === index ? null : index)}
                        className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-700 hover:text-teal-900 bg-teal-50 border border-teal-200 px-3 py-1.5 rounded-lg transition-colors"
                      >
                        <span>💬 {activeStoryIndex === index ? (isUrdu ? 'اسٹوری موڈ چھپائیں' : 'Hide Story Mode Scene') : (isUrdu ? 'اسٹوری موڈ منظر دیکھیں' : 'View Story Mode Scene')}</span>
                      </button>

                      {/* Animated Doctor & Patient Anime Dialogue Consultation Card for Assistant */}
                      {activeStoryIndex === index && (
                        <div className="mt-2">
                          <InteractiveAnimeConsultation
                            query={chatHistory[index - 1]?.content || ''}
                            content={msg.content}
                            language={language}
                          />
                        </div>
                      )}
                    </div>
                  )}

                  {/* Evidence Citations */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="p-3 rounded-lg bg-teal-50/60 border border-teal-200/80 text-xs space-y-1.5">
                      <div className="font-semibold text-teal-900 flex items-center gap-1.5">
                        <BookOpen className="size-3.5 text-teal-700" />
                        <span>{isUrdu ? 'مستند طبی حوالہ جات:' : 'Evidence & Guideline Citations:'}</span>
                      </div>
                      <ul className="space-y-1 pl-4 list-disc text-teal-800">
                        {msg.citations.map((c, cIdx) => (
                          <li key={cIdx}>
                            <strong>{c.source}</strong>: <em>{c.guideline}</em> {c.section ? `(${c.section})` : ''}
                            {c.url && (
                              <a
                                href={c.url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-0.5 ml-1 text-teal-600 underline"
                              >
                                link <ExternalLink className="size-2.5" />
                              </a>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {msg.search_used && (
                    <div className="text-[11px] text-gray-500 flex items-center gap-1">
                      <Globe className="size-3 text-gray-400" />
                      <span>{isUrdu ? 'تلاش میں پبلک میڈیکل سرچ شامل کی گئی' : 'DuckDuckGo public medical search included'}</span>
                    </div>
                  )}
                </div>

                {msg.role === 'user' && (
                  <div className="size-8 rounded-full bg-gray-200 text-gray-700 flex items-center justify-center shrink-0 mt-0.5">
                    <User className="size-4" />
                  </div>
                )}
              </div>
            ))
          )}

          {isLoading && (
            <div className="flex items-center gap-3 text-teal-900 text-xs font-semibold p-4 bg-teal-50/80 rounded-2xl border border-teal-200 shadow-sm w-fit animate-pulse" dir={isUrdu ? 'rtl' : 'ltr'}>
              <Loader2 className="size-4 animate-spin text-teal-600 shrink-0" />
              <span>
                {language === 'ur'
                  ? '🌸 پیاری ماں/بہن، بالکل پریشان نہ ہوں! ڈاکٹر عائشہ آپ کے لیے شفقت آمیز جواب تیار کر رہی ہیں...'
                  : language === 'roman_urdu'
                  ? '🌸 Pyari maan/behan, bilkul tension na lein! Dr. Ayesha aap ke liye friendly aur caring rehnumai tayyar kar rahi hain...'
                  : '🌸 Hello dear mother! Dr. Ayesha is preparing your warm, personalized clinical guidance...'}
              </span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 bg-gray-50 border-t border-gray-200">
          {error && (
            <div className="mb-3 p-2.5 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700 flex items-center gap-2">
              <AlertTriangle className="size-4 shrink-0 text-red-500" />
              <span>{error}</span>
            </div>
          )}

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={
                isUrdu
                  ? 'حمل یا بچے کی دیکھ بھال کے بارے میں اپنا سوال پوچھیں... (مثال: بلڈ پریشر یا حرکت)'
                  : 'Ask any question about pregnancy, nutrition, fetal kicks, checkups or baby care...'
              }
              className="flex-1 rounded-xl border border-gray-300 bg-white px-4 py-3 text-xs sm:text-sm text-gray-900 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500 shadow-sm"
              dir={isUrdu ? 'rtl' : 'ltr'}
            />

            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="rounded-xl bg-teal-600 px-5 py-3 text-sm font-semibold text-white shadow-sm hover:bg-teal-500 disabled:opacity-50 transition-colors flex items-center gap-2 shrink-0"
            >
              <span>{isUrdu ? 'ارسال کریں' : 'Send'}</span>
              <Send className="size-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
