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
 d['alerts']=rows(db,'SELECT a.*,o.name outlet FROM alerts a JOIN outlets o ON o.id=a.outlet_id')
 d['runs']=rows(db,'SELECT * FROM runs');d['notifications']=[];d['activity']=[];d['schemas']={k:list(v) for k,v in SCHEMAS.items()}
 d['trend']=rows(db,'SELECT * FROM sales');print(json.dumps(d));db.close()
`],{cwd:root,encoding:'utf8'}));
const elements=new Map();
function element(id){if(!elements.has(id))elements.set(id,{value:id==='dataset'?'franchises':id==='action-filter'?'active':'',innerHTML:'',textContent:'',hidden:false,addEventListener(){},classList:{toggle(){}},click(){}});return elements.get(id);}
const context=vm.createContext({document:{getElementById:element,querySelectorAll:()=>[],createElement:()=>element('download')},sessionStorage:{getItem:()=>null,removeItem(){},setItem(){}},setInterval(){},URL,URLSearchParams,Blob,console});
vm.runInContext(fs.readFileSync(path.join(root,'franchiseops/static/app.js'),'utf8'),context);
context.fixture=fixture;
vm.runInContext(`auth={role:'admin',username:'admin'};data=fixture;`,context);
for(const name of ['executive','performance','inventory','staff','marketing','audit','actions','data','methodology']){
 vm.runInContext(`page='${name}';render();`,context);
 if(element('content').innerHTML.length<100)throw Error('Empty render: '+name);
 console.log('PASS render '+name);
}
vm.runInContext(`if(esc('<img onerror="x">').includes('<img'))throw Error('HTML escaping failed');`,context);
console.log('PASS HTML escaping');
