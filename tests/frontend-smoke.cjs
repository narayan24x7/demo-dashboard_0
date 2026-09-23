// Dependency-free render smoke test. This is not a real browser or visual test.
const fs=require('node:fs'),vm=require('node:vm'),cp=require('node:child_process'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const python=process.env.PYTHON||'python';
const fixture=JSON.parse(cp.execFileSync(python,['-c',`
import json,tempfile
from pathlib import Path
from franchiseops.db import connect,initialize,rows
from franchiseops.seed import seed
from franchiseops.agents import analyze,run_agents
from franchiseops.imports import SCHEMAS
with tempfile.TemporaryDirectory() as folder:
 db=connect(Path(folder)/'test.db');initialize(db);seed(db);run_agents(db);d=analyze(db)
 d['outlets']=rows(db,'SELECT * FROM outlets');d['runs']=rows(db,'SELECT * FROM runs');d['activity']=[];d['schemas']={k:list(v) for k,v in SCHEMAS.items()}
 d['data_quality']=[{'dataset':k,'rows':db.execute(f'SELECT COUNT(*) FROM {k}').fetchone()[0]} for k in SCHEMAS]
 d['trend']=rows(db,'SELECT outlet_id,date,revenue FROM sales');d['scope']={'milestone_1':['Performance'],'milestone_2':['Inventory'],'milestone_3':['Workforce','Marketing','Operational insights'],'agents':4}
 print(json.dumps(d));db.close()
`],{cwd:root,encoding:'utf8'}));
const elements=new Map();
function element(id){if(!elements.has(id))elements.set(id,{value:id==='dataset'?'franchises':'',innerHTML:'',textContent:'',hidden:false,disabled:false,files:[],onclick:null,onchange:null,onsubmit:null,className:'',addEventListener(){},classList:{toggle(){}},click(){},closest(){return null;}});return elements.get(id);}
const context=vm.createContext({document:{getElementById:element,querySelectorAll:()=>[],createElement:()=>element('download')},setInterval(){},URL,URLSearchParams,Blob,console,fetch:async()=>({ok:true,json:async()=>fixture})});
vm.runInContext(fs.readFileSync(path.join(root,'franchiseops/static/app.js'),'utf8'),context);
context.fixture=fixture;
vm.runInContext(`data=fixture;`,context);
for(const name of ['overview','performance','inventory','staff','marketing','insights','data','testing']){
 vm.runInContext(`page='${name}';render();`,context);
 if(element('content').innerHTML.length<100)throw Error('Empty render: '+name);
 console.log('PASS render '+name);
}
vm.runInContext(`if(esc('<img onerror="x">').includes('<img'))throw Error('HTML escaping failed');`,context);
console.log('PASS HTML escaping');
