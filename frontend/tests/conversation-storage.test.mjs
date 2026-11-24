import test from 'node:test'
import assert from 'node:assert/strict'
import { CONVERSATION_KEY, parseConversation, saveConversation, loadConversation, deleteConversation } from '../src/conversationStorage.ts'
const messages=[{role:'user',content:'Explain mediation'},{role:'assistant',content:'Unverified general explanation.'}]
const raw=()=>({version:1,mode:'general_information',savedAt:'2026-11-24T10:00:00Z',messages:structuredClone(messages)})
function storage(){const values=new Map();return {getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)}}
test('explicit save/load/delete stores text only, with no credential or evidence metadata',()=>{
 const s=storage();assert.equal(loadConversation(s),null)
 const input=messages.map(m=>({...m,accessToken:'SYNTHETIC_DO_NOT_STORE',general:{sources_verified:false,citations:[]}}))
 saveConversation(s,'general_information',input)
 assert.deepEqual(loadConversation(s).messages,messages)
 assert(!s.getItem(CONVERSATION_KEY).includes('SYNTHETIC_DO_NOT_STORE'))
 assert(!s.getItem(CONVERSATION_KEY).includes('citations'))
 deleteConversation(s);assert.equal(loadConversation(s),null)
})
for(const [name,change] of [
 ['research mode',d=>d.mode='research'],['unknown version',d=>d.version=2],
 ['authority metadata',d=>d.sources_verified=true],['message evidence',d=>d.messages[1].citations=[]],
 ['system role',d=>d.messages[0].role='system'],['reordered roles',d=>d.messages.reverse()],
 ['partial exchange',d=>d.messages.pop()],['blank text',d=>d.messages[0].content=' '],
 ['oversized user text',d=>d.messages[0].content='x'.repeat(2001)],['oversized answer',d=>d.messages[1].content='x'.repeat(6001)],
 ['too many messages',d=>d.messages=Array.from({length:21},()=>messages).flat()],['invalid date',d=>d.savedAt='yesterday'],
])test('rejects '+name,()=>{const d=raw();change(d);assert.throws(()=>parseConversation(JSON.stringify(d)))})
test('corrupt/oversized storage fails safely',()=>{assert.throws(()=>parseConversation('{'));assert.throws(()=>parseConversation('x'.repeat(250001)))})
test('research results cannot be persisted',()=>{assert.throws(()=>saveConversation(storage(),'general_information',messages.map(m=>({...m,result:{citations:[]}}))))})
test('text that looks like HTML remains text; no rich content/approval object is restored',()=>{
 const d=raw();d.messages[1].content='<img src=x onerror=alert(1)>'
 assert.equal(parseConversation(JSON.stringify(d)).messages[1].content,d.messages[1].content)
})
test('storage access failures are surfaced for the UI to handle',()=>{
 const s={getItem(){throw Error('denied')},setItem(){throw Error('full')},removeItem(){throw Error('denied')}}
 assert.throws(()=>loadConversation(s));assert.throws(()=>saveConversation(s,'synthetic_demo',messages));assert.throws(()=>deleteConversation(s))
})
