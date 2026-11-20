import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { Activity, ArrowRight, CheckCircle2, Columns3, FolderKanban, LayoutList, LockKeyhole, MessageSquare, Plus, RefreshCw, Search, Send, ShieldCheck, X } from 'lucide-react';

type State='backlog'|'todo'|'in_progress'|'in_review'|'done'|'canceled';
type Priority='none'|'urgent'|'high'|'medium'|'low';
type Project={id:string;name:string;project_key:string;description:string};
type Issue={id:string;project_id:string;identifier:string;title:string;description:string;status:State;priority:Priority;assignee:string|null;cycle_id:string|null};
type Cycle={id:string;name:string;start_date:string;end_date:string};
type Comment={id:string;author:string;body:string;created_at:string};
type Stats={total:number;by_status:Partial<Record<State,number>>};
const states:{id:State;label:string}[]=[
{id:'backlog',label:'Backlog'},{id:'todo',label:'To do'},{id:'in_progress',label:'In progress'},
{id:'in_review',label:'In review'},{id:'done',label:'Done'},{id:'canceled',label:'Canceled'}];
const priorities:Priority[]=['urgent','high','medium','low','none'];
const base=((import.meta.env.VITE_PROJECTS_API_BASE as string|undefined)||'/api/v1').replace(/\/$/,'');
async function api<T>(token:string,path:string,init?:RequestInit):Promise<T>{
 const response=await fetch(base+path,{...init,headers:{'Content-Type':'application/json','Authorization':'Bearer '+token,...init?.headers}});
 if(!response.ok){let detail='Request failed ('+response.status+')';try{const data=await response.json();if(typeof data.detail==='string')detail=data.detail;}catch{/* no JSON */}throw Error(detail);}
 return response.json() as Promise<T>;
}
export default function App(){
 const [token,setToken]=useState(''),[draft,setDraft]=useState('');
 const [projects,setProjects]=useState<Project[]>([]),[projectId,setProjectId]=useState('');
 const [issues,setIssues]=useState<Issue[]>([]),[cycles,setCycles]=useState<Cycle[]>([]),[stats,setStats]=useState<Stats|null>(null);
 const [view,setView]=useState<'board'|'list'>('board'),[search,setSearch]=useState(''),[filter,setFilter]=useState<State|'all'>('all');
 const [active,setActive]=useState<Issue|null>(null),[comments,setComments]=useState<Comment[]>([]);
 const [mode,setMode]=useState<null|'project'|'issue'|'cycle'>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const [name,setName]=useState(''),[key,setKey]=useState(''),[description,setDescription]=useState(''),[priority,setPriority]=useState<Priority>('medium'),[cycleId,setCycleId]=useState('');
 const [startDate,setStartDate]=useState(''),[endDate,setEndDate]=useState(''),[comment,setComment]=useState('');
 const current=projects.find(p=>p.id===projectId);
 const loadProjects=useCallback(async()=>{const rows=await api<Project[]>(token,'/projects');setProjects(rows);setProjectId(old=>rows.find(p=>p.id===old)?.id||rows[0]?.id||'');},[token]);
 const loadIssues=useCallback(async()=>{if(!projectId){setIssues([]);setCycles([]);setStats(null);return;}
  const prefix='/projects/'+encodeURIComponent(projectId);
  const [rows,sprints,summary]=await Promise.all([api<Issue[]>(token,prefix+'/issues?limit=200'),api<Cycle[]>(token,prefix+'/cycles'),api<Stats>(token,prefix+'/stats')]);
  setIssues(rows);setCycles(sprints);setStats(summary);setActive(old=>old?rows.find(x=>x.id===old.id)||null:null);
 },[projectId,token]);
 useEffect(()=>{if(token)loadProjects().catch(e=>setError(e.message));},[token,loadProjects]);
 useEffect(()=>{if(token)loadIssues().catch(e=>setError(e.message));},[token,loadIssues]);
 useEffect(()=>{if(active)api<Comment[]>(token,'/issues/'+active.id+'/comments').then(setComments).catch(e=>setError(e.message));else setComments([]);},[active?.id,token]);
 useEffect(()=>{const fn=(e:KeyboardEvent)=>{if(e.key==='Escape'){setActive(null);setMode(null);}if(e.key==='/'&&!['INPUT','TEXTAREA'].includes((e.target as HTMLElement).tagName)){e.preventDefault();document.getElementById('issue-search')?.focus();}};window.addEventListener('keydown',fn);return()=>window.removeEventListener('keydown',fn);},[]);
 const visible=useMemo(()=>issues.filter(x=>(filter==='all'||x.status===filter)&&(x.title.toLowerCase().includes(search.toLowerCase())||x.identifier.toLowerCase().includes(search.toLowerCase()))),[issues,filter,search]);
 async function run(fn:()=>Promise<void>){setBusy(true);setError('');try{await fn();}catch(e){setError(e instanceof Error?e.message:'Unexpected error');}finally{setBusy(false);}}
 async function create(e:FormEvent){e.preventDefault();await run(async()=>{if(mode==='project'){const row=await api<Project>(token,'/projects',{method:'POST',body:JSON.stringify({name,key})});await loadProjects();setProjectId(row.id);}
  if(mode==='issue'){await api<Issue>(token,'/projects/'+projectId+'/issues',{method:'POST',body:JSON.stringify({title:name,description,priority,cycle_id:cycleId||null})});await loadIssues();}
  if(mode==='cycle'){await api<Cycle>(token,'/projects/'+projectId+'/cycles',{method:'POST',body:JSON.stringify({name,start_date:startDate,end_date:endDate})});await loadIssues();}
  setMode(null);setName('');setDescription('');setKey('');setCycleId('');});}
 async function updateIssue(id:string,patch:object){await run(async()=>{const next=await api<Issue>(token,'/issues/'+id,{method:'PATCH',body:JSON.stringify(patch)});setActive(next);await loadIssues();});}
 async function addComment(e:FormEvent){e.preventDefault();if(!active)return;await run(async()=>{await api<Comment>(token,'/issues/'+active.id+'/comments',{method:'POST',body:JSON.stringify({author:'GoreeCloud',body:comment})});setComments(await api<Comment[]>(token,'/issues/'+active.id+'/comments'));setComment('');});}
 function openMode(m:'project'|'issue'|'cycle'){setName('');setDescription('');setMode(m);}
 if(!token)return <main className="auth"><form className="auth-card surface" onSubmit={e=>{e.preventDefault();setToken(draft.trim());setError('');}}>
  <div className="logo"><FolderKanban size={28}/></div><p className="kicker">GOREECLOUD / WORKSPACE</p>
  <h1>Build with clarity.</h1><p className="muted">One private workspace for planning, issues, cycles, and progress.</p>
  <label htmlFor="access">API access token</label><input id="access" type="password" autoComplete="off" value={draft} minLength={24} required placeholder="PROJECTS_ADMIN_TOKEN" onChange={e=>setDraft(e.target.value)}/>
  {error&&<p className="error" role="alert">{error}</p>}<button className="primary" type="submit">Open workspace <ArrowRight size={18}/></button>
  <small className="muted"><LockKeyhole size={14}/> The token stays in this tab's memory. Never use an untrusted server.</small>
 </form></main>;
 return <div className="layout">
  <aside className="nav">
   <div className="brand"><span className="logo"><FolderKanban size={21}/></span><div><strong>GoreeCloud</strong><small>Projects</small></div></div>
   <div className="workspace"><small>WORKSPACE</small><strong>Personal workspace</strong></div>
   <p className="nav-label">OVERVIEW</p>
   <button className="nav-button selected" onClick={()=>{setFilter('all');setSearch('');}}><FolderKanban size={18}/> Projects <span className="count">{projects.length}</span></button>
   <button className="nav-button" onClick={()=>setView('list')}><LayoutList size={18}/> All issues</button>
   <div className="nav-label projects-label">YOUR PROJECTS <button className="small-icon" title="New project" aria-label="New project" onClick={()=>openMode('project')}><Plus size={17}/></button></div>
   {projects.map(p=><button key={p.id} className={'project-button '+(p.id===projectId?'selected':'')} onClick={()=>{setProjectId(p.id);setActive(null);}}><span className="initials">{p.project_key.slice(0,2)}</span><span className="project-name">{p.name}</span></button>)}
   <div className="nav-bottom"><div><ShieldCheck size={16}/> Self-hosted by design</div><button className="nav-button" onClick={()=>{setToken('');setDraft('');setProjects([]);setActive(null);}}><LockKeyhole size={18}/> Lock workspace</button></div>
  </aside>
  <main className="main">
   <header className="topbar"><div><span>Workspace</span><b>/</b><strong>{current?.name||'Projects'}</strong></div><div className="top-right"><span className="dev"><Activity size={13}/> DEVELOPMENT PREVIEW</span><button className="small-icon" aria-label="Refresh" onClick={()=>run(async()=>{await loadProjects();await loadIssues();})}><RefreshCw size={18}/></button><span className="user-avatar">GC</span></div></header>
   <div className="content">
    <div className="page-heading"><div><p className="kicker">WORKSPACE / {current?.project_key||'ALL PROJECTS'}</p><h1>{current?.name||'Start something new'}</h1><p className="muted">{current?.description||'Plan deliberately. Make progress visible.'}</p></div><div className="actions"><button className="secondary" disabled={!projectId} onClick={()=>openMode('cycle')}>New cycle</button><button className="primary" disabled={!projectId} onClick={()=>openMode('issue')}><Plus size={18}/> New issue</button></div></div>
    {error&&<div className="error-box" role="alert">{error}<button className="small-icon" aria-label="Dismiss" onClick={()=>setError('')}><X size={16}/></button></div>}
    {!projects.length?<section className="empty surface"><FolderKanban size={45}/><h2>Create your first project</h2><p>Get started with a backlog, meaningful issue IDs, and cycles.</p><button className="primary" onClick={()=>openMode('project')}><Plus size={18}/> New project</button></section>:<>
    <div className="stats"><div className="stat surface"><span>All issues</span><strong>{stats?.total??0}</strong><small>Across your project</small></div><div className="stat surface"><span>In progress</span><strong>{stats?.by_status.in_progress??0}</strong><small>Currently being worked</small></div><div className="stat surface"><span>Completed</span><strong>{stats?.by_status.done??0}</strong><small>Moved to done</small></div><div className="stat surface"><span>Cycles</span><strong>{cycles.length}</strong><small>Planning windows</small></div></div>
    <section className="tracker"><div className="section-head"><div><h2>Issue tracker</h2><p className="muted">Keep everything moving, one issue at a time.</p></div><div className="tools"><label className="search"><Search size={16}/><input id="issue-search" aria-label="Search issues" placeholder="Search issues  /" value={search} onChange={e=>setSearch(e.target.value)}/></label><select aria-label="Filter by status" value={filter} onChange={e=>setFilter(e.target.value as State|'all')}><option value="all">All statuses</option>{states.map(s=><option key={s.id} value={s.id}>{s.label}</option>)}</select><div className="switch"><button aria-label="Board view" className={view==='board'?'selected':''} onClick={()=>setView('board')}><Columns3 size={18}/></button><button aria-label="List view" className={view==='list'?'selected':''} onClick={()=>setView('list')}><LayoutList size={18}/></button></div></div></div>
    {view==='board'?<div className="board">{states.map(s=><div className="column" key={s.id}><header><span className={'state-icon '+s.id}>●</span><strong>{s.label}</strong><span className="count">{visible.filter(i=>i.status===s.id).length}</span></header>{visible.filter(i=>i.status===s.id).map(i=><button className="card surface" key={i.id} onClick={()=>setActive(i)}><span>{i.title}</span><footer><code>{i.identifier}</code><span className={'priority '+i.priority}>{i.priority}</span></footer></button>)}{!visible.some(i=>i.status===s.id)&&<p className="column-empty">No issues here yet</p>}</div>)}</div>:
    <div className="list surface">{visible.map(i=><button className="issue-row" key={i.id} onClick={()=>setActive(i)}><span className={'state-icon '+i.status}>●</span><code>{i.identifier}</code><strong>{i.title}</strong><span>{states.find(s=>s.id===i.status)?.label}</span><small className={'priority '+i.priority}>{i.priority}</small><ArrowRight size={17}/></button>)}{!visible.length&&<div className="no-results">No matching issues.</div>}</div>}
    <p className="footnote">Showing {visible.length} of {issues.length} loaded issues. <button onClick={()=>openMode('issue')}>Create an issue</button></p>
    </section></>}
   </div>
  </main>
  {active&&<div className="shade" onMouseDown={e=>{if(e.currentTarget===e.target)setActive(null);}}><section className="detail surface" role="dialog" aria-modal="true" aria-labelledby="issue-title"><header><code>{active.identifier}</code><button className="small-icon" aria-label="Close" onClick={()=>setActive(null)}><X size={20}/></button></header><h2 id="issue-title">{active.title}</h2><p className="muted issue-description">{active.description||'No description yet.'}</p>
    <div className="properties"><label>Status<select disabled={busy} value={active.status} onChange={e=>updateIssue(active.id,{status:e.target.value})}>{states.map(s=><option key={s.id} value={s.id}>{s.label}</option>)}</select></label><label>Priority<select disabled={busy} value={active.priority} onChange={e=>updateIssue(active.id,{priority:e.target.value})}>{priorities.map(x=><option value={x} key={x}>{x}</option>)}</select></label><label>Cycle<select disabled={busy} value={active.cycle_id||''} onChange={e=>updateIssue(active.id,{cycle_id:e.target.value||null})}><option value="">No cycle</option>{cycles.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label></div>
    <section className="comment-section"><h3><MessageSquare size={18}/> Comments</h3>{comments.map(c=><div className="comment" key={c.id}><span className="user-avatar">GC</span><div><strong>{c.author}</strong><small>{new Date(c.created_at).toLocaleString()}</small><p>{c.body}</p></div></div>)}{!comments.length&&<p className="muted">No comments yet.</p>}<form onSubmit={addComment}><input aria-label="Comment" required value={comment} onChange={e=>setComment(e.target.value)} placeholder="Add a comment..."/><button className="primary" disabled={busy} aria-label="Send"><Send size={17}/></button></form></section>
   </section></div>}
  {mode&&<div className="shade modal-shade" onMouseDown={e=>{if(e.currentTarget===e.target)setMode(null);}}><section className="modal surface" role="dialog" aria-modal="true" aria-labelledby="modal-title"><header><p className="kicker">GOREECLOUD / CREATE</p><button className="small-icon" aria-label="Close" onClick={()=>setMode(null)}><X size={20}/></button></header><h2 id="modal-title">{mode==='project'?'Create a project':mode==='issue'?'Create an issue':'Plan a cycle'}</h2><form onSubmit={create} className="form"><label>{mode==='issue'?'Issue title':mode==='cycle'?'Cycle name':'Project name'}<input autoFocus required maxLength={mode==='issue'?240:120} value={name} onChange={e=>setName(e.target.value)} placeholder={mode==='project'?'GoreeCloud Notebook':mode==='cycle'?'Sprint 1':'What needs to get done?'}/></label>
    {mode==='project'&&<label>Identifier (2–8 letters/digits)<input required pattern="[A-Za-z][A-Za-z0-9]{1,7}" maxLength={8} value={key} onChange={e=>setKey(e.target.value)} placeholder="NOTE"/></label>}
    {mode==='issue'&&<><label>Description<textarea rows={4} value={description} onChange={e=>setDescription(e.target.value)} placeholder="Context and acceptance criteria"/></label><div className="form-row"><label>Priority<select value={priority} onChange={e=>setPriority(e.target.value as Priority)}>{priorities.map(x=><option value={x} key={x}>{x}</option>)}</select></label><label>Cycle<select value={cycleId} onChange={e=>setCycleId(e.target.value)}><option value="">No cycle</option>{cycles.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label></div></>}
    {mode==='cycle'&&<div className="form-row"><label>Start date<input type="date" required value={startDate} onChange={e=>setStartDate(e.target.value)}/></label><label>End date<input type="date" required min={startDate} value={endDate} onChange={e=>setEndDate(e.target.value)}/></label></div>}
    <button className="primary" disabled={busy} type="submit">{busy?'Working…':'Create'} <CheckCircle2 size={17}/></button>
   </form></section></div>}
 </div>;
}
