"""Explainable autonomous analytics agents. All scores are heuristics, not trained AI predictions."""
from datetime import date, timedelta
from statistics import mean, pstdev
from .db import rows, now, log
import json, math

def clamp(value): return round(max(0,min(100,value)),1)
def safe(n,d): return n/d if d else 0

def performance(db, start, end):
    span=(date.fromisoformat(end)-date.fromisoformat(start)).days+1
    previous=(date.fromisoformat(start)-timedelta(days=span)).isoformat()
    result=[]
    for o in rows(db,'SELECT * FROM outlets'):
        current=rows(db,'SELECT * FROM sales WHERE outlet_id=? AND date BETWEEN ? AND ? ORDER BY date',(o['id'],start,end))
        prior=rows(db,'SELECT revenue FROM sales WHERE outlet_id=? AND date>=? AND date<?',(o['id'],previous,start))
        rev=sum(r['revenue'] for r in current); cost=sum(r['cost'] for r in current)
        prev=sum(r['revenue'] for r in prior)
        result.append(dict(outlet_id=o['id'],name=o['name'],region=o['region'],revenue=round(rev,2),profit=round(rev-cost,2),transactions=sum(r['transactions'] for r in current),margin=round(safe(rev-cost,rev)*100,1),growth=round((rev/prev-1)*100,1) if prev else None,days=len(current),coverage=round(len(current)/span*100,1)))
    for r in result:
        peers=[x for x in result if x['region']==r['region'] and x['outlet_id']!=r['outlet_id'] and x['days']]
        if not peers: peers=[x for x in result if x['outlet_id']!=r['outlet_id'] and x['days']]
        peer=mean(safe(x['revenue'],x['days']) for x in peers) if peers else None
        r['peer_index']=round(safe(safe(r['revenue'],r['days']),peer)*100,1) if peer else None
        r['score']=clamp(.4*min(100,(r['peer_index'] if r['peer_index'] is not None else 100))+.3*min(100,r['margin']/30*100)+.3*min(100,70+(r['growth'] or 0))) if r['days'] else None
        r['health']='No data' if r['score'] is None else 'Healthy' if r['score']>=80 else 'Watch' if r['score']>=60 else 'At risk'
    return result

def inventory(db, as_of):
    result=[]
    for item in rows(db,'SELECT i.*,o.name outlet FROM inventory i JOIN outlets o ON o.id=i.outlet_id'):
        history=rows(db,'SELECT used,wasted FROM movements WHERE inventory_id=? AND date<=? AND date>=? ORDER BY date',(item['id'],as_of,(date.fromisoformat(as_of)-timedelta(days=27)).isoformat()))
        values=[h['used'] for h in history]
        demand=mean(values) if values else None
        sd=pstdev(values) if len(values)>1 else 0
        safety=1.65*sd*math.sqrt(item['lead_days'])
        target=(demand*(item['lead_days']+7)+safety) if demand is not None else item['reorder_level']
        trigger=max(item['reorder_level'],demand*item['lead_days']+safety) if demand is not None else item['reorder_level']
        shortage=item['quantity']<trigger
        expired=(date.fromisoformat(item['expiry_date'])-date.fromisoformat(as_of)).days
        result.append(dict(item,daily_demand=round(demand,2) if demand is not None else None,forecast_7d=round(demand*7,1) if demand is not None else None,safety_stock=round(safety,1),reorder_point=round(trigger,1),days_cover=round(safe(item['quantity'],demand),1) if demand else None,replenish=max(0,math.ceil(target-item['quantity'])) if shortage else 0,shortage=shortage,waste_pct=round(safe(sum(h['wasted'] for h in history),sum(h['used']+h['wasted'] for h in history))*100,1),expiry_days=expired,history_days=len(values)))
    return result

def staff(db):
    return [dict(r,attendance=round(min(100,safe(r['worked_hours'],r['scheduled_hours'])*100),1),orders_per_hour=round(safe(r['orders'],r['worked_hours']),2),hours_gap=round(max(0,r['scheduled_hours']-r['worked_hours']),1)) for r in rows(db,'SELECT s.*,o.name outlet FROM staff s JOIN outlets o ON o.id=s.outlet_id')]

def marketing(db):
    return [dict(r,roas=round(safe(r['attributed_revenue'],r['spend']),2) if r['spend'] else None,roi=round((r['attributed_revenue']*r['gross_margin']-r['spend'])/r['spend']*100,1) if r['spend'] else None,ctr=round(safe(r['clicks'],r['impressions'])*100,2),conversion=round(safe(r['conversions'],r['clicks'])*100,2)) for r in rows(db,'SELECT c.*,o.name outlet FROM campaigns c JOIN outlets o ON o.id=c.outlet_id')]

def audit(db, as_of):
    # Most recent inspection per outlet and category, with deterministic tie-breaking.
    return rows(db,'''SELECT a.*,o.name outlet FROM audits a JOIN outlets o ON o.id=a.outlet_id
        WHERE a.date<=? AND a.id=(SELECT b.id FROM audits b WHERE b.outlet_id=a.outlet_id AND b.category=a.category AND b.date<=? ORDER BY b.date DESC,b.id DESC LIMIT 1)''',(as_of,as_of))

def analyze(db,start=None,end=None):
    end=end or date.today().isoformat(); start=start or (date.fromisoformat(end)-timedelta(days=29)).isoformat()
    p=performance(db,start,end); i=inventory(db,date.today().isoformat()); s=staff(db); m=marketing(db); a=audit(db,date.today().isoformat())
    intelligence=[]
    for o in p:
        oid=o['outlet_id']; inv=[x for x in i if x['outlet_id']==oid]; team=[x for x in s if x['outlet_id']==oid]; campaigns=[x for x in m if x['outlet_id']==oid and x['roi'] is not None]; audits=[x for x in a if x['outlet_id']==oid]
        components={'performance':o['score'],'inventory':clamp(100-100*safe(sum(x['shortage'] for x in inv),len(inv))) if inv else None,'staff':clamp(mean(x['attendance'] for x in team)) if team else None,'marketing':clamp(mean(70+x['roi']*.3 for x in campaigns)) if campaigns else None,'audit':clamp(mean(x['score'] for x in audits)) if audits else None}
        weights={'performance':.3,'inventory':.2,'staff':.15,'marketing':.15,'audit':.2}
        available=[k for k in components if components[k] is not None]
        score=clamp(sum(components[k]*weights[k] for k in available)/sum(weights[k] for k in available)) if available else None
        critical=any(x['critical'] for x in audits)
        risk='No data' if score is None else 'High' if critical or score<60 else 'Medium' if score<80 else 'Low'
        intelligence.append(dict(outlet_id=oid,name=o['name'],region=o['region'],score=score,risk=risk,components=components,coverage=len(available),opportunity='Resolve safety findings before expansion' if critical else 'Pilot expansion of profitable campaigns' if score is not None and score>=80 else 'Stabilize weak operating areas before increasing spend'))
    return dict(performance=p,inventory=i,staff=s,marketing=m,audit=a,intelligence=intelligence,start=start,end=end,snapshot_date=date.today().isoformat())

def findings(data):
    out=[]
    def add(oid,agent,key,severity,message,recommendation): out.append((oid,agent,key,severity,message,recommendation))
    for r in data['performance']:
        if not r['days']: add(r['outlet_id'],'Performance',f"sales-missing-{r['outlet_id']}",'high','No sales data in the reporting period','Import validated daily sales before interpreting performance.')
        elif r['score']<70 or (r['growth'] is not None and r['growth']<-10): add(r['outlet_id'],'Performance',f"performance-{r['outlet_id']}",'high',f"Revenue trend {r['growth']}%; health {r['score']}/100",'Review daily sales and staffing; create a 7-day recovery plan.')
    for r in data['inventory']:
        if r['shortage']: add(r['outlet_id'],'Inventory',f"stock-{r['id']}",'high',f"{r['product']}: stock {r['quantity']}; reorder point {r['reorder_point']}",f"Order approximately {r['replenish']} units; confirm demand and expiry before purchasing.")
        if r['expiry_days']<=3 and r['quantity']>0: add(r['outlet_id'],'Inventory',f"expiry-{r['id']}",'critical' if r['expiry_days']<0 else 'medium',f"{r['product']}: expires in {r['expiry_days']} days",'Quarantine expired stock; otherwise prioritize first-expiry-first-out usage.')
        if r['waste_pct']>8: add(r['outlet_id'],'Inventory',f"waste-{r['id']}",'medium',f"{r['product']}: waste rate {r['waste_pct']}%",'Reduce batch sizes and inspect storage and handling.')
    for r in data['staff']:
        if r['attendance']<85: add(r['outlet_id'],'Staff',f"staff-{r['id']}",'medium',f"{r['name']}: {r['hours_gap']} uncovered hours",'Discuss availability with the manager and rebalance the shift schedule.')
    for r in data['marketing']:
        if r['roi'] is not None and r['roi']<0: add(r['outlet_id'],'Marketing',f"campaign-{r['id']}",'medium',f"{r['name']}: contribution ROI {r['roi']}%",'Review attribution, audience and offer; test a smaller budget before scaling.')
    for r in data['audit']:
        if r['critical'] or r['score']<80: add(r['outlet_id'],'Audit',f"audit-{r['outlet_id']}-{r['category']}",'critical' if r['critical'] else 'medium',f"{r['category']}: {r['finding']}",'Assign a corrective action and verify closure with a follow-up inspection.')
    return out

def run_agents(db):
    timestamp=now()
    cur=db.execute('INSERT INTO runs(started_at,status) VALUES(?,?)',(timestamp,'running')); run_id=cur.lastrowid
    data=analyze(db); found=findings(data); active_keys=[]
    for oid,agent,key,severity,message,recommendation in found:
        active_keys.append(key)
        due=(date.today()+timedelta(days=1 if severity=='critical' else 3 if severity=='high' else 7)).isoformat()
        db.execute('''INSERT INTO alerts(outlet_id,agent,alert_key,severity,message,recommendation,created_at,last_seen,due_date) VALUES(?,?,?,?,?,?,?,?,?)
        ON CONFLICT(alert_key) DO UPDATE SET severity=excluded.severity,message=excluded.message,recommendation=excluded.recommendation,last_seen=excluded.last_seen''',(oid,agent,key,severity,message,recommendation,timestamp,timestamp,due))
        alert=db.execute('SELECT id,status FROM alerts WHERE alert_key=?',(key,)).fetchone()
        if alert['status']!='resolved':
            for channel in ['in_app','email','sms','mobile']:
                db.execute('INSERT OR IGNORE INTO notifications(alert_id,channel,status,created_at) VALUES(?,?,?,?)',(alert['id'],channel,'delivered' if channel=='in_app' else 'pending',timestamp))
    # Closed actions stay closed until a manager explicitly reopens them. Findings remain visible.
    db.execute("UPDATE alerts SET severity='critical' WHERE status!='resolved' AND due_date<?",(date.today().isoformat(),))
    summary={'findings':len(found),'outlets':len(data['performance']),'agents':5,'engine':'rules-and-statistics'}
    db.execute('UPDATE runs SET status=?,finished_at=?,summary=? WHERE id=?',('completed',now(),json.dumps(summary),run_id))
    log(db,'agents.run',json.dumps(summary)); db.commit()
    return dict(id=run_id,**summary)
