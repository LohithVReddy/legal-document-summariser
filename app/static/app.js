let current={id:null,text:""};
const $=id=>document.getElementById(id);
$("fileInput").addEventListener("change",()=>{const f=$("fileInput").files[0];$("fileName").textContent=f?f.name:"Choose a legal document";});
$("summarizeBtn").addEventListener("click",async()=>{
 const file=$("fileInput").files[0]; if(!file){status("Choose a document first.",true);return;}
 const form=new FormData();form.append("file",file);form.append("level",$("level").value);
 $("summarizeBtn").disabled=true;status("Processing document...",false);
 try{const r=await fetch("/api/summarize",{method:"POST",body:form});const d=await r.json();if(!r.ok)throw Error(d.detail||"Processing failed");
 current={id:d.document_id,text:d.raw_text};$("docType").textContent=d.document_type;$("pageCount").textContent=d.pages;$("partyCount").textContent=d.key_information.parties.length;$("clauseCount").textContent=d.clauses.length;$("fileMeta").textContent=d.filename;$("summary").textContent=d.summary;renderInfo(d.key_information);renderClauses(d.clauses);$("downloadBtn").disabled=false;$("askBtn").disabled=false;status("Summary generated successfully.",false);loadHistory();
 }catch(e){status(e.message,true)}finally{$("summarizeBtn").disabled=false}
});
$("downloadBtn").addEventListener("click",()=>{if(current.id)location.href="/api/download/"+current.id});
$("askBtn").addEventListener("click",async()=>{
 const q=$("question").value.trim();if(!q||!current.text)return;$("askBtn").disabled=true;$("answer").textContent="Searching...";
 const f=new FormData();f.append("question",q);f.append("text",current.text);
 try{const r=await fetch("/api/ask",{method:"POST",body:f});const d=await r.json();$("answer").innerHTML="<div>"+esc(d.answer)+"</div>"+(d.sources||[]).map(s=>'<div class="source"><b>Source: Page '+s.page+"</b><br>"+esc(s.text)+"</div>").join("")}catch(e){$("answer").textContent=e.message}finally{$("askBtn").disabled=false}
});
function renderInfo(i){const e=[["Parties",i.parties],["Dates",i.dates],["Money",i.money],["Emails",i.emails]];$("keyInfo").innerHTML=e.map(x=>x[1].length?'<div class="info-item"><strong>'+x[0]+"</strong>"+x[1].map(esc).join("<br>")+"</div>":"").join("")||'<span class="muted">No key information detected.</span>'}
function renderClauses(c){$("clauses").innerHTML=c.length?c.map(x=>'<span class="chip">'+esc(x)+"</span>").join(""):'<span class="muted">No common clauses detected.</span>'}
async function loadHistory(){const r=await fetch("/api/history"),d=await r.json();$("history").innerHTML=d.length?d.map(x=>'<div class="history-item"><span><b>'+esc(x.filename)+"</b><br><small>"+esc(x.document_type||"")+"</small></span><small>"+esc(x.uploaded_at)+"</small></div>").join(""):'<span class="muted">No documents yet.</span>'}
function status(x,e){$("status").textContent=x;$("status").style.color=e?"#b42318":"#067647"}
function esc(x){return String(x).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))}
loadHistory();
