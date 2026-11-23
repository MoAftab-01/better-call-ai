import { ArrowUp, MessageSquare, Scale, Trash2 } from 'lucide-react'
import { ReadAloud, VoiceInput } from './BrowserVoice'
import { useEffect, useRef, useState } from 'react'
import { apiUrl } from '../api'
import { sendDemoQuestion, sendQuestion, type Answer, type ChatStatus, type Message } from '../chat'

const starters = [
  { label: 'BNS commencement', question: 'What does the BNS commencement notification state?' },
  { label: 'BNSS First Schedule', question: 'What does the BNSS commencement notification say about the First Schedule entry relating to BNS section 106(2)?' },
  { label: 'BSA notification', question: 'What is stated in the BSA commencement notification?' },
  { label: 'BNS archival text 15', question: 'BNS section 15' },
  { label: 'BNSS archival text 25', question: 'BNSS section 25' },
  { label: 'BSA archival text 109', question: 'BSA section 109' },
]
export default function ConversationWorkspace({ connected, research, onSelect }: {
  connected: boolean
  research: { status: ChatStatus | null; error: boolean; retry: () => void }
  onSelect: (answer: Answer | null) => void
}) {
  const [demoAvailable, setDemoAvailable] = useState(false)
  const [demoMode, setDemoMode] = useState(false)
  const isDemo = demoAvailable && demoMode
  useEffect(() => {
    if (!connected) return
    let active = true
    let request: AbortController | null = null
    async function checkDemo() {
      if (request) return
      const abort = new AbortController(); request = abort
      const timer = window.setTimeout(() => abort.abort(), 5000)
      try {
        const response = await fetch(apiUrl('/api/demo/status'), { signal: abort.signal, cache: 'no-store' })
        const data = response.ok ? await response.json() : null
        if (active) setDemoAvailable(data?.enabled === true && data?.mode === 'synthetic_demo')
      } catch { if (active) setDemoAvailable(false) }
      finally { window.clearTimeout(timer); request = null }
    }
    void checkDemo()
    const interval = window.setInterval(() => void checkDemo(), 15000)
    return () => { active = false; window.clearInterval(interval); request?.abort() }
  }, [connected])
  const [draft, setDraft] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const { status, error: statusError, retry: retryStatus } = research
  const publicationPending = status?.research_state === 'publication_pending'
  const canResearch = connected && !statusError && !!status?.available
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [failedQuestion, setFailedQuestion] = useState('')
  const [accessToken, setAccessToken] = useState('')
  const [voiceEpoch, setVoiceEpoch] = useState(0)
  const conversation = useRef<string | null>(null)
  const controller = useRef<AbortController | null>(null)
  const sending = useRef(false)
  const sequence = useRef(0)
  const input = useRef<HTMLTextAreaElement>(null)
  const end = useRef<HTMLDivElement>(null)
  useEffect(() => { end.current?.scrollIntoView({ block: 'nearest' }) }, [messages, busy])
  useEffect(() => () => { controller.current?.abort() }, [])
  async function submit(question = draft, retry = false) {
    const text = question.trim()
    if (!text || sending.current || !connected || (!isDemo && !canResearch)) return
    sending.current = true
    setBusy(true); setError(''); setFailedQuestion(''); setDraft('')
    const serial = ++sequence.current
    const abort = new AbortController(); controller.current = abort
    const timer = window.setTimeout(() => abort.abort(), 30000)
    if (!retry) setMessages(old => [...old, { id: crypto.randomUUID(), role: 'user' as const, content: text }].slice(-40))
    try {
      if (isDemo) {
        const demo = await sendDemoQuestion(text, abort.signal)
        if (sequence.current !== serial) return
        setMessages(old => [...old, { id: crypto.randomUUID(), role: 'assistant' as const, content: demo.answer, demo }].slice(-40))
        onSelect(null)
        return
      }
      const result = await sendQuestion(text, conversation.current, messages, abort.signal, accessToken)
      if (sequence.current !== serial) return
      conversation.current = result.conversation_id
      setMessages(old => [...old, { id: crypto.randomUUID(), role: 'assistant' as const, content: result.answer, result }].slice(-40))
      onSelect(result)
    } catch (e) {
      if (sequence.current !== serial) return
      setFailedQuestion(text)
      setError(abort.signal.aborted ? 'The request timed out. You can retry.' : e instanceof Error ? e.message : 'Connection failed. Please retry.')
    } finally {
      window.clearTimeout(timer)
      if (sequence.current === serial) { sending.current = false; setBusy(false) }
    }
  }
  function clear() {
    setVoiceEpoch(n => n + 1)
    sequence.current++; controller.current?.abort(); sending.current = false
    setBusy(false); setMessages([]); setDraft(''); setError(''); setFailedQuestion('')
    conversation.current = null; onSelect(null); input.current?.focus()
  }
  const unavailable = !connected ? 'Backend disconnected. Use Retry in the connection indicator.'
    : isDemo ? '' : statusError ? 'Chat service unavailable. Refresh the backend connection to retry.'
      : !status ? 'Checking research availability...' : !status.available ? status.research_message : ''
  return (
    <section className="conversation-panel" id="workspace" aria-labelledby="conversation-title" tabIndex={-1}>
      <header className="panel-header">
        <div className="panel-title"><MessageSquare size={17} aria-hidden="true" /><h2 id="conversation-title">Your conversation</h2></div>
        <button className="clear-chat" type="button" onClick={clear} aria-label="Clear conversation"><Trash2 size={14} />Clear</button>
      </header>
      {demoAvailable && <div className="demo-notice">
        <button type="button" className="source-select" aria-pressed={isDemo} onClick={() => { clear(); setDemoMode(!isDemo) }}>
          {isDemo ? 'Return to legal research (publication gated)' : 'Try synthetic demo'}
        </button>
        {isDemo && <p role="status"><strong>Demo mode — synthetic examples</strong><br />Fictional exercises only. No verified Indian legal advice, official citations or private evidence. Real research remains publication gated.</p>}
      </div>}
      {!messages.length && <div className="conversation-empty">
        <div className="empty-emblem" aria-hidden="true"><Scale size={29} strokeWidth={1.4} /></div>
        <p className="section-kicker">RESEARCH WITH THE SOURCE IN VIEW</p>
        <h3>{isDemo ? 'Explore a fictional scenario.' : publicationPending ? 'Research is not available yet.' : canResearch ? 'Ask what the document says.' : 'Checking research availability.'}</h3>
        <p>{isDemo ? 'Try a fictional rent receipt, parcel or document timeline exercise. Replies are fixed synthetic examples; optional AI only selects an example. This does not answer real legal questions.' : publicationPending ? 'Official-source publication must be authorized before this website can provide legal answers or citations. You may prepare a draft; nothing can be submitted while research is unavailable.'
          : canResearch ? 'Explore conservative selections from original BNS, BNSS and BSA Acts and commencement notifications. Coverage depends on the authorized corpus. Answers quote unreviewed archival text, not your current legal rights.'
            : 'The workspace is available. Source suggestions and research become available only when the backend confirms source access.'}</p>
        {isDemo && <div className="starter-list">{['Fictional rent receipt exercise', 'Fictional parcel exercise', 'Fictional document timeline'].map(question => <button key={question} type="button" className="starter-button" onClick={() => { setDraft(question); input.current?.focus() }}>{question}</button>)}</div>}
        {canResearch && !isDemo && <div className="starter-area"><p>Start with an available source.</p><div className="starter-list">
          {starters.map(s => <button className="starter-button" type="button" key={s.label} onClick={() => { setDraft(s.question); input.current?.focus() }}>{s.label}</button>)}
        </div></div>}
      </div>}
      {!!messages.length && <div className="message-list" role="log" aria-label="Conversation messages" aria-live="polite" aria-busy={busy}>
        {messages.map(m => <article key={m.id} className={'chat-message ' + m.role}>
          <strong>{m.role === 'user' ? 'You' : 'Better Call AI'}</strong>
          {m.result && <span className="evidence-badge">{m.result.evidence_status.replaceAll('_', ' ')}</span>}
          {m.demo && <span className="evidence-badge">SYNTHETIC DEMO · NOT LEGAL EVIDENCE</span>}
          <p>{m.content}</p>
          {m.demo && <><p className="answer-mode">{m.demo.provider_status === 'selected' ? 'AI-selected synthetic example' : m.demo.provider_status === 'fallback' ? 'Provider unavailable or invalid selection; deterministic sample' : 'Deterministic synthetic sample'} · No official citations</p><ReadAloud text={m.content} /></>}
          {m.result && <>
            <p className="answer-mode">{m.result.provider.status === 'completed' ? 'Groq evidence selection' : 'Extractive source response'} · {m.result.retrieval_mode.toUpperCase()} · currentness unknown</p>
            <button type="button" className="source-select" onClick={() => onSelect(m.result!)}>View sources for this answer ({m.result.citations.length})</button>
            <ReadAloud text={m.content} />
            <details className="answer-warnings"><summary>Scope and uncertainty</summary><ul>{m.result.warnings.map(w => <li key={w}>{w}</li>)}</ul></details>
          </>}
        </article>)}
        <div ref={end} />
      </div>}
      {busy && <button className="source-select" type="button" onClick={() => { sequence.current++; controller.current?.abort(); sending.current = false; setBusy(false); setError('Request cancelled.'); setFailedQuestion('') }}>Cancel request</button>}
      {busy && <p className="chat-progress" role="status">{isDemo ? 'Preparing a synthetic example...' : 'Retrieving and checking source evidence...'}</p>}
      {error && <div className="chat-error" role="alert"><p>{error}</p>{failedQuestion && <button type="button" disabled={busy || !connected} onClick={() => void submit(failedQuestion, true)}>Retry question</button>}</div>}
      {statusError && connected && <button type="button" className="source-select" onClick={retryStatus}>Retry chat readiness</button>}
      <form className="composer" onSubmit={e => { e.preventDefault(); void submit() }} aria-label={isDemo ? "Synthetic demo question" : "Legal research question"}>
        {status?.authentication_required && canResearch && !isDemo && <label className="access-token">Private demo access token (memory only)<input type="password" autoComplete="off" value={accessToken} onChange={e => setAccessToken(e.target.value)} maxLength={256} /><span>Use a token supplied privately by the operator. Never enter your Groq API key.</span></label>}
        <div className="composer-label-row"><label htmlFor="legal-question">{isDemo ? 'Ask about a fictional demo scenario' : 'Ask an archival legal research question'}</label><span className="draft-label">ENGLISH</span></div>
        <div className="composer-input"><textarea ref={input} id="legal-question" name="question" value={draft} onChange={e => setDraft(e.target.value)} maxLength={2000} rows={3}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void submit() } }}
          placeholder={isDemo ? "Try: fictional rent receipt exercise" : "What does S.O. 850(E) say about commencement?"} aria-describedby="answer-availability draft-privacy" />
          <div className="composer-toolbar"><span className="character-count">{draft.length.toLocaleString('en-IN')} / 2,000</span><div className="composer-actions">
            <button className="send-button" type="submit" disabled={busy || !draft.trim() || !!unavailable} aria-label="Send question"><ArrowUp size={19} aria-hidden="true" /></button>
          </div></div>
        </div>
        <p className="composer-notice" id="answer-availability" role="status">{unavailable || (isDemo ? 'Fictional/synthetic examples only. No verified Indian legal advice.' : status?.answer_mode)}{status && !status.retrieval.passages && status.retrieval.corpus_kind !== 'public' && ' No local corpus is loaded; unsupported questions receive an insufficient-evidence response.'}</p>
        {status && status.retrieval.passages > 0 && <p className="answer-mode">{status.retrieval.passages} unapproved archival selections · {status.retrieval.mode.toUpperCase()} · limited coverage</p>}
        <p className="draft-privacy" id="draft-privacy">{isDemo ? 'Only your submitted question goes to the demo backend and optionally Groq to select a synthetic example. Avoid personal or confidential information. No research evidence is accessed. ' : publicationPending ? 'Drafts stay in this browser and cannot be submitted while publication is pending. ' : 'Submitted questions go to the backend and, when evidence is available and configured, Groq. '}{isDemo ? 'History stays in browser memory (40 messages); no demo history is sent. Clear or reload to remove it.' : 'History stays in browser memory (40 messages, six recent turns sent). Clear or reload to remove it.'}</p>
        <VoiceInput key={voiceEpoch} onText={setDraft} disabled={busy} />
      </form>
    </section>
  )
}
