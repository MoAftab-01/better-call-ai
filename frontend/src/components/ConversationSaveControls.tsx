import { useState } from 'react'
import { deleteConversation, loadConversation, saveConversation, type SavedConversation, type SavedMode } from '../conversationStorage'
import type { Message } from '../chat'

export default function ConversationSaveControls({ mode, messages, busy, onRestore }: {
  mode: SavedMode | null; messages: Message[]; busy: boolean; onRestore: (saved: SavedConversation) => void
}) {
  const [notice, setNotice] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  function save() {
    if (!mode || !confirmed) return
    try {
      saveConversation(window.localStorage, mode, messages)
      setNotice('Saved on this browser only. Saving again replaces the previous saved copy.')
    } catch { setNotice('Could not save. Use complete alternating exchanges, or check browser storage permissions.') }
  }
  function restore() {
    try {
      const saved = loadConversation(window.localStorage)
      if (!saved) { setNotice('No saved conversation exists on this browser.'); return }
      onRestore(saved)
      setNotice('Restored local text, not verified evidence. Nothing was submitted. It becomes AI context only if you send a new question.')
    } catch { setNotice('Saved data is invalid or storage is unavailable. You can delete the saved copy and start again.') }
  }
  function remove() {
    try { deleteConversation(window.localStorage); setNotice('Saved copy deleted. Use Clear to remove the current conversation too.') }
    catch { setNotice('Browser storage is unavailable. Remove this site’s stored data in browser settings if needed.') }
  }
  return <section className="conversation-save" aria-label="Local conversation storage">
    <details><summary>Save or restore on this device</summary>
      <p>Optional, unencrypted browser storage on this browser profile and origin only. Do not save confidential details. One saved AI or synthetic conversation replaces the previous copy. Research evidence and access tokens are excluded. Restore replaces the current conversation and clears its draft. Clear removes the current chat; Delete saved copy removes the stored copy.</p>
      <label><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} />I understand this saves conversation text on this device.</label>
      <div className="save-actions">
        <button type="button" className="source-select" onClick={save} disabled={!confirmed || !mode || !messages.length || busy}>Save on this device</button>
        <button type="button" className="source-select" onClick={restore} disabled={busy}>Restore saved conversation</button>
        <button type="button" className="source-select" onClick={remove}>Delete saved copy</button>
      </div>
      <p role="status" aria-live="polite">{notice}</p>
    </details>
  </section>
}
