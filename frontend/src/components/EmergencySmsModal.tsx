import React, { useState, useEffect } from 'react';
import {
  VillageRiskDetail,
  ShelterRecommendationResult,
  EvacuationPriority,
} from '../types';
import { getStationMetadata } from '../utils/stationMetadata';
import {
  Radio,
  Send,
  X,
  Globe,
  Terminal,
  Users,
  CheckCircle2,
  Info,
  Copy,
  Check,
  ShieldAlert,
  MessageSquare,
  ExternalLink,
  AlertTriangle,
  Key,
  RefreshCw,
  Bot,
} from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  village: VillageRiskDetail | null;
  shelterRec: ShelterRecommendationResult | null;
  priorityDetail?: EvacuationPriority | null;
}

interface DispatchLogLine {
  timestamp: string;
  target: string;
  lang: string;
  risk: string;
  status: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
}

export type SupportedAlertLanguage =
  | 'english'
  | 'hindi'
  | 'garhwali'
  | 'mandyali'
  | 'malayalam'
  | 'kumaoni'
  | 'nepali';

export const EmergencySmsModal: React.FC<Props> = ({
  isOpen,
  onClose,
  village,
  shelterRec,
  priorityDetail,
}) => {
  const stationMeta = getStationMetadata(village?.village_id);
  
  const getInitialLang = (): SupportedAlertLanguage => {
    const primary = stationMeta.primaryLanguage.toLowerCase();
    if (primary.includes('garhwali')) return 'garhwali';
    if (primary.includes('mandyali')) return 'mandyali';
    if (primary.includes('malayalam')) return 'malayalam';
    if (primary.includes('hindi')) return 'hindi';
    return 'english';
  };

  const [lang, setLang] = useState<SupportedAlertLanguage>(getInitialLang());
  const [isSimulating, setIsSimulating] = useState(false);
  const [dispatchLogs, setDispatchLogs] = useState<DispatchLogLine[]>([]);
  const [isCompleted, setIsCompleted] = useState(false);
  const [copied, setCopied] = useState(false);

  // Telegram Integration State
  const [telegramChatId, setTelegramChatId] = useState<string>(() => {
    return localStorage.getItem('apada_telegram_chat_id') || '7558738119';
  });
  const [customBotToken, setCustomBotToken] = useState<string>(() => {
    return localStorage.getItem('apada_telegram_bot_token') || '';
  });
  const [showAdvancedTelegram, setShowAdvancedTelegram] = useState(false);
  const [isTelegramDispatching, setIsTelegramDispatching] = useState(false);
  const [telegramFeedback, setTelegramFeedback] = useState<{
    type: 'idle' | 'success' | 'warning' | 'error';
    message: string;
  }>({ type: 'idle', message: '' });

  const handleUpdateChatId = (newId: string) => {
    setTelegramChatId(newId);
    localStorage.setItem('apada_telegram_chat_id', newId);
  };

  const handleUpdateBotToken = (newToken: string) => {
    setCustomBotToken(newToken);
    localStorage.setItem('apada_telegram_bot_token', newToken);
  };

  useEffect(() => {
    if (!isOpen) {
      setIsSimulating(false);
      setDispatchLogs([]);
      setIsCompleted(false);
      setCopied(false);
    } else {
      setLang(getInitialLang());
    }
  }, [isOpen, village?.village_id]);

  if (!isOpen) return null;

  const villageName = village?.village_name || 'Phata';
  const riskLevel = village?.risk_level || 'CRITICAL';
  const riskScore = village ? Math.round(village.flash_flood_risk_score) : 88;
  const exposedPop = village?.exposure.population_exposed || 2450;
  const shelterName = shelterRec?.recommended_shelter.name || 'Govindghat Relief Center';
  const safeRoute = shelterRec?.route
    ? `Route B via ${shelterRec.route.destination_shelter_name}`
    : 'Route B (Hazard-Bypassing Pathfinder)';
  const blockedRoads = shelterRec?.route.hazards_encountered.length
    ? shelterRec.route.hazards_encountered.join(', ')
    : 'Bridge B-04 / ROAD-010 (Submerged)';

  const topFactor =
    village?.factors && village.factors.length > 0
      ? village.factors[0].feature_label
      : 'Extreme Cloudburst Runoff';

  const priorityScore = priorityDetail
    ? Math.round(priorityDetail.evacuation_priority_score > 1 ? priorityDetail.evacuation_priority_score : priorityDetail.evacuation_priority_score * 100)
    : riskScore;

  const priorityRank = priorityDetail?.rank ? `#${priorityDetail.rank}` : 'P-1';

  // Status calculation
  let statusBadgeText = 'ALERT READY';
  let statusBadgeColor = 'bg-white/10 text-white border-white/20';

  if (isSimulating) {
    statusBadgeText = 'DISPATCHING...';
    statusBadgeColor = 'bg-amber-500/20 text-amber-400 border-amber-500/40 animate-pulse';
  } else if (isCompleted) {
    statusBadgeText = 'DISPATCH COMPLETE';
    statusBadgeColor = 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
  }

  // Localized alert text templates
  const alertMessages: Record<SupportedAlertLanguage, string> = {
    english: `🚨 CRITICAL FLASH-FLOOD WARNING [APADA MITRA]
Location: ${villageName} Village (#${stationMeta.stationNumber.toString().padStart(2, '0')} - ${stationMeta.region})
Risk Level: ${riskLevel} (${riskScore}%)
Evacuation Priority: ${priorityRank} (${priorityScore} pts)
Primary Driver: ${topFactor}
Exposed Population: ${exposedPop.toLocaleString()} residents
Action: Immediate Evacuation to Relief Shelter
Recommended Shelter: ${shelterName}
Safest Route: ${safeRoute}
Avoid Segment: ${blockedRoads}
Authority: District Disaster Management Authority (DDMA)`,

    hindi: `🚨 अत्यंत गंभीर फ़्लैश-फ्लड चेतावनी [आपदा मित्र]
स्थान: ${villageName} गांव (#${stationMeta.stationNumber.toString().padStart(2, '0')} - ${stationMeta.region})
जोखिम स्तर: ${riskLevel} (${riskScore}%)
निकासी प्राथमिकता: ${priorityRank} (${priorityScore} अंक)
मुख्य कारण: ${topFactor}
प्रभावित जनसंख्या: ${exposedPop.toLocaleString()} निवासी
कार्रवाई: तुरंत राहत शिविर में जाएं
अनुशंसित आश्रय: ${shelterName}
सुरक्षित मार्ग: ${safeRoute}
असुरक्षित मार्ग से बचें: ${blockedRoads}
प्राधिकरण: जिला आपदा प्रबंधन प्राधिकरण (DDMA)`,

    garhwali: `🚨 आपदा मित्र गंभीर चेतावनी [आपदा मित्र - गढ़वाल]
स्थान: ${villageName} गाँव (#${stationMeta.stationNumber.toString().padStart(2, '0')} - चमोली/रुद्रप्रयाग)
खतरो स्तर: ${riskLevel} (${riskScore}%)
निकासी प्राथमिकता: ${priorityRank} (${priorityScore} अंक)
मुख्य कारण: ${topFactor}
प्रभावित लोग: ${exposedPop.toLocaleString()} लोग
कार्रवाई: तुरंत सुरक्षित ठौर (Shelter) जावा
सुरक्षित ठौर: ${shelterName}
सुरक्षित बाटो: ${safeRoute}
टूटे बाटो से बचावा: ${blockedRoads}
प्राधिकरण: जिला आपदा प्रबंधन प्राधिकरण (DDMA)`,

    mandyali: `🚨 आपदा मित्र अति गंभीर चेतावनी [आपदा मित्र - मण्डयाली]
स्थान: ${villageName} गाँव (#${stationMeta.stationNumber.toString().padStart(2, '0')} - औट/मण्डी खड्ड)
खतरे री स्थिति: ${riskLevel} (${riskScore}%)
निकासी प्राथमिकता: ${priorityRank} (${priorityScore} अंक)
मुख्य कारण: ${topFactor}
प्रभावित लोक: ${exposedPop.toLocaleString()} निवासी
कार्रवाई: तुरंत सुरक्षित आश्रय (Shelter) जो चला
सुरक्षित रस्ता: ${safeRoute}
खराब रस्ते री मनाही: ${blockedRoads}
प्राधिकरण: जिला आपदा प्रबंधन प्राधिकरण (DDMA, मण्डी)`,

    malayalam: `🚨 അതിതീവ്ര പ്രളയ മുന്നറിയിപ്പ് [ആപദ മിത്ര - വയനാട്]
സ്ഥലം: ${villageName} ഗ്രാമം (#${stationMeta.stationNumber.toString().padStart(2, '0')} - വയനാട്)
അപകട നില: ${riskLevel} (${riskScore}%)
ഒഴിപ്പിക്കൽ മുൻഗണന: ${priorityRank} (${priorityScore} പോയിന്റുകൾ)
പ്രധാന കാരണം: ${topFactor}
ബാധിക്കപ്പെട്ട ജനസംഖ്യ: ${exposedPop.toLocaleString()} ആളുകൾ
നടപടി: ഉടൻ തന്നെ ദുരിതാശ്വാസ ക്യാമ്പിലേക്ക് മാറുക
സുരക്ഷിത ക്യാമ്പ്: ${shelterName}
സുരക്ഷിത പാത: ${safeRoute}
ഒഴിവാക്കേണ്ട പാത: ${blockedRoads}
അതോറിറ്റി: ജില്ലാ ദുരന്തനിവാരണ അതോറിറ്റി (DDMA)`,

    kumaoni: `🚨 आपदा मित्र गंभीर चेतावनी [आपदा मित्र - कुमाऊँनी]
स्थान: ${villageName} गाँव (#${stationMeta.stationNumber.toString().padStart(2, '0')})
खतरो स्तर: ${riskLevel} (${riskScore}%)
निकासी प्राथमिकता: ${priorityRank} (${priorityScore} अंक)
मुख्य कारण: ${topFactor}
प्रभावित लोग: ${exposedPop.toLocaleString()} बासिंदा
कार्रवाई: तुरंत सुरक्षित थान (Shelter) जावा
सुरक्षित थान: ${shelterName}
सुरक्षित बाट: ${safeRoute}
खतरनाक बाट से बचावा: ${blockedRoads}
प्राधिकरण: जिला आपदा प्रबंधन प्राधिकरण (DDMA)`,

    nepali: `🚨 आपतकालीन बाढी चेतावनी [आपदा मित्र]
स्थान: ${villageName} गाउँ (#${stationMeta.stationNumber.toString().padStart(2, '0')})
जोखिम स्तर: ${riskLevel} (${riskScore}%)
निकासी प्राथमिकता: ${priorityRank} (${priorityScore} अंक)
मुख्य कारक: ${topFactor}
प्रभावित जनसंख्या: ${exposedPop.toLocaleString()} बासिन्दा
कार्रवाई: तुरुन्त सुरक्षित आश्रयस्थल जानुहोस्
सुरक्षित आश्रय: ${shelterName}
सुरक्षित सडक: ${safeRoute}
अवरुद्ध सडक जोगिनुहोस्: ${blockedRoads}
प्राधिकरण: जिल्ला विपद् व्यवस्थापन प्राधिकरण (DDMA)`,
  };

  const currentAlertText = alertMessages[lang];

  const handleCopyMessage = () => {
    navigator.clipboard.writeText(currentAlertText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

    const executeTelegramDispatch = async (
      textToSend: string
    ): Promise<{ success: boolean; message: string; statusCode?: number }> => {
      const targetChat = telegramChatId.trim();
      if (!targetChat) {
        const err = 'Please provide a valid Telegram Chat ID or Username.';
        setTelegramFeedback({ type: 'error', message: err });
        return { success: false, message: err };
      }

      setIsTelegramDispatching(true);
      setTelegramFeedback({ type: 'idle', message: '' });

      const token = customBotToken.trim() || '8930236949:AAF4IO2am0V31BonD-bciYLuQHJCdK02NXc';

      try {
        // 1. Try server-side proxy
        const resp = await fetch('/api/alerts/telegram/dispatch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chat_id: targetChat,
            text: textToSend,
            bot_token: customBotToken.trim() || undefined,
          }),
        });

        const result = await resp.json();

        if (result.success) {
          setIsTelegramDispatching(false);
          setTelegramFeedback({
            type: 'success',
            message: `Live alert delivered to Telegram (Chat ID: ${targetChat})! Check your phone.`,
          });
          return { success: true, message: result.message, statusCode: result.status_code };
        } else if (result.status_code !== 500 && !result.message?.includes('getaddrinfo')) {
          setIsTelegramDispatching(false);
          const is429 = result.status_code === 429;
          setTelegramFeedback({
            type: is429 ? 'warning' : 'error',
            message: result.message || 'Telegram dispatch failed.',
          });
          return { success: false, message: result.message, statusCode: result.status_code };
        }
      } catch {
        // Fall through to browser direct fetch
      }

      // 2. Direct browser fetch fallback (if backend DNS / network had issues)
      try {
        const directResp = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chat_id: targetChat,
            text: textToSend,
          }),
        });
        const directJson = await directResp.json();
        setIsTelegramDispatching(false);

        if (directJson.ok) {
          setTelegramFeedback({
            type: 'success',
            message: `Alert delivered directly to Telegram (Chat ID: ${targetChat})!`,
          });
          return { success: true, message: 'Delivered', statusCode: 200 };
        } else {
          const is429 = directJson.error_code === 429;
          setTelegramFeedback({
            type: is429 ? 'warning' : 'error',
            message: directJson.description || 'Failed to dispatch via Telegram.',
          });
          return { success: false, message: directJson.description, statusCode: directJson.error_code };
        }
      } catch {
        setIsTelegramDispatching(false);
        const errMsg = 'Network or adblocker error preventing Telegram connection.';
        setTelegramFeedback({ type: 'error', message: errMsg });
        return { success: false, message: errMsg, statusCode: 500 };
      }
    };

    const handleStartDispatchSimulation = () => {
    // Real Telegram alert dispatch (fires alongside the local simulation)
    executeTelegramDispatch(currentAlertText).then((res) => {
      const timeStr = getNow();
      setDispatchLogs((prev) => [
        ...prev,
        {
          timestamp: timeStr,
          target: villageName,
          lang: lang.toUpperCase(),
          risk: riskLevel,
          status: res.success ? 'TELEGRAM OK' : res.statusCode === 429 ? 'RATE LIMITED' : 'NOT STARTED',
          message: res.success
            ? `TELEGRAM BROADCAST DELIVERED — Recipient Chat ID: ${telegramChatId}`
            : `TELEGRAM BROADCAST ATTEMPT — ${res.message}`,
          type: res.success ? 'success' : res.statusCode === 429 ? 'warning' : 'error',
        },
      ]);
    });

    setIsSimulating(true);
    setIsCompleted(false);
    setDispatchLogs([]);

    const getNow = () => new Date().toLocaleTimeString('en-US', { hour12: false });

    const workflowSteps: { delay: number; msg: string; status: string; type: 'info' | 'success' | 'warning' }[] = [
      { delay: 250, msg: `ALERT CREATED — Target: ${villageName} (${riskLevel})`, status: 'PREPARED', type: 'info' },
      { delay: 700, msg: `TARGET VERIFIED — Population Exposed: ${exposedPop.toLocaleString()}`, status: 'VERIFIED', type: 'info' },
      { delay: 1200, msg: `LANGUAGE PACK — Applied: ${lang.toUpperCase()}`, status: 'LOCALIZED', type: 'info' },
      { delay: 1700, msg: `ROUTE & SHELTER — Shelter: ${shelterName} | Bypass: ${blockedRoads}`, status: 'ATTACHED', type: 'warning' },
      { delay: 2300, msg: `SIMULATED LOCAL DISPATCH COMPLETE — ${exposedPop.toLocaleString()} recipient nodes updated`, status: 'SIMULATED', type: 'success' },
    ];

    workflowSteps.forEach((step) => {
      setTimeout(() => {
        const timeStr = getNow();
        setDispatchLogs((prev) => [
          ...prev,
          {
            timestamp: timeStr,
            target: villageName,
            lang: lang.toUpperCase(),
            risk: riskLevel,
            status: step.status,
            message: step.msg,
            type: step.type,
          },
        ]);
        if (step.type === 'success') {
          setIsSimulating(false);
          setIsCompleted(true);
        }
      }, step.delay);
    });
  };

  return (
    <div className="fixed inset-0 bg-black/85 backdrop-blur-md flex items-center justify-center z-50 p-4 font-sans select-text">
      <div className="bg-[#14181D] border border-white/10 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] select-text">
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/10 bg-[#0E1115] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#FF7A18] to-[#FFB703] p-0.5 flex items-center justify-center shadow-lg shadow-orange-500/20">
              <div className="w-full h-full bg-[#14181D] rounded-[10px] flex items-center justify-center">
                <Radio className="w-5 h-5 text-[#FF7A18] animate-pulse" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-black text-white uppercase tracking-wider font-mono">
                  EMERGENCY ALERT GENERATOR
                </h2>
                <span className={`text-[9px] font-mono font-black px-2 py-0.5 rounded-lg border ${statusBadgeColor}`}>
                  {statusBadgeText}
                </span>
              </div>
              <p className="text-[11px] text-gray-400 font-sans mt-0.5">
                LOCAL MULTILINGUAL SMS DISPATCH SIMULATION
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white p-1.5 rounded-lg hover:bg-white/10 transition cursor-pointer"
            title="Close Alert Console"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-5 overflow-y-auto flex-1 text-xs select-text font-mono">
          {/* Transparency Notice */}
          <div className="bg-amber-500/10 border border-amber-500/30 p-3.5 rounded-xl text-white text-[11px] font-sans flex items-start gap-3 shadow-inner">
            <Info className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <strong className="text-amber-400 font-mono uppercase text-xs">LOCAL SMS SIMULATION</strong>
                <span className="bg-amber-500/20 text-amber-400 text-[9px] font-black px-1.5 py-0.2 rounded border border-amber-500/40 font-mono">OFFLINE DEMO</span>
              </div>
              <p className="leading-normal text-gray-300">
                Demonstration workflow only — no external SMS is transmitted. Derived from live APADA MITRA hazard calculations.
              </p>
            </div>
          </div>

          {/* Alert Target Summary */}
          <div className="space-y-1.5">
            <span className="text-[10px] text-gray-400 uppercase font-black tracking-wider block">
              ALERT TARGET PARAMETERS
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <div className="bg-[#0E1115] border border-white/5 p-3 rounded-xl">
                <span className="text-[10px] text-gray-400 uppercase block font-bold">Target Location</span>
                <span className="text-sm font-black text-white">{villageName}</span>
              </div>

              <div className="bg-[#0E1115] border border-white/5 p-3 rounded-xl">
                <span className="text-[10px] text-gray-400 uppercase block font-bold">Risk Level</span>
                <span className={`text-xs font-black inline-flex items-center gap-1 mt-0.5 ${
                  riskLevel === 'CRITICAL' ? 'text-red-400' : riskLevel === 'HIGH' ? 'text-orange-400' : 'text-emerald-400'
                }`}>
                  <ShieldAlert className="w-3.5 h-3.5" />
                  {riskLevel} ({riskScore}%)
                </span>
              </div>

              <div className="bg-[#0E1115] border border-white/5 p-3 rounded-xl">
                <span className="text-[10px] text-gray-400 uppercase block font-bold">Evacuation Priority</span>
                <span className="text-sm font-black text-[#FFB703]">
                  {priorityRank} <span className="text-xs text-gray-400">({priorityScore} pts)</span>
                </span>
              </div>

              <div className="bg-[#0E1115] border border-white/5 p-3 rounded-xl">
                <span className="text-[10px] text-gray-400 uppercase block font-bold">Exposed Pop</span>
                <span className="text-sm font-black text-white flex items-center gap-1">
                  <Users className="w-3.5 h-3.5 text-[#FF7A18]" />
                  {exposedPop.toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* Multilingual Selector & Message Preview */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-black text-white uppercase tracking-wider flex items-center gap-1.5">
                <Globe className="w-4 h-4 text-[#FF7A18]" />
                MESSAGE PREVIEW
              </span>

              <div className="flex items-center gap-2">
                {/* Language Switcher */}
                <div className="flex bg-[#0E1115] p-1 rounded-xl border border-white/10 text-[10px] overflow-x-auto">
                  <button
                    onClick={() => setLang('garhwali')}
                    className={`px-2.5 py-1 rounded-lg transition font-bold cursor-pointer ${
                      lang === 'garhwali' ? 'bg-[#FF7A18] text-black font-extrabold' : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    गढ़वाली
                  </button>
                  <button
                    onClick={() => setLang('mandyali')}
                    className={`px-2.5 py-1 rounded-lg transition font-bold cursor-pointer ${
                      lang === 'mandyali' ? 'bg-[#FF7A18] text-black font-extrabold' : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    मण्डयाली
                  </button>
                  <button
                    onClick={() => setLang('malayalam')}
                    className={`px-2.5 py-1 rounded-lg transition font-bold cursor-pointer ${
                      lang === 'malayalam' ? 'bg-[#FF7A18] text-black font-extrabold' : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    മലയാളം
                  </button>
                  <button
                    onClick={() => setLang('hindi')}
                    className={`px-2.5 py-1 rounded-lg transition font-bold cursor-pointer ${
                      lang === 'hindi' ? 'bg-[#FF7A18] text-black font-extrabold' : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    हिन्दी
                  </button>
                  <button
                    onClick={() => setLang('english')}
                    className={`px-2.5 py-1 rounded-lg transition font-bold cursor-pointer ${
                      lang === 'english' ? 'bg-[#FF7A18] text-black font-extrabold' : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    ENGLISH
                  </button>
                </div>

                {/* 1-Click Copy Button */}
                <button
                  onClick={handleCopyMessage}
                  className="flex items-center gap-1.5 px-3 py-1 bg-[#181D22] hover:bg-[#1C2228] border border-white/10 text-[#FFB703] rounded-xl text-[10px] font-black transition cursor-pointer"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-[#FF7A18]" />}
                  {copied ? 'COPIED!' : 'COPY ALERT'}
                </button>
              </div>
            </div>

            {/* Generated Message Box */}
            <div className="bg-[#0E1115] p-4 rounded-xl border border-white/10 text-xs font-mono text-white whitespace-pre-wrap leading-relaxed shadow-inner select-text">
              {currentAlertText}
            </div>
          </div>

          {/* Telegram Emergency Broadcast Gateway */}
          <div className="bg-[#0B0E12] border border-cyan-500/30 rounded-xl p-4 space-y-3 shadow-lg shadow-cyan-500/5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-lg bg-[#0088cc]/20 border border-[#0088cc]/40 flex items-center justify-center">
                  <MessageSquare className="w-3.5 h-3.5 text-[#0088cc]" />
                </div>
                <div>
                  <span className="text-[11px] font-black text-white uppercase tracking-wider block font-mono">
                    TELEGRAM BROADCAST GATEWAY
                  </span>
                  <span className="text-[10px] text-gray-400 font-sans block">
                    Dispatch live emergency CAP alerts to real phones & channels
                  </span>
                </div>
              </div>
              <a
                href="https://t.me/apada_mitra_2026_bot"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-[10px] text-cyan-400 hover:text-cyan-300 font-bold bg-cyan-950/60 px-2.5 py-1 rounded-lg border border-cyan-500/30 transition hover:border-cyan-500/60 cursor-pointer"
              >
                <Bot className="w-3 h-3" />
                <span>@apada_mitra_2026_bot</span>
                <ExternalLink className="w-2.5 h-2.5 ml-0.5 opacity-70" />
              </a>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-12 gap-2.5 items-end">
              <div className="sm:col-span-8 space-y-1">
                <div className="flex items-center justify-between">
                  <label className="text-[9px] uppercase font-bold text-gray-400 font-mono tracking-wider">
                    TARGET TELEGRAM CHAT ID
                  </label>
                  <a
                    href="https://t.me/userinfobot"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[9px] text-gray-500 hover:text-cyan-400 transition cursor-pointer"
                  >
                    Find your ID via @userinfobot
                  </a>
                </div>
                <div className="relative">
                  <input
                    type="text"
                    value={telegramChatId}
                    onChange={(e) => handleUpdateChatId(e.target.value)}
                    placeholder="e.g. 7695969720 or -100xxxxxxxxxx"
                    className="w-full bg-[#14181D] border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:border-cyan-500 focus:outline-none placeholder-gray-600"
                  />
                </div>
              </div>

              <div className="sm:col-span-4">
                <button
                  type="button"
                  disabled={isTelegramDispatching}
                  onClick={() => executeTelegramDispatch(currentAlertText)}
                  className={`w-full py-1.5 px-3 rounded-lg text-xs font-black uppercase tracking-wider font-mono transition flex items-center justify-center gap-1.5 shadow-md ${
                    isTelegramDispatching
                      ? 'bg-cyan-600/50 text-cyan-200 cursor-wait'
                      : 'bg-[#0088cc] hover:bg-[#0077b5] text-white cursor-pointer active:scale-95'
                  }`}
                >
                  {isTelegramDispatching ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>SENDING...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" />
                      <span>DISPATCH LIVE</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Live Delivery Status Feedback Pill */}
            {telegramFeedback.type !== 'idle' && (
              <div
                className={`p-2.5 rounded-lg text-[11px] font-sans flex items-start gap-2 border ${
                  telegramFeedback.type === 'success'
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : telegramFeedback.type === 'warning'
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                    : 'bg-red-500/10 border-red-500/30 text-red-300'
                }`}
              >
                {telegramFeedback.type === 'success' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                )}
                <div className="leading-snug">
                  <span className="font-semibold block font-mono text-[10px] uppercase tracking-wider">
                    {telegramFeedback.type === 'success'
                      ? 'DISPATCH CONFIRMED'
                      : telegramFeedback.type === 'warning'
                      ? 'TELEGRAM COOLDOWN NOTICE'
                      : 'DISPATCH NOTICE'}
                  </span>
                  <span>{telegramFeedback.message}</span>
                </div>
              </div>
            )}

            {/* Collapsible Advanced Config (Custom Bot Token) */}
            <div className="pt-1 border-t border-white/5">
              <button
                type="button"
                onClick={() => setShowAdvancedTelegram(!showAdvancedTelegram)}
                className="text-[9px] text-gray-500 hover:text-gray-300 transition flex items-center gap-1 font-mono uppercase cursor-pointer"
              >
                <Key className="w-3 h-3" />
                <span>{showAdvancedTelegram ? 'Hide Advanced Token Settings' : 'Use Custom / Fresh Bot Token (Bypass Flood Limit)'}</span>
              </button>

              {showAdvancedTelegram && (
                <div className="mt-2 space-y-1 bg-[#14181D] p-2.5 rounded-lg border border-white/10">
                  <label className="text-[9px] uppercase font-bold text-gray-400 font-mono tracking-wider block">
                    CUSTOM BOT TOKEN (FROM @BOTFATHER)
                  </label>
                  <input
                    type="text"
                    value={customBotToken}
                    onChange={(e) => handleUpdateBotToken(e.target.value)}
                    placeholder="Leave blank to use default @apada_mitra_2026_bot"
                    className="w-full bg-[#0E1115] border border-white/10 rounded px-2.5 py-1 text-[11px] text-white font-mono focus:border-cyan-500 focus:outline-none placeholder-gray-600"
                  />
                  <p className="text-[9px] text-gray-500 font-sans mt-1">
                    Tip: If Telegram gives a 429 rate limit error, create a free bot in 20 seconds on Telegram with <a href="https://t.me/BotFather" target="_blank" rel="noreferrer" className="text-cyan-400 underline">@BotFather</a> and paste its token here.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Primary Dispatch Action Button */}
          <button
            disabled={isSimulating}
            onClick={handleStartDispatchSimulation}
            className={`w-full font-black py-3 rounded-xl transition flex items-center justify-center gap-2 shadow-xl uppercase tracking-wider text-xs font-mono cursor-pointer ${
              isSimulating
                ? 'bg-amber-500 text-black cursor-wait'
                : isCompleted
                ? 'bg-emerald-500 hover:bg-emerald-400 text-black'
                : 'bg-gradient-to-r from-[#FF7A18] to-[#FFB703] hover:from-[#FF7A18]/90 hover:to-[#FFB703]/90 text-black'
            }`}
          >
            <Send className="w-4 h-4" />
            {isSimulating
              ? 'SIMULATING LOCAL SMS DISPATCH...'
              : isCompleted
              ? 'RE-SIMULATE LOCAL SMS DISPATCH'
              : 'SIMULATE SMS DISPATCH'}
          </button>

          {/* Live Dispatch Terminal Log */}
          {(dispatchLogs.length > 0 || isSimulating) && (
            <div className="space-y-2 bg-[#08090B] p-4 rounded-xl border border-white/10 shadow-2xl font-mono select-text">
              <div className="flex items-center justify-between text-[11px] text-gray-300 border-b border-white/10 pb-2">
                <span className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-white">
                  <Terminal className="w-4 h-4 text-[#FF7A18]" />
                  DISPATCH LOG TERMINAL
                </span>
                <span className="text-[10px] text-gray-500 font-bold">OFFLINE LOG</span>
              </div>

              <div className="space-y-1.5 max-h-48 overflow-y-auto text-[11px]">
                {dispatchLogs.map((log, i) => (
                  <div
                    key={i}
                    className={`flex items-start justify-between gap-2 p-1.5 rounded-lg border bg-[#14181D] ${
                      log.type === 'success'
                        ? 'border-emerald-500/40 text-emerald-400'
                        : log.type === 'warning'
                        ? 'border-amber-500/40 text-amber-400'
                        : 'border-white/10 text-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-2 text-[10px]">
                      <span className="text-gray-500">{log.timestamp}</span>
                      <span className="font-bold text-white">[{log.target}]</span>
                      <span className="text-[#FFB703] font-bold">{log.lang}</span>
                    </div>
                    <div className="text-right text-[10px]">
                      <span className={`font-black px-1.5 py-0.2 rounded text-[9px] ${
                        log.status === 'SIMULATED' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-white/10 text-white'
                      }`}>
                        {log.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {isCompleted && (
                <div className="mt-3 pt-2.5 border-t border-emerald-500/30 text-emerald-400 text-xs font-black flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    SIMULATED DISPATCH COMPLETE — {exposedPop.toLocaleString()} Targets Processed
                  </span>
                  <span className="bg-emerald-500/20 text-emerald-400 text-[10px] px-2 py-0.5 rounded border border-emerald-500/40">
                    STATUS: OK
                  </span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-[#0E1115] border-t border-white/10 text-[10px] text-gray-400 flex items-center justify-between">
          <span>Targeting Engine: APADA MITRA SIH26192</span>
          <span className="text-[#FFB703] font-bold uppercase">LOCAL SMS DISPATCH SIMULATION</span>
        </div>
      </div>
    </div>
  );
};

export default EmergencySmsModal;
