import json,threading,urllib.request,urllib.error
from http.server import ThreadingHTTPServer
import server

def test_api_boundary_and_dashboard_assets():
 http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
 t=threading.Thread(target=http.serve_forever,daemon=True);t.start()
 base=f'http://127.0.0.1:{http.server_port}'
 try:
  with urllib.request.urlopen(base+'/api/status') as r:assert json.load(r)['mode']=='live'
  with urllib.request.urlopen(base+'/') as r:assert b'FranchiseOps AI' in r.read()
  for route,headers,code in [('/api/run/unknown',{},400),('/api/run/all',{'Origin':'https://untrusted.example'},403)]:
   req=urllib.request.Request(base+route,data=b'',headers=headers,method='POST')
   try:urllib.request.urlopen(req);assert False
   except urllib.error.HTTPError as e:assert e.code==code
 finally:http.shutdown();http.server_close()
