"""Small dependency-free WSGI API. Use a WSGI server behind HTTPS for deployment."""
import csv, io, json, os, secrets, time, threading, sqlite3, hashlib, hmac
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs
from .db import connect, initialize, rows, now, log
from .agents import analyze, run_agents
from .imports import SCHEMAS, import_csv
from .briefing import brief
STATIC=Path(__file__).parent/'static'
SESSIONS={}; ATTEMPTS={}; LOCK=threading.Lock()

def password_ok(value, stored):
    if stored.startswith('pbkdf2$'):
        _,salt,digest=stored.split('$')
        return hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',value.encode(),bytes.fromhex(salt),260000).hex(),digest)
    return hmac.compare_digest(value,stored)

def application(env,start_response):
    def respond(payload,status='200 OK',ctype='application/json',extra=()):
        data=payload if isinstance(payload,bytes) else json.dumps(payload,allow_nan=False).encode()
        start_response(status,[('Content-Type',ctype),('Content-Length',str(len(data))),('X-Content-Type-Options','nosniff'),('Cache-Control','no-store'),('X-Frame-Options','DENY'),('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"),*extra]); return [data]
    path=env.get('PATH_INFO','/'); method=env.get('REQUEST_METHOD','GET')
    if path=='/healthz': return respond({'status':'ok'})
    if path in ('/','/app.js','/style.css'):
        if method!='GET': return respond({'error':'Method not allowed'},'405 Method Not Allowed')
        name='index.html' if path=='/' else path[1:]
        return respond((STATIC/name).read_bytes(),ctype={'html':'text/html; charset=utf-8','js':'text/javascript; charset=utf-8','css':'text/css; charset=utf-8'}[name.split('.')[-1]])
    try:
        size=int(env.get('CONTENT_LENGTH') or 0)
        if size>5_000_000: return respond({'error':'Maximum request size is 5 MB'},'413 Payload Too Large')
        body=json.loads(env['wsgi.input'].read(size)) if size else {}
        if not isinstance(body,dict): raise ValueError('JSON body must be an object')
        if path=='/api/login' and method=='POST':
            ip=env.get('REMOTE_ADDR','local'); t=time.time()
            with LOCK:
                recent=[x for x in ATTEMPTS.get(ip,[]) if t-x<300]; ATTEMPTS[ip]=recent
                if len(recent)>=10: return respond({'error':'Too many attempts. Try again in five minutes.'},'429 Too Many Requests')
                username=str(body.get('username','')); password=str(body.get('password',''))
                role=None
                if username==os.getenv('ADMIN_USER','admin') and password_ok(password,os.getenv('ADMIN_PASSWORD','demo-change-me')): role='admin'
                elif os.getenv('VIEWER_PASSWORD') and username==os.getenv('VIEWER_USER','viewer') and password_ok(password,os.environ['VIEWER_PASSWORD']): role='viewer'
                if not role:
                    recent.append(t); return respond({'error':'Invalid credentials'},'401 Unauthorized')
                for token,session in list(SESSIONS.items()):
                    if session['expires']<t: SESSIONS.pop(token,None)
                token=secrets.token_urlsafe(32); SESSIONS[token]={'role':role,'user':username,'expires':t+8*3600}
            return respond({'token':token,'role':role,'username':username,'demo':not bool(os.getenv('ADMIN_PASSWORD'))})
        token=env.get('HTTP_AUTHORIZATION','').removeprefix('Bearer ')
        session=SESSIONS.get(token)
        if not session or session['expires']<time.time(): return respond({'error':'Please sign in'},'401 Unauthorized')
        if path=='/api/logout' and method=='POST':
            SESSIONS.pop(token,None); return respond({'ok':True})
        if method not in ('GET','POST','PATCH'): return respond({'error':'Method not allowed'},'405 Method Not Allowed')
        if method!='GET' and session['role']!='admin': return respond({'error':'Administrator access required'},'403 Forbidden')
        query={k:v[0] for k,v in parse_qs(env.get('QUERY_STRING','')).items()}
        db=connect()
        try:
            if path=='/api/dashboard' and method=='GET':
                start=query.get('start'); end=query.get('end')
                if start: date.fromisoformat(start)
                if end: date.fromisoformat(end)
                if start and end and start>end: raise ValueError('Start date must be before end date')
                data=analyze(db,start,end)
                allowed={r['outlet_id'] for r in data['performance'] if (not query.get('outlet') or str(r['outlet_id'])==query['outlet']) and (not query.get('region') or r['region']==query['region'])}
                for key in ['performance','inventory','staff','marketing','audit','intelligence']: data[key]=[r for r in data[key] if r['outlet_id'] in allowed]
                data['outlets']=rows(db,'SELECT * FROM outlets'); data['alerts']=[r for r in rows(db,'SELECT a.*,o.name outlet FROM alerts a JOIN outlets o ON o.id=a.outlet_id ORDER BY a.created_at DESC') if r['outlet_id'] in allowed]
                data['trend']=rows(db,'SELECT outlet_id,date,revenue FROM sales WHERE date BETWEEN ? AND ? ORDER BY date',(data['start'],data['end']))
                data['trend']=[r for r in data['trend'] if r['outlet_id'] in allowed]
                data['runs']=rows(db,'SELECT * FROM runs ORDER BY id DESC LIMIT 10')
                data['notifications']=rows(db,'SELECT channel,status,COUNT(*) count FROM notifications GROUP BY channel,status')
                data['activity']=rows(db,'SELECT * FROM activity ORDER BY id DESC LIMIT 30')
                data['schemas']={k:list(v) for k,v in SCHEMAS.items()}
                return respond(data)
            if path=='/api/run' and method=='POST': return respond(run_agents(db))
            if path=='/api/brief' and method=='POST': return respond(brief(db))
            if path=='/api/import' and method=='POST':
                count=import_csv(db,str(body.get('dataset','')),str(body.get('csv',''))); return respond({'rows':count})
            if path=='/api/actions' and method=='PATCH':
                aid=int(body['id']); status=body.get('status','open'); owner=str(body.get('owner','')).strip(); notes=str(body.get('notes','')).strip(); due=body.get('due_date') or None
                if status not in ['open','in_progress','resolved']: raise ValueError('Invalid action status')
                if len(owner)>100 or len(notes)>2000: raise ValueError('Owner or notes too long')
                if due: date.fromisoformat(due)
                if status=='resolved' and not notes: raise ValueError('Add closure evidence in notes before resolving')
                with db:
                    cur=db.execute('UPDATE alerts SET status=?,owner=?,notes=?,due_date=?,resolved_at=? WHERE id=?',(status,owner,notes,due,now() if status=='resolved' else None,aid))
                    if not cur.rowcount: return respond({'error':'Action not found'},'404 Not Found')
                    log(db,'action.update',f"{session['user']}: action {aid} -> {status}")
                return respond({'ok':True})
            if path=='/api/export' and method=='GET':
                dataset=query.get('dataset','sales')
                if dataset not in SCHEMAS: raise ValueError('Unknown dataset')
                records=rows(db,f'SELECT * FROM {dataset}')
                fields=list(SCHEMAS[dataset]); buf=io.StringIO(); writer=csv.writer(buf); writer.writerow(fields)
                for row in records:
                    writer.writerow([("'"+str(row[k])) if isinstance(row[k],str) and row[k].startswith(('=','+','-','@','\t','\r')) else row[k] for k in fields])
                return respond(buf.getvalue().encode(),ctype='text/csv; charset=utf-8',extra=[('Content-Disposition',f'attachment; filename="{dataset}.csv"')])
            return respond({'error':'Not found'},'404 Not Found')
        finally: db.close()
    except (ValueError,KeyError,TypeError,sqlite3.IntegrityError) as e: return respond({'error':str(e)},'400 Bad Request')
    except Exception:
        import traceback; traceback.print_exc()
        return respond({'error':'Internal error; check the server log'},'500 Internal Server Error')
