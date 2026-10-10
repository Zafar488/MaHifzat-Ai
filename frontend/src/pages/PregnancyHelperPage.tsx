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
} from 'lucide-react';
import { api } from '@/lib/api-client';

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

const SUGGESTED_PROMPTS_EN = [
  'What are normal fetal movements in the 3rd trimester?',
  'Which foods and nutrients are essential during pregnancy?',
  'What are the danger signs of pre-eclampsia?',
  'Is light walking or lifting safe during pregnancy?',
  'What happens during routine antenatal checkups (ANC)?',
];

const SUGGESTED_PROMPTS_UR = [
  'حمل کی تیسری سہ ماہی میں بچے کی حرکت کیسی ہونی چاہیے؟',
  'حاملہ خواتین کے لیے آئرن اور متوازن غذا کی کیا اہمیت ہے؟',
  'پری ایکلیمپسیا (ہائی بلڈ پریشر) کی خطرے کی علامات کیا ہیں؟',
  'کیا حمل کے دوران ہلکی ورزش یا وزن اٹھانا محفوظ ہے؟',
  'قبل از ولادت باقاعدہ معائنے (ANC) کا کیا شیڈول ہے؟',
];

export default function PregnancyHelperPage() {
  const [language, setLanguage] = useState<'en' | 'ur'>('en');
  const [query, setQuery] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      setError(err.response?.data?.detail || err.message || 'Failed to consult medical guidance assistant.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = () => {
    setChatHistory([]);
    setError(null);
  };

  const isUrdu = language === 'ur';
  const suggestedPrompts = isUrdu ? SUGGESTED_PROMPTS_UR : SUGGESTED_PROMPTS_EN;

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:px-8 space-y-6">
      {/* Header & Language Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900 flex items-center gap-2.5">
            <Sparkles className="size-6 text-teal-600" />
            {isUrdu ? 'رہنما برائے حمل (Pregnancy Helper AI)' : 'Pregnancy Education Helper'}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {isUrdu
              ? 'عالمی ادارہ صحت (WHO) اور برطانوی این ایچ ایس (NHS/NICE) کی مستند طبی ہدایات پر مبنی معلوماتی چیٹ۔'
              : 'Evidence-grounded WHO & NHS clinical guidance assistant with automatic danger-sign detection.'}
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

      {/* Suggested Prompt Chips */}
      <div className="bg-teal-50/50 rounded-xl border border-teal-100 p-4 space-y-2">
        <h3 className="text-xs font-bold text-teal-900 uppercase tracking-wider flex items-center gap-1.5">
          <BookOpen className="size-4 text-teal-600" />
          {isUrdu ? 'اکثر پوچھے جانے والے طبی سوالات:' : 'Suggested Clinical Education Topics:'}
        </h3>
        <div className="flex flex-wrap gap-2 pt-1">
          {suggestedPrompts.map((promptText, idx) => (
            <button
              key={idx}
              onClick={() => handleSendMessage(promptText)}
              disabled={isLoading}
              className="text-xs px-3 py-1.5 rounded-full bg-white border border-teal-200 text-teal-900 hover:bg-teal-600 hover:text-white transition-all shadow-sm disabled:opacity-50 text-left"
            >
              {promptText}
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Conversation Container */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden flex flex-col h-[520px]">
        {/* Thread Box */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {chatHistory.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-8 space-y-3">
              <div className="size-12 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center">
                <Bot className="size-6" />
              </div>
              <h3 className="text-sm font-bold text-gray-900">
                {isUrdu ? 'حمل کی دیکھ بھال کے بارے میں اپنا سوال پوچھیں' : 'Ask Any Maternal & Fetal Care Question'}
              </h3>
              <p className="text-xs text-gray-500 max-w-md">
                {isUrdu
                  ? 'ہمارا جدید گائیڈنس سسٹم WHO اور NHS کی مستند گائیڈ لائنز کے ذریعے طبی جوابات اور خطرے کی علامات کا تجزیہ فراہم کرتا ہے۔'
                  : 'Get instant clinical answers backed by WHO & NHS guidelines. Emergency danger signs are flagged immediately.'}
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

                  {/* Message Bubble */}
                  <div
                    className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-teal-700 text-white rounded-br-none shadow-sm'
                        : 'bg-gray-50 text-gray-900 border border-gray-200 rounded-bl-none'
                    }`}
                    dir={isUrdu ? 'rtl' : 'ltr'}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>

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
            <div className="flex items-center gap-3 text-teal-700 text-xs font-semibold p-4 bg-teal-50 rounded-xl border border-teal-100 w-fit">
              <Loader2 className="size-4 animate-spin" />
              <span>{isUrdu ? 'طبی گائیڈ لائنز سے معلومات حاصل کی جا رہی ہیں...' : 'Consulting WHO/NHS clinical guidelines...'}</span>
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
                  ? 'اپنا سوال یہاں لکھیں... (مثال: بلڈ پریشر کی علامات)'
                  : 'Ask a pregnancy or maternal health question...'
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
