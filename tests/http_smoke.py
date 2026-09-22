"""Launch the real server with an isolated DB, exercise HTTP, then cleanly stop it."""
import subprocess,sys,os,tempfile,time,json,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory() as d:
 env=dict(os.environ,FRANCHISEOPS_DB=str(Path(d)/'test.db'))
 for name in ['ADMIN_PASSWORD','ADMIN_USER','OLLAMA_MODEL']: env.pop(name,None)
 process=subprocess.Popen([sys.executable,str(root/'run.py'),'--port','18761'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 try:
  base='http://127.0.0.1:18761'
  for _ in range(50):
   try:
    with urllib.request.urlopen(base+'/healthz',timeout=1) as r: assert json.load(r)['status']=='ok'
    break
   except OSError: time.sleep(.1)
  else: raise RuntimeError('Server did not start')
  req=urllib.request.Request(base+'/api/login',json.dumps({'username':'admin','password':'demo-change-me'}).encode(),{'Content-Type':'application/json'})
  with urllib.request.urlopen(req) as r: token=json.load(r)['token']
  headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'}
  for path in ['/api/dashboard','/api/dashboard?outlet=2']:
   with urllib.request.urlopen(urllib.request.Request(base+path,headers=headers)) as r:
    result=json.load(r); assert len(result['performance'])==(1 if '?' in path else 6)
  for path in ['/api/run','/api/brief']:
   with urllib.request.urlopen(urllib.request.Request(base+path,b'{}',headers)) as r: assert r.status==200
  for path in ['/','/app.js','/style.css']:
   with urllib.request.urlopen(base+path) as r: assert r.status==200
  print('PASS real HTTP: health, login, dashboard, outlet filter, orchestration, briefing, HTML/JS/CSS')
 finally:
  process.terminate(); process.communicate(timeout=10)
