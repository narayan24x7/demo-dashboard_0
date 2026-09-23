'use strict';
const $=id=>document.getElementById(id);
let data=null, page='overview';
const pages={
  overview:['◈','Milestone 3 overview','Workforce, marketing and operational insights integrated with Milestones 1 and 2.'],
  performance:['↗','Outlet performance · M1','Sales monitoring, peer benchmarking and performance score.'],
  inventory:['▦','Inventory intelligence · M2','Forecast demand, monitor stock and generate replenishment recommendations.'],
  staff:['♧','Workforce analytics · M3','Enhanced Staff Agent for coverage, attendance and productivity.'],
  marketing:['◎','Marketing effectiveness · M3','Enhanced Marketing Agent for CTR, conversion, ROAS and contribution ROI.'],
  insights:['✦','Operational insights · M3','Cross-module recommendations generated only from Milestones 1–3 evidence.'],
  data:['⇄','Data preparation & validation · M3','Validate source datasets, joins and CSV contracts before analytics.'],
  testing:['✓','Integration & testing · M3','Verify the end-to-end Milestone 3 pipeline and recent analytics runs.']
};
const esc=v=>String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=(v,d=0)=>v==null?'—':Number(v).toLocaleString('en-IN',{maximumFractionDigits:d});
const money=v=>'₹'+fmt(v);
const sum=(xs,k)=>xs.reduce((a,x)=>a+(Number(x[k])||0),0);
const avg=(xs,k)=>{const values=xs.filter(x=>x[k]!=null);return values.length?sum(values,k)/values.length:null;};
const pill=(v,prefix='')=>`<span class="pill ${esc((prefix+v).toLowerCase().replace(/\s+/g,'-'))}">${esc(v)}</span>`;
function notice(message,error=false){$('notice').hidden=false;$('notice').textContent=message;$('notice').className=error?'error':'';}
async function api(path,options={}){const response=await fetch(path,{...options,headers:{'Content-Type':'application/json',...options.headers}});if(!response.ok){let body={};try{body=await response.json();}catch{}throw Error(body.error||'Request failed');}return response;}
$('nav').innerHTML=Object.entries(pages).map(([key,[icon,label]])=>`<button data-page="${key}"><span class="icon">${icon}</span>${label}</button>`).join('');
$('nav').onclick=e=>{const button=e.target.closest('[data-page]');if(button){page=button.dataset.page;render();}};
$('apply').onclick=()=>load().catch(e=>notice(e.message,true));
$('run').onclick=async()=>{ $('run').disabled=true;try{const result=await (await api('/api/run',{method:'POST',body:'{}'})).json();await load();notice(`Run #${result.id} completed · ${result.agents} agents · ${result.operational_insights} operational insights · ${result.scope}.`);}catch(e){notice(e.message,true);}finally{$('run').disabled=false;}};

function panel(title,subtitle,body){return `<section class="panel"><div class="panel-head"><div><h2>${esc(title)}</h2><p>${esc(subtitle)}</p></div></div>${body}</section>`;}
function kpis(items){return `<div class="kpis">${items.map((item,i)=>`<div class="kpi ${i===0?'featured':''}"><div class="kpi-label">${esc(item[0])}</div><div class="value">${item[1]}</div><div class="sub">${esc(item[2])}</div></div>`).join('')}</div>`;}
function table(rows,columns){if(!rows.length)return '<div class="empty">No records for the current filters.</div>';return `<div class="table-wrap"><table><thead><tr>${columns.map(c=>`<th>${esc(c[0])}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${columns.map(c=>`<td>${typeof c[1]==='function'?c[1](row):esc(row[c[1]])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;}
function trend(){
  if(!data.trend.length)return '<div class="empty">No sales trend data.</div>';
  const byDate={};data.trend.forEach(r=>byDate[r.date]=(byDate[r.date]||0)+r.revenue);
  const entries=Object.entries(byDate).sort((a,b)=>a[0].localeCompare(b[0]));
  const values=entries.map(x=>x[1]),max=Math.max(...values),min=Math.min(...values),range=max-min||1;
  const points=entries.map((x,i)=>`${20+i*(760/Math.max(1,entries.length-1))},${205-(x[1]-min)/range*165}`).join(' ');
  const labels=[0,Math.floor((entries.length-1)/2),entries.length-1].filter((x,i,a)=>a.indexOf(x)===i).map(i=>`<text x="${20+i*(760/Math.max(1,entries.length-1))}" y="226" text-anchor="middle">${esc(entries[i][0].slice(5))}</text>`).join('');
  return `<svg class="chart" viewBox="0 0 800 235" preserveAspectRatio="none"><line class="gridline" x1="20" x2="780" y1="40" y2="40"/><line class="gridline" x1="20" x2="780" y1="122" y2="122"/><line class="gridline" x1="20" x2="780" y1="205" y2="205"/><polyline class="trendline" points="${points}"/>${labels}</svg>`;
}
function attentionRanks(){return data.outlet_summary.map(x=>`<div class="rank"><span>${esc(x.name)}</span><div class="bar"><svg viewBox="0 0 100 9" preserveAspectRatio="none"><rect width="${Math.min(100,x.total_insights*20)}" height="9" rx="4"/></svg></div><b>${fmt(x.total_insights)}</b></div>`).join('')||'<div class="empty">No outlets</div>';}
function insightsList(limit=8){const rows=data.insights.slice(0,limit);return rows.map(r=>`<div class="insight"><div class="insight-symbol">!</div><div><h3>${esc(r.outlet)} · ${esc(r.source)} ${pill(r.severity,'severity-')}</h3><p><b>${esc(r.title)}</b> — ${esc(r.evidence)}</p><p>${esc(r.recommendation)}</p></div></div>`).join('')||'<div class="empty">No operational issues detected for the current filters.</div>';}

function overview(){
  const shortages=data.inventory.filter(x=>x.shortage).length;
  const high=data.insights.filter(x=>x.severity==='high').length;
  return kpis([
    ['Selected-period revenue',money(sum(data.performance,'revenue')),'Milestone 1 performance data'],
    ['Inventory reorder items',fmt(shortages),'Milestone 2 stock monitoring'],
    ['Average workforce coverage',fmt(avg(data.staff,'coverage_pct'),1)+'%','Milestone 3 Staff Agent'],
    ['Average marketing ROI',fmt(avg(data.marketing,'roi'),1)+'%','Milestone 3 Marketing Agent']
  ])+`<div class="grid2">${panel('Revenue pulse','Sales trend from the selected reporting period',trend())}${panel('Outlet attention','Count of operational insights; this is not a franchise health score',attentionRanks())}</div>`+
  panel('Milestone 3 priority insights',`${high} high-priority recommendation(s) from current evidence`,insightsList(5))+
  panel('Project scope','Only required functionality through Milestone 3 is included',`<div class="scope-grid">${[['Milestone 1',data.scope.milestone_1],['Milestone 2',data.scope.milestone_2],['Milestone 3',data.scope.milestone_3]].map(([name,items])=>`<div class="scope-card"><h3>${esc(name)}</h3><ul>${items.map(x=>`<li>${esc(x)}</li>`).join('')}</ul></div>`).join('')}</div>`);
}
function performance(){return kpis([
  ['Revenue',money(sum(data.performance,'revenue')),'Selected reporting period'],
  ['Operating contribution',money(sum(data.performance,'profit')),'Revenue minus recorded operating cost'],
  ['Transactions',fmt(sum(data.performance,'transactions')),'Across selected outlets'],
  ['Average performance score',fmt(avg(data.performance,'score'),1),'Peer revenue · margin · growth']
])+panel('Revenue over time','Equal-length previous periods are used for growth',trend())+panel('Outlet benchmarking','Milestone 1 peer index and performance score',table(data.performance,[['Outlet','name'],['Region','region'],['Revenue',r=>money(r.revenue)],['Margin',r=>fmt(r.margin,1)+'%'],['Growth',r=>r.growth==null?'No baseline':fmt(r.growth,1)+'%'],['Peer index',r=>fmt(r.peer_index,1)],['Score',r=>fmt(r.score,1)],['Health',r=>pill(r.health)]]));}
function inventory(){return kpis([
  ['Reorder candidates',fmt(data.inventory.filter(x=>x.shortage).length),'Below demand-based reorder point'],
  ['Stock value',money(data.inventory.reduce((a,x)=>a+x.quantity*x.unit_cost,0)),'Current quantity × unit cost'],
  ['Expiring ≤3 days',fmt(data.inventory.filter(x=>x.expiry_days<=3&&x.quantity>0).length),'Near-term expiry risk'],
  ['Average waste rate',fmt(avg(data.inventory,'waste_pct'),1)+'%','Trailing movement history']
])+`<div class="note">Milestone 2 dependency retained because Milestone 3 operational insights consume inventory evidence. Forecast uses trailing 28-day demand and lead-time safety stock.</div>`+panel('Stock monitoring & replenishment','Review the suggested quantity before ordering',table(data.inventory,[['Outlet','outlet'],['Product','product'],['On hand',r=>fmt(r.quantity,1)],['7-day demand',r=>fmt(r.forecast_7d,1)],['Days cover',r=>fmt(r.days_cover,1)],['Reorder point',r=>fmt(r.reorder_point,1)],['Replenish',r=>fmt(r.replenish)],['Waste',r=>fmt(r.waste_pct,1)+'%'],['Expiry',r=>r.expiry_days+'d']]));}
function staff(){return kpis([
  ['Team records',fmt(data.staff.length),'Current workforce dataset'],
  ['Average coverage',fmt(avg(data.staff,'coverage_pct'),1)+'%','Worked ÷ scheduled hours'],
  ['Uncovered hours',fmt(sum(data.staff,'hours_gap'),1),'Total roster gap'],
  ['Orders / worked hour',fmt(avg(data.staff,'orders_per_hour'),2),'Mean staff productivity indicator']
])+panel('Workforce analytics','Enhanced Staff Agent metrics for Milestone 3',table(data.staff,[['Outlet','outlet'],['Team member','name'],['Role','role'],['Shift','shift'],['Scheduled',r=>fmt(r.scheduled_hours,1)+'h'],['Worked',r=>fmt(r.worked_hours,1)+'h'],['Coverage',r=>fmt(r.coverage_pct,1)+'%'],['Orders/hour',r=>fmt(r.orders_per_hour,2)],['Gap',r=>fmt(r.hours_gap,1)+'h'],['Status',r=>pill(r.status)]]));}
function marketing(){return kpis([
  ['Campaign spend',money(sum(data.marketing,'spend')),'Selected outlets'],
  ['Attributed revenue',money(sum(data.marketing,'attributed_revenue')),'Recorded campaign attribution'],
  ['Average ROAS',fmt(avg(data.marketing,'roas'),2)+'x','Attributed revenue ÷ spend'],
  ['Average contribution ROI',fmt(avg(data.marketing,'roi'),1)+'%','Margin-adjusted return']
])+panel('Marketing effectiveness','Enhanced Marketing Agent metrics for Milestone 3',table(data.marketing,[['Outlet','outlet'],['Campaign','name'],['Spend',r=>money(r.spend)],['CTR',r=>fmt(r.ctr,2)+'%'],['Conversion',r=>fmt(r.conversion,2)+'%'],['ROAS',r=>fmt(r.roas,2)+'x'],['Contribution',r=>money(r.contribution)],['ROI',r=>r.roi==null?'—':fmt(r.roi,1)+'%'],['Cost/conv.',r=>r.cost_per_conversion==null?'—':money(r.cost_per_conversion)],['Effectiveness',r=>pill(r.effectiveness)]]));}
function insights(){return kpis([
  ['Operational insights',fmt(data.insights.length),'Cross-module recommendations'],
  ['High priority',fmt(data.insights.filter(x=>x.severity==='high').length),'Requires near-term review'],
  ['Medium priority',fmt(data.insights.filter(x=>x.severity==='medium').length),'Monitor and improve'],
  ['Stable outlets',fmt(data.outlet_summary.filter(x=>x.status==='Stable').length),'No current generated insight']
])+panel('Outlet attention summary','Recommendation counts only; no extra composite intelligence score',table(data.outlet_summary,[['Outlet','name'],['Region','region'],['High',r=>fmt(r.high_priorities)],['Medium',r=>fmt(r.medium_priorities)],['Total',r=>fmt(r.total_insights)],['Status',r=>pill(r.status,'status-')]]))+panel('Operational recommendations','Evidence and recommendations generated from Performance, Inventory, Workforce and Marketing only',table(data.insights,[['Severity',r=>pill(r.severity,'severity-')],['Outlet','outlet'],['Source','source'],['Insight','title'],['Evidence','evidence'],['Recommendation','recommendation']]));}
function datasets(){return panel('CSV validation & imports','Milestone 3 data preparation keeps only datasets required through Milestone 3',`<div class="data-form"><label>Dataset<select id="dataset">${Object.keys(data.schemas).map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('')}</select></label><p id="schema-hint" class="muted"></p><label>CSV file<input id="csv-file" type="file" accept=".csv,text/csv"></label><div class="buttons"><button id="export">Export source CSV</button><button class="primary" type="submit" form="import-form">Import validated CSV</button></div><form id="import-form"></form></div>`)+panel('Data coverage','Source table row counts after validation/import',table(data.data_quality,[['Dataset','dataset'],['Rows',r=>fmt(r.rows)]]))+`<div class="note">Join keys: <code>outlet_id</code> connects sales, inventory, staff and campaigns to outlets. <code>inventory_id</code> connects inventory movements. Audit/compliance data is intentionally not part of this Milestone 3 build.</div>`;}
function testing(){
  const runs=data.runs.map(r=>{let summary={};try{summary=JSON.parse(r.summary||'{}');}catch{}return {...r,agents:summary.agents,insights:summary.operational_insights,scope:summary.scope};});
  return panel('Milestone 3 integration flow','The dashboard consumes validated outputs from all required modules',`<div class="integration-flow"><div class="flow-box"><b>1. Data preparation</b>CSV validation + joins</div><div class="flow-box"><b>2. M1 + M2 agents</b>Performance + Inventory</div><div class="flow-box"><b>3. M3 agents</b>Staff + Marketing</div><div class="flow-box"><b>4. Operational insights</b>Cross-module recommendations</div><div class="flow-box"><b>5. M3 dashboard</b>Integrated visualization</div></div>`)+panel('Included verification','Automated tests cover analytics, data validation, API filters and removal of post-Milestone-3 routes',`<p class="check">✓ Run locally: <code>python -m unittest discover -s tests -v</code></p><p class="check">✓ HTTP smoke: <code>python tests/http_smoke.py</code></p><p class="check">✓ JavaScript syntax: <code>node --check franchiseops/static/app.js</code></p>`)+panel('Recent analytics runs','Integration run history from this database',table(runs,[['Run','id'],['Status','status'],['Agents',r=>fmt(r.agents)],['Insights',r=>fmt(r.insights)],['Scope','scope'],['Started','started_at'],['Finished','finished_at']]));
}
function bindDataPage(){if(page!=='data')return;const dataset=$('dataset');if(!dataset)return;const updateHint=()=>{$('schema-hint').textContent='Required columns: '+data.schemas[dataset.value].join(', ');};dataset.onchange=updateHint;updateHint();$('export').onclick=async()=>{try{const name=dataset.value;const blob=await (await api('/api/export?dataset='+encodeURIComponent(name))).blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name+'.csv';a.click();URL.revokeObjectURL(url);}catch(e){notice(e.message,true);}};$('import-form').onsubmit=async e=>{e.preventDefault();try{const file=$('csv-file').files[0];if(!file)throw Error('Choose a CSV file');if(file.size>4500000)throw Error('CSV must be smaller than 4.5 MB');const result=await (await api('/api/import',{method:'POST',body:JSON.stringify({dataset:dataset.value,csv:await file.text()})})).json();await load();notice(result.rows+' rows imported and validated.');}catch(error){notice(error.message,true);}};}
function render(){if(!data)return;document.querySelectorAll('[data-page]').forEach(x=>x.classList.toggle('active',x.dataset.page===page));$('page-title').textContent=pages[page][1];$('page-description').textContent=pages[page][2];$('content').innerHTML=({overview,performance,inventory,staff,marketing,insights,data:datasets,testing}[page])();bindDataPage();}
function updateFilters(){const regionValue=$('region').value,outletValue=$('outlet').value;const regions=[...new Set(data.outlets.map(x=>x.region))].sort();$('region').innerHTML='<option value="">All regions</option>'+regions.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('');$('outlet').innerHTML='<option value="">All outlets</option>'+data.outlets.map(x=>`<option value="${x.id}">${esc(x.name)}</option>`).join('');$('region').value=regions.includes(regionValue)?regionValue:'';$('outlet').value=data.outlets.some(x=>String(x.id)===outletValue)?outletValue:'';}
async function load(){const first=!data;const params=new URLSearchParams();if($('region').value)params.set('region',$('region').value);if($('outlet').value)params.set('outlet',$('outlet').value);if($('start').value)params.set('start',$('start').value);if($('end').value)params.set('end',$('end').value);data=await (await api('/api/dashboard'+(params.toString()?'?'+params:''))).json();if(first){$('start').value=data.start;$('end').value=data.end;}updateFilters();$('freshness').textContent=`Snapshot ${data.snapshot_date} · scope ${data.scope.agents} agents through M3`;render();}
$('export-view').onclick=()=>{if(!data)return;const key={overview:'insights',performance:'performance',inventory:'inventory',staff:'staff',marketing:'marketing',insights:'insights',testing:'runs'}[page];const records=data[key];if(!Array.isArray(records)||!records.length){notice('Choose a dashboard with records to export.');return;}const headers=Object.keys(records[0]);const quote=value=>'"'+String(value??'').replaceAll('"','""')+'"';const csv=[headers.join(','),...records.map(row=>headers.map(h=>quote(typeof row[h]==='object'?JSON.stringify(row[h]):row[h])).join(','))].join('\n');const blob=new Blob([csv],{type:'text/csv'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`franchiseops-${page}.csv`;a.click();URL.revokeObjectURL(url);};
load().catch(e=>notice(e.message,true));
setInterval(()=>{if(page!=='data')load().catch(e=>notice(e.message,true));},60000);
