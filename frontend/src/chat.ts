import { apiUrl } from './api'
export interface Citation {
  id: string; candidate_id: string; document_id: string; title: string; instrument: string
  source_url: string | null; issuing_authority: string | null; publication_date: string | null
  pdf_page: number; start_line: number; end_line: number; quote: string
  raw_sha256: string; processed_sha256: string | null; text_sha256: string
  publication_manifest_sha256?: string | null; publication_commentary?: string | null
  printed_number_unverified?: string | null; qa_flags?: string[]; context_text?: string
  context_text_sha256?: string; version_description?: string
}
export interface Answer {
  answer: string; conversation_id: string
  evidence_status: 'VERIFIED_REVIEWED' | 'ARCHIVAL_UNVERIFIED' | 'INSUFFICIENT_EVIDENCE'
  citations: Citation[]; provider: { status: string; generation_mode: string; model: string | null }
  warnings: string[]; legal_currentness: string; retrieval_mode: string
}
export interface ChatStatus {
  available: boolean; answer_mode: string; provider_configured: boolean
  authentication_required?: boolean
  research_state: 'available' | 'publication_pending' | 'unavailable'
  research_message: string
  retrieval: { passages: number; mode: string; detail: string; corpus_kind?: string }
}
export interface DemoAnswer {
  mode: 'synthetic_demo'; answer: string; disclaimer: string
  scenario_id: string | null; citations: never[]
  provider_status: 'deterministic' | 'selected' | 'fallback'
}
export async function sendDemoQuestion(message: string, signal: AbortSignal): Promise<DemoAnswer> {
  const response = await fetch(apiUrl('/api/demo/chat'), {
    method: 'POST', signal, headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ message }),
  })
  let data
  try { data = await response.json() } catch { throw new Error('The demo returned an unreadable response. Please retry.') }
  if (!response.ok) throw new Error(data?.error?.message || 'The demo request failed. Please retry.')
  if (data.mode !== 'synthetic_demo' || typeof data.answer !== 'string' || typeof data.disclaimer !== 'string' ||
      !Array.isArray(data.citations) || data.citations.length !== 0 ||
      !['deterministic', 'selected', 'fallback'].includes(data.provider_status)) {
    throw new Error('The backend returned an unexpected demo response.')
  }
  return data as DemoAnswer
}
export interface GeneralAnswer {
  mode: 'general_information'; answer: string; disclaimer: string; sources_verified: false
  citations: never[]; legal_currentness: 'unknown'; response_kind: 'generated' | 'safety_boundary'
  requires_professional_help: boolean
}
export interface GeneralTurn { role: 'user' | 'assistant'; content: string }
export async function sendGeneralQuestion(message: string, history: GeneralTurn[], signal: AbortSignal): Promise<GeneralAnswer> {
  const response = await fetch(apiUrl('/api/assistant/chat'), {
    method: 'POST', signal, headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ message, history: history.slice(-6).map(t => ({ role: t.role, content: t.content.slice(0, 1200) })) }),
  })
  let data
  try { data = await response.json() } catch { throw new Error('The AI Assistant returned an unreadable response. Try the synthetic demo.') }
  if (!response.ok) throw new Error(data?.error?.message || 'AI Assistant unavailable. Retry or choose the synthetic demo.')
  if (data.mode !== 'general_information' || data.sources_verified !== false || data.legal_currentness !== 'unknown' ||
      typeof data.answer !== 'string' || typeof data.disclaimer !== 'string' || !Array.isArray(data.citations) || data.citations.length ||
      !['generated', 'safety_boundary'].includes(data.response_kind) || typeof data.requires_professional_help !== 'boolean') {
    throw new Error('Unverified AI response failed validation. No answer was displayed.')
  }
  return data as GeneralAnswer
}
export interface Message { id: string; role: 'user' | 'assistant'; content: string; result?: Answer; demo?: DemoAnswer; general?: GeneralAnswer }
export function officialSource(url: string | null): string | undefined {
  if (!url) return undefined
  try {
    const parsed = new URL(url)
    if (parsed.protocol !== 'https:' || parsed.username || parsed.password) return undefined
    if (!parsed.hostname.endsWith('.gov.in') && !parsed.hostname.endsWith('.nic.in')) return undefined
    return parsed.href
  } catch { return undefined }
}
export async function sendQuestion(message: string, conversationId: string | null, messages: Message[], signal: AbortSignal, accessToken = ''): Promise<Answer> {
  const response = await fetch(apiUrl('/api/chat'), {
    method: 'POST', signal, headers: { 'Content-Type': 'application/json', Accept: 'application/json', ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}) },
    body: JSON.stringify({ message, conversation_id: conversationId,
      history: messages.slice(-6).map(m => ({ role: m.role, content: m.content.slice(0, 1200) })) }),
  })
  let data
  try { data = await response.json() } catch { throw new Error('The backend returned an unreadable response. Please retry.') }
  if (!response.ok) throw new Error(data?.error?.message || 'The request failed. Please retry.')
  if (typeof data.answer !== 'string' || typeof data.conversation_id !== 'string' || !Array.isArray(data.citations) || !Array.isArray(data.warnings) || !data.provider) {
    throw new Error('The backend returned an unexpected chat response.')
  }
  return data as Answer
}
