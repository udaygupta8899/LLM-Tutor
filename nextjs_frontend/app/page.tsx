"use client";
import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import Mermaid from './Mermaid';
import { generateQuizPDFReport } from './pdfGenerator';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  metadata?: {
    complexity?: string;
    routing_strategy?: string;
    security_status?: string;
    latency_seconds?: number;
    retrieved_documents?: any[];
  };
}

interface QuizQuestion {
  id: number;
  difficulty?: string;
  question: string;
  options: string[];
  correct_option: string;
  explanation: string;
}

interface QuizAnswerRecord {
  id: number;
  difficulty?: string;
  question: string;
  selectedOption: string;
  correctOption: string;
  isCorrect: boolean;
  explanation: string;
}

function cleanLatexDelimiters(text: string): string {
  if (!text) return "";
  let cleaned = text.replace(/\\\[([\s\S]*?)\\\]/g, '$$$$$1$$$$');
  cleaned = cleaned.replace(/\\\(([\s\S]*?)\\\)/g, '$$$1$$');
  return cleaned;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LLMTutorPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [tutorMode, setTutorMode] = useState<'explain' | 'hint' | 'quiz' | 'socratic'>('explain');
  const [threadId, setThreadId] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [latestMetadata, setLatestMetadata] = useState<any>(null);
  
  // Interactive Adaptive Quiz State
  const [showQuizModal, setShowQuizModal] = useState(false);
  const [quizTopic, setQuizTopic] = useState('Transformer Attention & Self-RAG');
  const [totalRequestedQuestions, setTotalRequestedQuestions] = useState(3);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [currentDifficulty, setCurrentDifficulty] = useState<'easy' | 'intermediate' | 'advanced'>('easy');
  const [currentQuestion, setCurrentQuestion] = useState<QuizQuestion | null>(null);
  const [isFetchingQuestion, setIsFetchingQuestion] = useState(false);
  const [isQuizActive, setIsQuizActive] = useState(false);
  
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [score, setScore] = useState(0);
  const [isAnswerSubmitted, setIsAnswerSubmitted] = useState(false);
  const [quizAnswerHistory, setQuizAnswerHistory] = useState<QuizAnswerRecord[]>([]);
  const [completedQuizSummary, setCompletedQuizSummary] = useState<{ topic: string; score: number; total: number; results: QuizAnswerRecord[] } | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setThreadId(crypto.randomUUID());
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentQuestion, completedQuizSummary]);

  const handleModeChange = (mode: 'explain' | 'hint' | 'quiz' | 'socratic') => {
    if (isQuizActive) return; // Mode switcher locked during quiz
    setTutorMode(mode);
    if (mode === 'quiz') {
      setShowQuizModal(true);
    }
  };

  const fetchNextDynamicQuestion = async (
    qNum: number,
    difficulty: 'easy' | 'intermediate' | 'advanced',
    prevQuestionsList: string[]
  ) => {
    setIsFetchingQuestion(true);
    try {
      const res = await fetch(`${API_BASE}/api/quiz/single-question`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: quizTopic.trim(),
          question_number: qNum,
          difficulty: difficulty,
          previous_questions: prevQuestionsList,
          api_key: apiKey.trim() || undefined
        })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to generate dynamic question from LLM.");
      }
      setCurrentQuestion(data);
      setSelectedOption(null);
      setIsAnswerSubmitted(false);
    } catch (err: any) {
      console.error(err);
      alert(err.message || "Failed to generate dynamic question. Please ensure your API key is provided.");
      setIsQuizActive(false);
    } finally {
      setIsFetchingQuestion(false);
    }
  };

  const handleStartQuiz = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quizTopic.trim() || isFetchingQuestion) return;

    setShowQuizModal(false);
    setIsQuizActive(true);
    setScore(0);
    setCurrentQuestionIndex(1);
    setCurrentDifficulty('easy');
    setQuizAnswerHistory([]);
    setCompletedQuizSummary(null);

    await fetchNextDynamicQuestion(1, 'easy', []);
  };

  const handleOptionSelect = (optionLetter: string) => {
    if (isAnswerSubmitted || !currentQuestion) return;
    setSelectedOption(optionLetter);
    setIsAnswerSubmitted(true);

    const isCorrect = optionLetter === currentQuestion.correct_option;
    if (isCorrect) {
      setScore(prev => prev + 1);
    }

    setQuizAnswerHistory(prev => [
      ...prev,
      {
        id: currentQuestion.id,
        difficulty: currentDifficulty,
        question: currentQuestion.question,
        selectedOption: optionLetter,
        correctOption: currentQuestion.correct_option,
        isCorrect: isCorrect,
        explanation: currentQuestion.explanation
      }
    ]);
  };

  const handleNextQuestion = async () => {
    if (!currentQuestion) return;

    if (currentQuestionIndex < totalRequestedQuestions) {
      const nextQNum = currentQuestionIndex + 1;
      // Adaptive Difficulty Progression:
      // If student answered correctly -> increase difficulty; otherwise stay or consolidate
      const wasCorrect = selectedOption === currentQuestion.correct_option;
      let nextDiff: 'easy' | 'intermediate' | 'advanced' = currentDifficulty;
      if (wasCorrect) {
        if (currentDifficulty === 'easy') nextDiff = 'intermediate';
        else if (currentDifficulty === 'intermediate') nextDiff = 'advanced';
      } else {
        if (currentDifficulty === 'advanced') nextDiff = 'intermediate';
      }

      setCurrentDifficulty(nextDiff);
      setCurrentQuestionIndex(nextQNum);

      const prevList = quizAnswerHistory.map(h => h.question);
      prevList.push(currentQuestion.question);

      await fetchNextDynamicQuestion(nextQNum, nextDiff, prevList);
    } else {
      // Quiz complete - finish session and unlock mode switcher
      const finalScore = score; // Already accurately incremented in handleOptionSelect
      const summary = {
        topic: quizTopic,
        score: finalScore,
        total: totalRequestedQuestions,
        results: quizAnswerHistory
      };
      setCompletedQuizSummary(summary);
      setIsQuizActive(false);
      setCurrentQuestion(null);
      setTutorMode('explain'); // Restore default mode
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);

    try {
      // Build sliding window conversational memory from recent messages
      const recentHistory = messages.slice(-4).map(m => 
        `${m.role === 'user' ? 'Student' : 'Tutor'}: ${m.content.slice(0, 300)}`
      ).join('\n\n');

      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question: currentInput, 
          thread_id: threadId,
          tutor_mode: tutorMode,
          chat_history: recentHistory,
          api_key: apiKey.trim() || undefined
        }),
      });

      if (!response.ok) throw new Error("Backend connection failed");
      const data = await response.json();
      
      const assistantMsg: Message = {
        role: 'assistant',
        content: data.answer,
        metadata: {
          complexity: data.complexity,
          routing_strategy: data.routing_strategy,
          security_status: data.security_status,
          latency_seconds: data.latency_seconds,
          retrieved_documents: data.retrieved_documents
        }
      };

      setMessages(prev => [...prev, assistantMsg]);
      setLatestMetadata(data);
    } catch (err: any) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `**⚠️ Error:** Could not connect to LLM Tutor API (${API_BASE}). Please ensure backend is running.` 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex flex-col h-screen bg-[#111827] text-[#f3f4f6]">
      {/* Top Header */}
      <header className="px-6 py-3.5 flex justify-between items-center border-b border-gray-800 bg-[#1f2937]/90 backdrop-blur">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow">
            🎓
          </div>
          <div>
            <div className="font-bold text-base text-white flex items-center gap-2">
              LLM Tutor
              <span className="text-[10px] bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded-full font-mono">
                Groq GPT-OSS-120B + Custom BM25/RRF
              </span>
            </div>
            <p className="text-[11px] text-gray-400">Adaptive Agentic RAG • Course Slides & Foundational Research Papers</p>
          </div>
        </div>

        {/* Mode Selector & API Key */}
        <div className="flex items-center space-x-3 text-xs">
          <input
            type="password"
            placeholder="Groq API Key (gsk_...)"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-indigo-300 placeholder-gray-500 focus:outline-none focus:border-indigo-500 w-48"
          />

          {/* Mode Selector is hidden / locked while Quiz is Active */}
          {!isQuizActive ? (
            <div className="flex items-center space-x-1">
              <span className="text-gray-400 mr-1">Mode:</span>
              {(['explain', 'hint', 'quiz', 'socratic'] as const).map(mode => (
                <button
                  key={mode}
                  onClick={() => handleModeChange(mode)}
                  className={`px-3 py-1 rounded-md capitalize font-medium transition ${
                    tutorMode === mode
                      ? 'bg-indigo-600 text-white shadow'
                      : 'bg-gray-800 text-gray-400 hover:text-white'
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-2 bg-indigo-950/80 border border-indigo-500/40 px-3 py-1.5 rounded-lg text-indigo-300 font-mono text-xs">
              <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping"></span>
              <span>Quiz In Progress (Question {currentQuestionIndex}/{totalRequestedQuestions})</span>
            </div>
          )}
        </div>
      </header>

      {/* Main Split Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat & Quiz Stream Area */}
        <div className="flex-1 flex flex-col h-full overflow-y-auto">
          <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
            
            {/* Active Interactive Dynamic Quiz Card */}
            {isQuizActive && currentQuestion && (
              <div className="max-w-3xl mx-auto bg-slate-900 border border-indigo-500/50 rounded-2xl p-6 shadow-2xl space-y-5 animate-in fade-in duration-300">
                <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono uppercase bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full font-semibold border border-indigo-500/30">
                        Adaptive Quiz
                      </span>
                      <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full font-semibold border ${
                        currentDifficulty === 'easy' ? 'bg-sky-950 text-sky-300 border-sky-800' :
                        (currentDifficulty === 'intermediate' ? 'bg-amber-950 text-amber-300 border-amber-800' : 'bg-purple-950 text-purple-300 border-purple-800')
                      }`}>
                        Level: {currentDifficulty.toUpperCase()}
                      </span>
                    </div>
                    <h3 className="text-lg font-bold text-white mt-1.5">{quizTopic}</h3>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400">Question</span>
                    <div className="text-base font-bold text-indigo-400">
                      {currentQuestionIndex} / {totalRequestedQuestions}
                    </div>
                  </div>
                </div>

                {isFetchingQuestion ? (
                  <div className="py-10 text-center text-slate-400 animate-pulse text-sm font-mono">
                    ⚡ LLM synthesizing next adaptive question based on mastery...
                  </div>
                ) : (
                  <>
                    {/* Current Question */}
                    <div className="text-base font-medium text-slate-100 leading-relaxed">
                      {currentQuestion.question}
                    </div>

                    {/* Interactive Clickable Options */}
                    <div className="space-y-3 pt-1">
                      {currentQuestion.options.map((opt, oIdx) => {
                        const optLetter = opt.trim().charAt(0);
                        const isSelected = selectedOption === optLetter;
                        const isCorrect = optLetter === currentQuestion.correct_option;
                        
                        let btnStyle = "bg-slate-800/80 hover:bg-slate-800 border-slate-700 text-slate-200";
                        if (isAnswerSubmitted) {
                          if (isCorrect) {
                            btnStyle = "bg-emerald-950/80 border-emerald-500 text-emerald-200 ring-1 ring-emerald-500 font-semibold";
                          } else if (isSelected && !isCorrect) {
                            btnStyle = "bg-rose-950/80 border-rose-500 text-rose-200 ring-1 ring-rose-500";
                          } else {
                            btnStyle = "bg-slate-800/40 border-slate-800 text-slate-500 opacity-60";
                          }
                        }

                        return (
                          <button
                            key={oIdx}
                            disabled={isAnswerSubmitted}
                            onClick={() => handleOptionSelect(optLetter)}
                            className={`w-full text-left p-4 rounded-xl border text-sm transition-all flex items-start gap-3 ${btnStyle}`}
                          >
                            <span className="font-bold shrink-0">{optLetter}.</span>
                            <span>{opt.replace(/^[A-D]\.\s*/, '')}</span>
                          </button>
                        );
                      })}
                    </div>

                    {/* Feedback & In-Depth Explanation */}
                    {isAnswerSubmitted && (
                      <div className={`p-4 rounded-xl border text-sm space-y-2 animate-in fade-in ${
                        selectedOption === currentQuestion.correct_option
                          ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-100'
                          : 'bg-rose-950/40 border-rose-800/80 text-rose-100'
                      }`}>
                        <div className="flex items-center gap-2 font-bold text-sm">
                          {selectedOption === currentQuestion.correct_option ? (
                            <span className="text-emerald-400">✅ Correct Answer! (Level Promoted)</span>
                          ) : (
                            <span className="text-rose-400">
                              ❌ Incorrect. (Correct choice: {currentQuestion.correct_option})
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed pt-1">
                          <strong>Explanation:</strong> {currentQuestion.explanation}
                        </p>

                        <div className="pt-3 flex justify-end">
                          <button
                            onClick={handleNextQuestion}
                            className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-lg text-xs flex items-center gap-1.5 transition shadow"
                          >
                            <span>{currentQuestionIndex < totalRequestedQuestions ? "Next Question →" : "View Final Assessment Report →"}</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* Quiz Results Summary & PDF Download Banner */}
            {completedQuizSummary && (
              <div className="max-w-3xl mx-auto bg-slate-900 border border-emerald-500/50 rounded-2xl p-6 shadow-2xl space-y-4 animate-in fade-in">
                <div className="flex justify-between items-start border-b border-slate-800 pb-4">
                  <div>
                    <span className="text-xs font-mono uppercase bg-emerald-500/20 text-emerald-300 px-2.5 py-1 rounded-full font-semibold">
                      Assessment Completed
                    </span>
                    <h3 className="text-xl font-bold text-white mt-2">{completedQuizSummary.topic}</h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Completed {completedQuizSummary.total} Questions • Final Score: <span className="font-bold text-emerald-400">{completedQuizSummary.score} / {completedQuizSummary.total}</span> ({Math.round((completedQuizSummary.score / completedQuizSummary.total) * 100)}%)
                    </p>
                  </div>
                  <button
                    onClick={() => generateQuizPDFReport({
                      topic: completedQuizSummary.topic,
                      totalQuestions: completedQuizSummary.total,
                      score: completedQuizSummary.score,
                      results: completedQuizSummary.results
                    })}
                    className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl text-xs flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition transform hover:scale-[1.02]"
                  >
                    <span>📄 Download Full PDF Report</span>
                  </button>
                </div>

                {/* Strengths & Weaknesses Quick Overview */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs pt-1">
                  <div className="p-3.5 bg-emerald-950/30 border border-emerald-800/60 rounded-xl space-y-1">
                    <span className="font-bold text-emerald-400">💪 Strong Areas:</span>
                    <p className="text-slate-300 leading-relaxed">
                      {completedQuizSummary.score > 0 
                        ? `Demonstrated clear command over foundational principles and question mechanics on ${completedQuizSummary.score} concept(s).`
                        : "Focus on revisiting foundational lecture slides to establish core terminology."}
                    </p>
                  </div>

                  <div className="p-3.5 bg-rose-950/30 border border-rose-800/60 rounded-xl space-y-1">
                    <span className="font-bold text-rose-400">🎯 Areas to Review:</span>
                    <p className="text-slate-300 leading-relaxed">
                      {completedQuizSummary.total - completedQuizSummary.score > 0
                        ? `Targeted review advised for ${completedQuizSummary.total - completedQuizSummary.score} concept(s). Check the downloadable PDF for complete technical explanations.`
                        : "Flawless score! Ready to advance to multi-hop architectural reasoning."}
                    </p>
                  </div>
                </div>

                <div className="pt-2 flex justify-between items-center text-xs text-slate-500">
                  <span>Report includes full itemized breakdown and source references</span>
                  <button 
                    onClick={() => setCompletedQuizSummary(null)}
                    className="text-indigo-400 hover:underline"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            )}

            {/* Standard Welcome Screen */}
            {messages.length === 0 && !isQuizActive && !completedQuizSummary && (
              <div className="h-[65vh] flex flex-col items-center justify-center text-center space-y-4 max-w-lg mx-auto">
                <div className="w-14 h-14 rounded-2xl bg-indigo-600/20 border border-indigo-500 flex items-center justify-center text-3xl">
                  📖
                </div>
                <h2 className="text-2xl font-bold text-white">How can I assist your LLM studies today?</h2>
                <p className="text-sm text-gray-400">
                  Grounded in foundational research papers (*Attention Is All You Need*, *RAG (Lewis 2020)*, *Self-RAG (Asai 2024)*, *Agentic RAG Survey (Singh 2026)*) and course materials.
                </p>
                <div className="flex flex-wrap gap-2 justify-center pt-2">
                  <button 
                    onClick={() => setInput("How does multi-head self-attention work in the Transformer architecture?")}
                    className="text-xs bg-gray-800 hover:bg-gray-700 text-indigo-300 px-3 py-1.5 rounded-lg border border-gray-700 transition"
                  >
                    Multi-Head Self-Attention
                  </button>
                  <button 
                    onClick={() => handleModeChange('quiz')}
                    className="text-xs bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-200 px-3 py-1.5 rounded-lg border border-indigo-500/50 transition font-semibold"
                  >
                    🎯 Take Interactive Quiz
                  </button>
                  <button 
                    onClick={() => setInput("Compare single-step RAG with Self-RAG reflection tokens and dynamic retrieval.")}
                    className="text-xs bg-gray-800 hover:bg-gray-700 text-indigo-300 px-3 py-1.5 rounded-lg border border-gray-700 transition"
                  >
                    Self-RAG vs Standard RAG
                  </button>
                </div>
              </div>
            )}

            {/* Messages */}
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[90%] md:max-w-[80%] p-4 rounded-2xl shadow-sm ${
                  m.role === 'user' 
                  ? 'bg-indigo-600 text-white rounded-br-sm' 
                  : 'bg-[#1f2937] border border-gray-700 text-gray-200 rounded-bl-sm'
                }`}>
                  <div className="markdown-content text-sm text-gray-200">
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm, remarkMath]}
                      rehypePlugins={[rehypeKatex]}
                      components={{
                        code({ node, className, children, ...props }: any) {
                          const match = /language-(\w+)/.exec(className || '');
                          const isMermaid = match && match[1] === 'mermaid';
                          const content = String(children).replace(/\n$/, '');

                          if (isMermaid) {
                            return <Mermaid chart={content} />;
                          }

                          return (
                            <code className={className} {...props}>
                              {children}
                            </code>
                          );
                        }
                      }}
                    >
                      {cleanLatexDelimiters(m.content)}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="p-4 rounded-2xl bg-[#1f2937] border border-gray-700 text-sm text-gray-400 animate-pulse font-mono flex items-center gap-2">
                  <span>⚡ Agentic LLM Tutor reasoning across course evidence...</span>
                </div>
              </div>
            )}
            <div ref={scrollRef} />
          </div>

          {/* Chat Input Bar */}
          <footer className="p-4 bg-[#111827] border-t border-gray-800">
            <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative group">
              <textarea
                rows={1}
                disabled={isQuizActive}
                className="w-full bg-[#1f2937] border border-gray-700 rounded-xl py-3.5 pl-4 pr-14 text-sm text-white focus:outline-none focus:border-indigo-500 resize-none transition-all placeholder-gray-500 disabled:opacity-40"
                placeholder={isQuizActive ? "Quiz in progress. Select options above..." : "Ask about attention mechanisms, RAG, prompt injection, or test security..."}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />
              <button 
                type="submit"
                className="absolute right-3 bottom-2.5 p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 transition disabled:opacity-50"
                disabled={isLoading || !input.trim() || isQuizActive}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M7 11L12 6L17 11M12 18V7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"></path>
                </svg>
              </button>
            </form>
          </footer>
        </div>

        {/* Right Telemetry & Grounding Inspector */}
        <aside className="w-80 border-l border-gray-800 bg-[#1f2937]/50 p-4 overflow-y-auto hidden lg:flex flex-col space-y-4 text-xs">
          <h3 className="font-bold text-gray-200 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
            🔍 RAG & Security Telemetry
          </h3>

          <div className="bg-[#1f2937] border border-gray-700 rounded-xl p-3 space-y-2.5">
            <div className="flex justify-between">
              <span className="text-gray-400">Security Gate:</span>
              <span className="font-semibold text-emerald-400">
                {latestMetadata?.security_status || 'IDLE'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Complexity:</span>
              <span className="font-mono text-indigo-300 font-semibold">
                {latestMetadata?.complexity?.toUpperCase() || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Strategy:</span>
              <span className="font-mono text-amber-300 font-semibold">
                {latestMetadata?.routing_strategy || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Latency:</span>
              <span className="font-mono text-gray-200">
                {latestMetadata ? `${latestMetadata.latency_seconds}s` : '0.00s'}
              </span>
            </div>
          </div>

          <h4 className="font-bold text-gray-300 uppercase tracking-wider text-[10px] pt-2">
            Retrieved Evidence Chunks ({latestMetadata?.retrieved_documents?.length || 0})
          </h4>

          <div className="space-y-2 flex-1 overflow-y-auto">
            {(!latestMetadata?.retrieved_documents || latestMetadata.retrieved_documents.length === 0) ? (
              <p className="text-gray-500 italic">No retrieval required or executed yet.</p>
            ) : (
              latestMetadata.retrieved_documents.map((doc: any, idx: number) => (
                <div key={idx} className="p-2.5 bg-[#1f2937] border border-gray-700/80 rounded-lg space-y-1">
                  <div className="flex justify-between font-semibold text-indigo-300 text-[10px]">
                    <span className="truncate max-w-[150px]">{doc.metadata?.source || 'Document'}</span>
                    <span>p. {doc.metadata?.page || 'N/A'}</span>
                  </div>
                  <p className="text-gray-300 line-clamp-3 text-[11px] leading-relaxed">
                    {doc.text}
                  </p>
                </div>
              ))
            )}
          </div>
        </aside>
      </div>

      {/* QUIZ CONFIGURATION MODAL POPUP */}
      {showQuizModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center pb-3 border-b border-slate-800">
              <h3 className="font-bold text-lg text-white flex items-center gap-2">
                <span>🎯 Start Interactive Adaptive Quiz</span>
              </h3>
              <button 
                onClick={() => setShowQuizModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleStartQuiz} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Quiz Topic
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Transformer Attention, Self-RAG, BM25"
                  value={quizTopic}
                  onChange={(e) => setQuizTopic(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Number of Questions
                </label>
                <input
                  type="number"
                  min={1}
                  max={10}
                  required
                  placeholder="e.g. 3, 5, 10"
                  value={totalRequestedQuestions}
                  onChange={(e) => setTotalRequestedQuestions(Math.max(1, Math.min(10, Number(e.target.value) || 1)))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
                <span className="text-[10px] text-slate-500 mt-1 block">Questions adjust in difficulty dynamically (Easy → Intermediate → Advanced)</span>
              </div>

              <div className="pt-2 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowQuizModal(false)}
                  className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isFetchingQuestion || !quizTopic.trim()}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition disabled:opacity-50 shadow-lg shadow-indigo-600/30"
                >
                  {isFetchingQuestion ? (
                    <span>Synthesizing Questions...</span>
                  ) : (
                    <span>Launch Adaptive Quiz →</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </main>
  );
}
