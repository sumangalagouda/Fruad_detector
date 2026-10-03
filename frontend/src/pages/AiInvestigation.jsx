import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { caseApi, aiApi } from '../api/client';
import CaseNav from '../components/CaseNav';
import EvidenceCard from '../components/EvidenceCard';
import StatusBadge from '../components/StatusBadge';
import {
  Bot,
  Send,
  Sparkles,
  HelpCircle,
  ThumbsUp,
  ThumbsDown,
  AlertCircle,
  CheckCircle2,
  FileCheck2,
  CornerDownLeft,
  User,
  Wrench,
  ShieldAlert,
} from 'lucide-react';

export default function AiInvestigation() {
  const { id } = useParams();
  const [caseData, setCaseData] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeInvestigationId, setActiveInvestigationId] = useState(null);
  const [feedbackSuccess, setFeedbackSuccess] = useState('');
  const chatEndRef = useRef(null);

  const quickPrompts = [
    'Why is this account suspicious?',
    'Which detectors triggered and why?',
    'Show the money trail for the incoming funds.',
    'Are there any circular flows detected?',
    'Are there any layering chains?',
    'Why was transaction T999 flagged?', // Trap case prompt
    'Summarize key findings for this investigation.',
  ];

  const fetchInit = async () => {
    try {
      const [caseRes, invRes] = await Promise.all([caseApi.get(id), aiApi.getInvestigations(id)]);
      setCaseData(caseRes.data.data.case);

      const sessions = invRes.data.data.investigations || [];
      if (sessions.length > 0) {
        const latest = sessions[0];
        setActiveInvestigationId(latest.investigation_id);
        setMessages(latest.messages || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchInit();
  }, [id]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleAsk = async (queryText) => {
    const textToSend = queryText || question;
    if (!textToSend.trim() || loading) return;

    const userMsg = {
      message_id: `temp-${Date.now()}`,
      sender: 'user',
      user_question: textToSend,
      response_text: textToSend,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setQuestion('');
    setLoading(true);

    try {
      const res = await aiApi.investigate(id, textToSend, activeInvestigationId);
      const data = res.data.data;
      setActiveInvestigationId(data.investigation_id);

      const assistantMsg = {
        message_id: data.message_id,
        sender: 'assistant',
        user_question: textToSend,
        response_text: data.answer,
        facts: data.parsed_sections?.facts || [],
        detected_patterns: data.parsed_sections?.detected_patterns || [],
        evidence_items: data.parsed_sections?.evidence || [],
        interpretations: data.parsed_sections?.interpretation || [],
        limitations: data.parsed_sections?.limitations || [],
        next_steps: data.parsed_sections?.next_steps || [],
        tool_calls: data.tool_calls || [],
        feedback: [],
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error(err);
      const errMsg = {
        message_id: `err-${Date.now()}`,
        sender: 'assistant',
        user_question: textToSend,
        response_text: 'An error occurred while analyzing case evidence. Please verify tool execution.',
        limitations: ['System error occurred in processing request.'],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (messageId, type) => {
    try {
      await aiApi.submitFeedback(activeInvestigationId, {
        message_id: messageId,
        feedback_type: type,
        comment: `Investigator flagged as ${type}`,
      });
      setFeedbackSuccess(`Feedback '${type}' recorded for audit & evaluation.`);
      setTimeout(() => setFeedbackSuccess(''), 4000);
      await fetchInit();
    } catch (e) {
      console.error('Failed to submit feedback', e);
    }
  };

  if (!caseData) return <div className="text-center py-20 text-slate-400">Loading AI investigation studio...</div>;

  return (
    <div>
      <CaseNav
        caseId={caseData.case_id}
        caseNumber={caseData.case_number}
        title={caseData.title}
        score={caseData.suspicion_score}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-210px)] min-h-[620px]">
          {/* Left Panel: Case Context & Prompt Chips */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between overflow-y-auto space-y-5">
            <div className="space-y-4">
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block mb-1">
                  Active Subject
                </span>
                <h3 className="font-bold text-white text-base">{caseData.person?.full_name}</h3>
                <span className="font-mono text-[11px] text-emerald-400">{caseData.case_number}</span>
              </div>

              {/* Suspicion Score Micro Badge */}
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Suspicion Score</span>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-2xl font-extrabold font-mono text-white">
                    {caseData.suspicion_score?.toFixed(1) || '0.0'}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">/ 100</span>
                </div>
                <p className="text-[10px] text-slate-400">Strictly grounded in deterministic evidence.</p>
              </div>

              {/* Suggested Questions */}
              <div>
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2 flex items-center gap-1.5">
                  <HelpCircle className="w-3.5 h-3.5 text-emerald-400" />
                  Investigative Prompts
                </span>
                <div className="space-y-1.5">
                  {quickPrompts.map((p, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleAsk(p)}
                      disabled={loading}
                      className="w-full text-left p-2 rounded-lg bg-slate-950/70 hover:bg-slate-800 text-slate-300 text-xs transition-colors border border-slate-800/80 hover:border-slate-700 flex items-start gap-1.5 disabled:opacity-50"
                    >
                      <span className="text-emerald-400 font-bold shrink-0">›</span>
                      <span className="leading-snug">{p}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800 text-[11px] text-slate-400 space-y-1">
              <p className="flex items-center gap-1 text-slate-300 font-medium">
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                Anti-Hallucination Enforced
              </p>
              <p>The AI assistant cannot modify scores or fabricate non-existent transactions.</p>
            </div>
          </div>

          {/* Right Panel: Chat Stream */}
          <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl flex flex-col justify-between overflow-hidden">
            {/* Messages Area */}
            <div className="flex-1 p-6 overflow-y-auto space-y-6">
              {feedbackSuccess && (
                <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{feedbackSuccess}</span>
                </div>
              )}

              {messages.length === 0 ? (
                <div className="text-center py-20 space-y-3">
                  <div className="w-12 h-12 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl mx-auto flex items-center justify-center text-emerald-400">
                    <Bot className="w-6 h-6" />
                  </div>
                  <h3 className="text-base font-bold text-white">FINTELLIGENCE AI Investigation Assistant</h3>
                  <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
                    Ask natural language questions about financial flows, suspicious triggers, circular patterns, or specific
                    transactions. All answers are grounded in verified evidence.
                  </p>
                </div>
              ) : (
                messages.map((m) => {
                  const isUser = m.sender === 'user';
                  return (
                    <div
                      key={m.message_id}
                      className={`flex gap-3 text-xs leading-relaxed ${isUser ? 'justify-end' : 'justify-start'}`}
                    >
                      {!isUser && (
                        <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0 mt-1">
                          <Bot className="w-4 h-4" />
                        </div>
                      )}

                      <div
                        className={`max-w-3xl rounded-2xl p-5 space-y-4 shadow-lg ${
                          isUser
                            ? 'bg-emerald-600 text-white font-medium rounded-br-none'
                            : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-bl-none'
                        }`}
                      >
                        {/* Display User Prompt or Assistant Formatted Response */}
                        {isUser ? (
                          <p className="text-sm">{m.response_text || m.user_question}</p>
                        ) : (
                          <div className="space-y-4">
                            {/* Answer Header */}
                            <div>
                              <p className="text-sm font-semibold text-white leading-relaxed whitespace-pre-wrap">
                                {m.response_text.split('\n\n')[0].replace(/^ANSWER\n?/, '')}
                              </p>
                            </div>

                            {/* Facts Block */}
                            {m.facts && m.facts.length > 0 && (
                              <div className="bg-slate-900/90 rounded-xl p-3 border border-slate-800 space-y-1">
                                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                                  Verified Facts
                                </span>
                                <ul className="space-y-1 text-slate-300">
                                  {m.facts.map((f, i) => (
                                    <li key={i} className="flex items-start gap-1.5">
                                      <span className="text-emerald-400 font-bold">•</span>
                                      <span>{f}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* Detected Patterns Block */}
                            {m.detected_patterns && m.detected_patterns.length > 0 && (
                              <div className="bg-slate-900/90 rounded-xl p-3 border border-slate-800 space-y-1">
                                <span className="text-[10px] uppercase font-bold text-amber-400 tracking-wider block">
                                  Detected Patterns
                                </span>
                                <ul className="space-y-1 text-slate-300">
                                  {m.detected_patterns.map((p, i) => (
                                    <li key={i} className="flex items-start gap-1.5">
                                      <span className="text-amber-400 font-bold">•</span>
                                      <span>{p}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* Evidence Cards */}
                            {m.evidence_items && m.evidence_items.length > 0 && (
                              <div className="space-y-2">
                                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                                  Citations & Provenance
                                </span>
                                <div className="space-y-1.5">
                                  {m.evidence_items.map((ev, i) => (
                                    <div
                                      key={i}
                                      className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-300 font-mono flex items-center justify-between"
                                    >
                                      <span>{ev}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Limitations */}
                            {m.limitations && m.limitations.length > 0 && (
                              <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-800/80">
                                <span className="text-[10px] uppercase font-bold text-slate-500 block">Limitations</span>
                                <ul className="list-disc list-inside">
                                  {m.limitations.map((lim, i) => (
                                    <li key={i}>{lim}</li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {/* Tool Calls Accordion */}
                            {m.tool_calls && m.tool_calls.length > 0 && (
                              <div className="pt-2 border-t border-slate-800/80">
                                <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">
                                  Tools Executed ({m.tool_calls.length})
                                </span>
                                <div className="flex flex-wrap gap-1.5">
                                  {m.tool_calls.map((tc, i) => (
                                    <span
                                      key={i}
                                      className="font-mono text-[10px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-cyan-400"
                                    >
                                      {tc.tool_name} ({tc.duration_ms}ms)
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Human-in-the-Loop Feedback Buttons */}
                            <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                              <span>Investigator Assessment:</span>
                              <div className="flex items-center gap-1.5">
                                <button
                                  onClick={() => handleFeedback(m.message_id, 'Correct')}
                                  className="px-2 py-1 rounded bg-slate-900 hover:bg-emerald-500/20 hover:text-emerald-400 border border-slate-800 text-[10px] font-semibold transition-colors"
                                >
                                  Correct
                                </button>
                                <button
                                  onClick={() => handleFeedback(m.message_id, 'False Positive')}
                                  className="px-2 py-1 rounded bg-slate-900 hover:bg-amber-500/20 hover:text-amber-400 border border-slate-800 text-[10px] font-semibold transition-colors"
                                >
                                  False Positive
                                </button>
                                <button
                                  onClick={() => handleFeedback(m.message_id, 'Incorrect')}
                                  className="px-2 py-1 rounded bg-slate-900 hover:bg-rose-500/20 hover:text-rose-400 border border-slate-800 text-[10px] font-semibold transition-colors"
                                >
                                  Incorrect
                                </button>
                                <button
                                  onClick={() => handleFeedback(m.message_id, 'Needs Review')}
                                  className="px-2 py-1 rounded bg-slate-900 hover:bg-purple-500/20 hover:text-purple-400 border border-slate-800 text-[10px] font-semibold transition-colors"
                                >
                                  Needs Review
                                </button>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })
              )}

              {loading && (
                <div className="flex gap-3 text-xs items-center text-slate-400">
                  <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0 animate-pulse">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                    <span>Retrieving authorized evidence & synthesizing grounded analysis...</span>
                  </div>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Input Bar */}
            <div className="p-4 bg-slate-950 border-t border-slate-800">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleAsk();
                }}
                className="flex items-center gap-3"
              >
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask an investigative question (e.g. 'Why is this account suspicious?', 'Where did T102 go?')..."
                  className="flex-1 px-4 py-3 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors shadow-inner"
                />
                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="px-5 py-3 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-xl text-xs flex items-center gap-2 shadow-lg shadow-emerald-500/20 disabled:opacity-50 transition-all shrink-0"
                >
                  <span>Inquire</span>
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
