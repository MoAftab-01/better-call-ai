/** Explicit device-only text save. Never persist research results, tokens or citation metadata. */
export const CONVERSATION_KEY = 'better-call-ai.conversation.v1'
export type SavedMode = 'general_information' | 'synthetic_demo'
export interface SavedTurn { role: 'user' | 'assistant'; content: string }
export interface SavedConversation { version: 1; mode: SavedMode; savedAt: string; messages: SavedTurn[] }
interface TextMessage extends SavedTurn { result?: unknown }

export function parseConversation(raw: string): SavedConversation {
  if (raw.length > 250000) throw new Error('Saved conversation is too large.')
  const d = JSON.parse(raw)
  if (!d || typeof d !== 'object' || Object.keys(d).sort().join(',') !== 'messages,mode,savedAt,version' ||
      d.version !== 1 || !['general_information', 'synthetic_demo'].includes(d.mode) ||
      typeof d.savedAt !== 'string' || d.savedAt.length > 40 || !Number.isFinite(Date.parse(d.savedAt)) ||
      !Array.isArray(d.messages) || !d.messages.length || d.messages.length > 40 || d.messages.length % 2) {
    throw new Error('Saved conversation format is invalid.')
  }
  for (let i = 0; i < d.messages.length; i++) {
    const t = d.messages[i]
    if (!t || Object.keys(t).sort().join(',') !== 'content,role' ||
        t.role !== (i % 2 ? 'assistant' : 'user') || typeof t.content !== 'string' || !t.content.trim() ||
        t.content.length > (t.role === 'user' ? 2000 : 6000)) throw new Error('Saved messages are invalid.')
  }
  return d as SavedConversation
}
export function saveConversation(storage: Storage, mode: SavedMode, messages: TextMessage[]): SavedConversation {
  if (messages.some(m => m.result !== undefined)) throw new Error('Research evidence cannot be saved with these controls.')
  const saved = parseConversation(JSON.stringify({ version: 1, mode, savedAt: new Date().toISOString(),
    messages: messages.map(m => ({ role: m.role, content: m.content })) }))
  storage.setItem(CONVERSATION_KEY, JSON.stringify(saved))
  return saved
}
export function loadConversation(storage: Storage): SavedConversation | null {
  const value = storage.getItem(CONVERSATION_KEY)
  return value === null ? null : parseConversation(value)
}
export function deleteConversation(storage: Storage) { storage.removeItem(CONVERSATION_KEY) }
