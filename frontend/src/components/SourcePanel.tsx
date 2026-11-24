import { BookOpen, Phone } from 'lucide-react'
import { officialSource, type Answer } from '../chat'
import { useEffect, useState } from 'react'
import { apiUrl } from '../api'
export default function SourcePanel({ answer, publicationPending = false }: { answer: Answer | null; publicationPending?: boolean }) {
  const [references, setReferences] = useState<{ title: string; url: string; purpose: string; checked_at: string }[]>([])
  const [referenceState, setReferenceState] = useState('Loading checked reference links...')
  const [referenceAttempt, setReferenceAttempt] = useState(0)
  useEffect(() => {
    let active = true
    const abort = new AbortController()
    const timer = window.setTimeout(() => abort.abort(), 5000)
    async function load() {
      try {
        const r = await fetch(apiUrl('/api/references'), { signal: abort.signal })
        if (!r.ok) throw new Error('Unavailable')
        const d = await r.json()
        const expected = new Set(['https://indiacode.gov.in/', 'https://www.sci.gov.in/', 'https://nalsa.gov.in/'])
        if (d.sources_verified_for_answers !== false || d.used_in_ai_answers !== false || !Array.isArray(d.references) || d.references.length !== 3 ||
            new Set(d.references.map((x: { url: string }) => x.url)).size !== 3 ||
            !d.references.every((x: { title: string; url: string; purpose: string; checked_at: string }) =>
              expected.has(x.url) && typeof x.title === 'string' && typeof x.purpose === 'string' && Number.isFinite(Date.parse(x.checked_at)))) throw new Error('Invalid')
        if (active) { setReferences(d.references); setReferenceState('') }
      } catch { if (active) setReferenceState('Reference links are unavailable. Retry; no links have been invented.') }
      finally { window.clearTimeout(timer) }
    }
    void load()
    return () => { active = false; window.clearTimeout(timer); abort.abort() }
  }, [referenceAttempt])
  return <aside className="reference-column" aria-label="Sources and upcoming voice features">
    <section className="sources-panel" id="sources" aria-labelledby="sources-title" tabIndex={-1}>
      <header className="panel-header"><div className="panel-title"><BookOpen size={17} aria-hidden="true" /><h2 id="sources-title">Sources & citations</h2></div></header>
      <div className="sources-content">
        {!answer || publicationPending ? <><div className="source-emblem" aria-hidden="true"><BookOpen size={30} strokeWidth={1.3} /></div><h3>{publicationPending ? 'Sources are not available yet.' : 'Evidence beside the answer.'}</h3><p>{publicationPending ? 'Official-source publication is pending. This public workspace cannot provide legal citations until an authorized corpus is available.' : 'Ask a supported question, then select an answer to inspect its actual sources. No sources are selected yet.'}</p></>
          : !answer.citations.length ? <p>No adequate evidence was found for this answer. No citations are invented.</p>
            : answer.citations.map(c => <article className="citation-card" key={c.candidate_id}>
              <span className="evidence-badge">ARCHIVAL · UNREVIEWED</span>
              <h3>[{c.id}] {c.instrument || c.title}</h3><p>{c.title}</p>
              <p>{c.issuing_authority}<br />Publication: {c.publication_date || 'Unknown'}<br />Physical PDF page {c.pdf_page}, normalized lines {c.start_line}–{c.end_line}</p>
              {officialSource(c.source_url) && <a href={officialSource(c.source_url) + '#page=' + c.pdf_page} target="_blank" rel="noopener noreferrer">Open official source PDF</a>}
              <details><summary>Exact cited text</summary><blockquote>{c.quote}</blockquote></details>
              {c.printed_number_unverified && <p>Printed numeric start: {c.printed_number_unverified}. Document-only attribution; section boundaries are automated and not visually approved.</p>}
              {c.version_description && <p>{c.version_description}</p>}
              {c.publication_commentary && <p className="publication-commentary">{c.publication_commentary}</p>}
              {!!c.qa_flags?.length && <details><summary>Extraction quality warnings</summary><ul>{c.qa_flags.map(f => <li key={f}>{f.replaceAll('_', ' ')}</li>)}</ul><p>These warnings remain unresolved. Matching extracted text does not prove visual correctness.</p></details>}
              {c.context_text && <details><summary>Original surrounding context</summary><blockquote>{c.context_text}</blockquote><p>Context SHA-256: {c.context_text_sha256}</p></details>}
              <details><summary>Evidence binding</summary><dl><dt>Document</dt><dd>{c.document_id}</dd><dt>Source reference (not evidence approval)</dt><dd>{c.candidate_id}</dd><dt>Raw PDF SHA-256</dt><dd>{c.raw_sha256}</dd>{c.processed_sha256 && <><dt>Processed SHA-256</dt><dd>{c.processed_sha256}</dd></>}<dt>Exact text SHA-256</dt><dd>{c.text_sha256}</dd>{c.publication_manifest_sha256 && <><dt>Publication manifest SHA-256</dt><dd>{c.publication_manifest_sha256}</dd></>}</dl></details>
            </article>)}
        <p className="source-unavailable">Source identity does not prove legal correctness or current applicability. Existing proposals remain unapproved.</p>
      </div>
    </section>
    <section className="sources-panel official-references" aria-labelledby="official-references-title">
      <header className="panel-header"><h2 id="official-references-title">Official reference portals</h2></header>
      <div className="sources-content">
        <p>Checked navigation links, not citations for AI answers. The assistant has not read these sites. Portal availability does not verify a document or current law.</p>
        {references.map(r => <div className="reference-link" key={r.url}><a href={r.url} target="_blank" rel="noopener noreferrer">{r.title}</a><p>{r.purpose}<br />Link checked {r.checked_at.slice(0, 10)} (HTTPS 200).</p></div>)}
        {referenceState && <p role="status">{referenceState}</p>}
        {referenceState.includes('unavailable') && <button type="button" className="source-select" onClick={() => setReferenceAttempt(n => n + 1)}>Retry reference links</button>}
      </div>
    </section>
    <section className="voice-panel" aria-labelledby="voice-title"><div className="voice-panel-top"><span className="voice-icon"><Phone size={18} aria-hidden="true" /></span><span className="coming-soon">CALLS COMING SOON</span></div><h2 id="voice-title">A conversation, in your voice.</h2><p id="voice-availability">Optional browser dictation and read aloud are available where supported. Telephone calls are unavailable.</p><button className="voice-button" type="button" disabled aria-describedby="voice-availability"><Phone size={15} aria-hidden="true" />Start voice call</button></section>
  </aside>
}
