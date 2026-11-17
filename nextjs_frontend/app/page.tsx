"use client";
import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import Mermaid from './Mermaid';

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
  question: string;
  options: string[];
  correct_option: string;
  explanation: string;
}

function cleanLatexDelimiters(text: string): string {
  if (!text) return "";
  let cleaned = text.replace(/\\\[([\s\S]*?)\\\]/g, '$$$$$1$$$$');
  cleaned = cleaned.replace(/\\\(([\s\S]*?)\\\)/g, '$$$1$$');
  return cleaned;
}

export default function LLMTutorPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [tutorMode, setTutorMode] = useState<'explain' | 'hint' | 'quiz' | 'socratic'>('explain');
  const [threadId, setThreadId] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [latestMetadata, setLatestMetadata] = useState<any>(null);
  
  // Interactive Quiz Modal State
  const [showQuizModal, setShowQuizModal] = useState(false);
  const [quizTopic, setQuizTopic] = useState('Transformer Attention & RAG');
  const [quizNumQuestions, setQuizNumQuestions] = useState(3);
  const [isGeneratingQuiz, setIsGeneratingQuiz] = useState(false);
  const [activeQuiz, setActiveQuiz] = useState<{ topic: string; questions: QuizQuestion[] } | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [score, setScore] = useState(0);
  const [isAnswerSubmitted, setIsAnswerSubmitted] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setThreadId(crypto.randomUUID());
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeQuiz]);

  const handleModeChange = (mode: 'explain' | 'hint' | 'quiz' | 'socratic') => {
    setTutorMode(mode);
    if (mode === 'quiz') {
      setShowQuizModal(true);
    }
  };

  const handleStartQuiz = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quizTopic.trim() || isGeneratingQuiz) return;
    setIsGeneratingQuiz(true);

    try {
      const res = await fetch("http://localhost:8000/api/quiz/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: quizTopic.trim(),
          num_questions: Number(quizNumQuestions),
          api_key: apiKey.trim() || undefined
        })
      });
      const data = await res.json();
      if (data.questions && data.questions.length > 0) {
        setActiveQuiz({ topic: data.topic, questions: data.questions });
        setCurrentQuestionIndex(0);
        setSelectedOption(null);
        setIsAnswerSubmitted(false);
        setScore(0);
        setShowQuizModal(false);
      }
    } catch (err) {
      alert("Failed to generate quiz. Make sure backend is running.");
    } finally {
      setIsGeneratingQuiz(false);
    }
  };

  const handleOptionSelect = (optionLetter: string) => {
    if (isAnswerSubmitted) return;
    setSelectedOption(optionLetter);
    setIsAnswerSubmitted(true);

    const currentQ = activeQuiz?.questions[currentQuestionIndex];
    if (currentQ && optionLetter === currentQ.correct_option) {
      setScore(prev => prev + 1);
    }
  };

  const handleNextQuestion = () => {
    if (!activeQuiz) return;
    if (currentQuestionIndex + 1 < activeQuiz.questions.length) {
      setCurrentQuestionIndex(prev => prev + 1);
      setSelectedOption(null);
      setIsAnswerSubmitted(false);
    } else {
      // Quiz finished - record summary in chat
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `🎉 **Quiz Completed: ${activeQuiz.topic}**\n\n**Your Final Score:** \`${score + (selectedOption === activeQuiz.questions[currentQuestionIndex].correct_option ? 1 : 0)} / ${activeQuiz.questions.length}\`\n\nGreat job reviewing this topic! Click the **Quiz** mode button anytime to start another interactive challenge.`
        }
      ]);
      setActiveQuiz(null);
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
      const response = await fetch("http://localhost:8000/api/chat", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question: currentInput, 
          thread_id: threadId,
          tutor_mode: tutorMode,
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
        content: `**⚠️ Error:** Could not connect to LLM Tutor API (http://localhost:8000). Please ensure backend is running.` 
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
      </header>

      {/* Main Split Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat & Quiz Stream Area */}
        <div className="flex-1 flex flex-col h-full overflow-y-auto">
          <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
            
            {/* Active Interactive Quiz Card (When Quiz Mode Active) */}
            {activeQuiz && (
              <div className="max-w-3xl mx-auto bg-slate-900 border border-indigo-500/50 rounded-2xl p-6 shadow-2xl space-y-5 animate-in fade-in duration-300">
                <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                  <div>
                    <span className="text-xs font-mono uppercase bg-indigo-500/20 text-indigo-300 px-2.5 py-1 rounded-full font-semibold">
                      Interactive Quiz
                    </span>
                    <h3 className="text-lg font-bold text-white mt-1.5">{activeQuiz.topic}</h3>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400">Question</span>
                    <div className="text-sm font-bold text-indigo-400">
                      {currentQuestionIndex + 1} / {activeQuiz.questions.length}
                    </div>
                  </div>
                </div>

                {/* Current Question */}
                <div className="text-base font-medium text-slate-100 leading-relaxed">
                  {activeQuiz.questions[currentQuestionIndex].question}
                </div>

                {/* Interactive Clickable Options */}
                <div className="space-y-3 pt-1">
                  {activeQuiz.questions[currentQuestionIndex].options.map((opt, oIdx) => {
                    const optLetter = opt.trim().charAt(0);
                    const isSelected = selectedOption === optLetter;
                    const isCorrect = optLetter === activeQuiz.questions[currentQuestionIndex].correct_option;
                    
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

                {/* Feedback & Explanation Card (Revealed upon selection) */}
                {isAnswerSubmitted && (
                  <div className={`p-4 rounded-xl border text-sm space-y-2 animate-in fade-in ${
                    selectedOption === activeQuiz.questions[currentQuestionIndex].correct_option
                      ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-100'
                      : 'bg-rose-950/40 border-rose-800/80 text-rose-100'
                  }`}>
                    <div className="flex items-center gap-2 font-bold text-sm">
                      {selectedOption === activeQuiz.questions[currentQuestionIndex].correct_option ? (
                        <span className="text-emerald-400">✅ Correct Answer!</span>
                      ) : (
                        <span className="text-rose-400">
                          ❌ Incorrect. (Correct choice: {activeQuiz.questions[currentQuestionIndex].correct_option})
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed pt-1">
                      <strong>Explanation:</strong> {activeQuiz.questions[currentQuestionIndex].explanation}
                    </p>

                    <div className="pt-3 flex justify-end">
                      <button
                        onClick={handleNextQuestion}
                        className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-lg text-xs flex items-center gap-1.5 transition shadow"
                      >
                        <span>{currentQuestionIndex + 1 < activeQuiz.questions.length ? "Next Question →" : "Finish Quiz"}</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Standard Welcome Screen */}
            {messages.length === 0 && !activeQuiz && (
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
                className="w-full bg-[#1f2937] border border-gray-700 rounded-xl py-3.5 pl-4 pr-14 text-sm text-white focus:outline-none focus:border-indigo-500 resize-none transition-all placeholder-gray-500"
                placeholder="Ask about attention mechanisms, RAG, prompt injection, or test security..."
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
                disabled={isLoading || !input.trim()}
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
                <span>🎯 Start Interactive Quiz</span>
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
                  value={quizNumQuestions}
                  onChange={(e) => setQuizNumQuestions(Math.max(1, Math.min(10, Number(e.target.value) || 1)))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
                <span className="text-[10px] text-slate-500 mt-1 block">Type any number of questions between 1 and 10</span>
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
                  disabled={isGeneratingQuiz || !quizTopic.trim()}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition disabled:opacity-50 shadow-lg shadow-indigo-600/30"
                >
                  {isGeneratingQuiz ? (
                    <span>Generating Questions...</span>
                  ) : (
                    <span>Launch Quiz →</span>
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
