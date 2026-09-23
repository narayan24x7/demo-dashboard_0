"""Local dashboard server; no Streamlit or frontend build required."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import json,threading,uuid,os
from pipeline import ROOT,run,REGISTRY
lock=threading.Lock();jobs={}
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT/'dist'),**kw)
 def reply(self,obj,status=200):
  b=json.dumps(obj).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
 def do_GET(self):
  p=urlparse(self.path).path
  if p=='/api/status':return self.reply({'mode':'live','agents':list(REGISTRY)})
  if p.startswith('/api/jobs/'):return self.reply(jobs.get(p.rsplit('/',1)[-1],{'status':'unknown'}))
  return super().do_GET()
 def do_POST(self):
  origin=self.headers.get('Origin')
  if origin and urlparse(origin).netloc!=self.headers.get('Host'):return self.reply({'error':'Origin not allowed'},403)
  if not self.path.startswith('/api/run/'):return self.reply({'error':'Not found'},404)
  key=self.path.rsplit('/',1)[-1]
  if key!='all' and key not in REGISTRY:return self.reply({'error':'Unknown agent'},400)
  if not lock.acquire(blocking=False):return self.reply({'error':'An agent is already running. Please wait.'},409)
  jid=uuid.uuid4().hex;jobs[jid]={'status':'running','agent':key}
  def task():
   try:jobs[jid]={'status':'succeeded','agents':run(key)}
   except Exception as e:jobs[jid]={'status':'failed','error':str(e)}
   finally:lock.release()
  threading.Thread(target=task,daemon=True).start();return self.reply({'job':jid},202)
if __name__=='__main__':
 port=int(os.environ.get('PORT','8000'));host=os.environ.get('HOST','127.0.0.1')
 print(f'FranchiseOps AI: http://{host}:{port}',flush=True)
 ThreadingHTTPServer((host,port),Handler).serve_forever()
