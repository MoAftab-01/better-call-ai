/** Isolated production/public integration against SYNTHETIC data only. */
import { spawn } from 'node:child_process'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { join, resolve } from 'node:path'
import { randomUUID, createHash } from 'node:crypto'
import assert from 'node:assert/strict'
const root=resolve(import.meta.dirname,'../..')
const base=process.env.PUBLIC_E2E_BACKEND_URL||'http://127.0.0.1:8004'
const url=process.env.PUBLIC_E2E_FRONTEND_URL||'http://127.0.0.1:5176'
const publicationPending=true
const noSpeech=process.argv.includes('--no-speech')
const status=await fetch(base+'/api/chat/status'),data=await status.json()
if(publicationPending){
 assert.equal(status.headers.get('x-kanoon-public-website-test'),'no-corpus')
 assert.equal(data.research_state,'publication_pending');assert.equal(data.retrieval.passages,0)
}else assert.equal(status.headers.get('x-kanoon-synthetic-public-corpus'),'true')
assert.equal(data.provider_configured,false);assert.equal(data.retrieval.corpus_kind,'public')
const profile=join(root,'backend/data/test-runs','public-chrome-'+randomUUID().slice(0,8))
await mkdir(profile,{recursive:true})
const chrome=spawn(process.env.CHROME_BINARY||'C:/Program Files/Google/Chrome/Application/chrome.exe',[
 '--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'})
const pause=ms=>new Promise(r=>setTimeout(r,ms));let socket,session,id=0
const pending=new Map(),checks=[];let chatPosts=0, demoPosts=0, leakedAuth=false, intercept=false
function rpc(method,params={},browser=false){const key=++id;return new Promise((resolve,reject)=>{
 const timer=setTimeout(()=>reject(Error('CDP timeout '+method)),15000)
 pending.set(key,{resolve:v=>{clearTimeout(timer);resolve(v)},reject})
 socket.send(JSON.stringify({id:key,method,params,...(session&&!browser?{sessionId:session}:{})}))
})}
async function evaluate(expression){const r=await rpc('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});assert(!r.exceptionDetails);return r.result.value}
async function until(expression){for(let n=0;n<150;n++){if(await evaluate('Boolean('+expression+')'))return;await pause(100)}throw Error('Timed out: '+expression+'; body='+await evaluate('document.body?.textContent?.slice(0,2000)'))}
async function input(selector,value){await evaluate(`(()=>{let e=document.querySelector(${JSON.stringify(selector)});Object.getOwnPropertyDescriptor(e instanceof HTMLTextAreaElement?HTMLTextAreaElement.prototype:HTMLInputElement.prototype,'value').set.call(e,${JSON.stringify(value)});e.dispatchEvent(new Event('input',{bubbles:true}));})()`)}
try{
 let info;for(let n=0;n<150;n++){try{info=(await readFile(join(profile,'DevToolsActivePort'),'utf8')).trim().split('\n');break}catch{await pause(100)}}
 assert(info);socket=new WebSocket('ws://127.0.0.1:'+info[0].trim()+info[1].trim())
 await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',reject,{once:true})})
 socket.addEventListener('message',e=>{
  const r=JSON.parse(e.data)
  if(pending.has(r.id)){const p=pending.get(r.id);pending.delete(r.id);r.error?p.reject(Error(r.error.message)):p.resolve(r.result)}
  if(r.method==='Network.requestWillBeSent'&&r.params.request.method==='POST'){
   const req=r.params.request
   if(req.url.endsWith('/api/chat'))chatPosts++
   if(req.url.endsWith('/api/demo/chat')){demoPosts++;leakedAuth ||= Object.keys(req.headers).some(k=>k.toLowerCase()==='authorization')}
  }
  if(r.method==='Fetch.requestPaused'){
   if(intercept==='hold')return
   void rpc('Fetch.fulfillRequest',{requestId:r.params.requestId,responseCode:429,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from(JSON.stringify({error:{message:'SYNTHETIC rate-limit response; retry later.'}})).toString('base64')})
  }
 })
 const target=await rpc('Target.createTarget',{url:'about:blank'},true)
 session=(await rpc('Target.attachToTarget',{targetId:target.targetId,flatten:true},true)).sessionId
 await rpc('Page.enable');await rpc('Runtime.enable');await rpc('Network.enable')
 await rpc('Page.addScriptToEvaluateOnNewDocument',{source:noSpeech?`
  Object.defineProperty(window,'SpeechRecognition',{value:undefined});Object.defineProperty(window,'webkitSpeechRecognition',{value:undefined});Object.defineProperty(window,'speechSynthesis',{value:undefined});
 `:`
  class SyntheticRecognition {constructor(){window.__recognition=this}start(){this.started=true}stop(){this.stopped=true;this.onend?.()}abort(){this.aborted=true;this.onend?.()}}
  window.SpeechRecognition=SyntheticRecognition;
  Object.defineProperty(window,'speechSynthesis',{value:{cancel(){window.__speechCancelled=true},speak(u){window.__spoken=u.text}},configurable:true});
 `})
 await rpc('Page.navigate',{url})
 await until('document.querySelector(".connection-connected") && document.querySelector(".demo-notice button") && document.querySelector(".publication-notice")')
 assert.equal((await fetch(base+'/api/ready')).status,503)
 await input('#legal-question','rent receipt')
 assert(await evaluate('document.querySelector(".send-button").disabled'))
 checks.push('real research remains publication-pending with disabled submit')
 await evaluate('document.querySelector(".demo-notice button").click()')
 await until('document.body.textContent.includes("Demo mode \u2014 synthetic examples")')
 assert.equal(await evaluate('document.querySelectorAll(".access-token,.citation-card").length'),0)
 assert.equal(await evaluate('document.querySelector("form.composer").getAttribute("aria-label")'),'Synthetic demo question')
 checks.push('explicit opt-in, accessible demo label, no token or citation UI')
 if(!noSpeech){
  assert(await evaluate('document.querySelector(".browser-voice button").disabled'))
  await evaluate('document.querySelector(".voice-consent input").click();document.querySelector(".browser-voice button").click()')
  await until('document.querySelector(".browser-voice button").textContent.includes("Stop recording")')
  const before=demoPosts
  await evaluate('window.__recognition.onresult({results:[[{transcript:"fictional rent receipt"}]]});window.__recognition.onend()')
  assert.equal(await evaluate('document.querySelector("#legal-question").value'),'fictional rent receipt');assert.equal(demoPosts,before)
  checks.push('mock voice consent/start/transcription; no automatic submission')
  await evaluate('document.querySelector(".browser-voice button").click();window.__recognition.onerror({error:"not-allowed"});window.__recognition.onend()')
  await until('document.querySelector(".browser-voice").textContent.includes("permission denied")')
  await evaluate('document.querySelector(".browser-voice button").click()')
  await until('document.querySelector(".browser-voice button").textContent.includes("Stop recording")')
  await evaluate('document.querySelector(".browser-voice button").click()')
  assert(await evaluate('window.__recognition.stopped'))
  await evaluate('document.querySelector(".browser-voice button").click()')
  await until('document.querySelectorAll(".browser-voice button").length===2')
  await evaluate('document.querySelectorAll(".browser-voice button")[1].click()')
  assert(await evaluate('window.__recognition.aborted && window.__recognition.onresult===null'))
  checks.push('mock microphone denial, stop and cancellation retain typed fallback')
 }else{
  assert((await evaluate('document.querySelector(".browser-voice").textContent')).includes('unavailable'))
  checks.push('unsupported recognition retains typed fallback')
 }
 await input('#legal-question','fictional rent receipt')
 assert.equal(await evaluate(`(()=>{const e=new KeyboardEvent('keydown',{key:'Enter',shiftKey:true,bubbles:true,cancelable:true});document.querySelector('#legal-question').dispatchEvent(e);return e.defaultPrevented})()`),false)
 await evaluate('document.querySelector("#legal-question").focus()')
 await rpc('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13})
 await rpc('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13})
 await until('document.querySelector(".chat-message.assistant")')
 const text=await evaluate('document.querySelector(".chat-message.assistant").textContent')
 assert(text.includes('Fictional/synthetic example only')&&text.includes('Mira')&&text.includes('No official citations'))
 assert.equal(await evaluate('document.querySelectorAll(".citation-card,.source-select[aria-label*=citation]").length'),0)
 checks.push('Enter submits real demo request; Shift+Enter stays newline; synthetic answer with no citations')
 if(!noSpeech){
  await evaluate('Array.from(document.querySelectorAll("button")).find(b=>b.textContent.includes("Read aloud")).click()')
  assert((await evaluate('window.__spoken')).includes('Fictional/synthetic example only'))
  await until('Array.from(document.querySelectorAll("button")).some(b=>b.textContent.includes("Stop reading"))')
  await evaluate('Array.from(document.querySelectorAll("button")).find(b=>b.textContent.includes("Stop reading")).click()')
  assert(await evaluate('window.__speechCancelled'))
  checks.push('mock synthesis reads disclaimer and exact response; stop works')
 }else{
  assert((await evaluate('document.querySelector(".message-list").textContent')).includes('Read aloud is unavailable'))
  checks.push('unsupported synthesis leaves full response readable')
 }
 intercept='rate'
 await rpc('Fetch.enable',{patterns:[{urlPattern:'*api/demo/chat',requestStage:'Request'}]})
 await input('#legal-question','parcel exercise');await evaluate('document.querySelector(".send-button").click()')
 await until('document.querySelector(".chat-error")')
 assert((await evaluate('document.querySelector(".chat-error").textContent')).includes('SYNTHETIC rate-limit'))
 await rpc('Fetch.disable');intercept=false
 await evaluate('document.querySelector(".chat-error button").click()')
 await until('document.querySelectorAll(".chat-message.assistant").length===2')
 checks.push('error and retry states preserve message history')
 intercept='hold'
 await rpc('Fetch.enable',{patterns:[{urlPattern:'*api/demo/chat',requestStage:'Request'}]})
 await input('#legal-question','timeline exercise');await evaluate('document.querySelector(".send-button").click()')
 await until('document.querySelector(".chat-progress")')
 assert(await evaluate('document.querySelector(".send-button").disabled'))
 await evaluate('Array.from(document.querySelectorAll("button")).find(b=>b.textContent==="Cancel request").click()')
 await until('document.querySelector(".chat-error").textContent.includes("Request cancelled")')
 await rpc('Fetch.disable');intercept=false
 checks.push('loading, duplicate-send guard and request cancellation')
 await rpc('Emulation.setDeviceMetricsOverride',{width:320,height:850,deviceScaleFactor:1,mobile:true});await pause(200)
 assert(await evaluate('document.documentElement.scrollWidth<=innerWidth'))
 assert(await evaluate('!!document.querySelector("label[for=legal-question]") && !!document.querySelector(".message-list[aria-live=polite]")'))
 checks.push('320px layout has no overflow; labelled input and live message log')
 await evaluate('document.querySelector(".demo-notice button").click()')
 await until('!document.querySelector(".chat-message")')
 await input('#legal-question','real legal question')
 assert(await evaluate('document.querySelector(".send-button").disabled'))
 assert.equal(chatPosts,0);assert.equal(leakedAuth,false)
 assert.equal((await fetch(base+'/api/ready')).status,503)
 checks.push('leaving demo clears chat; research still blocked; zero research POSTs or bearer-token exposure')
 const report={synthetic_only:true,real_microphone_tested:false,live_groq:false,no_speech:noSpeech,checks,demo_posts:demoPosts,research_posts:chatPosts,authorization_exposed:leakedAuth}
 await mkdir(join(root,'frontend/.qa'),{recursive:true})
 await writeFile(join(root,'frontend/.qa/demo-'+(noSpeech?'unsupported':'mock-voice')+'.json'),JSON.stringify(report,null,2))
 console.log(JSON.stringify(report))
}finally{
 if(socket?.readyState===WebSocket.OPEN){try{await rpc('Browser.close',{},true)}catch{}socket.close()}
 if(chrome.exitCode===null)chrome.kill()
}
