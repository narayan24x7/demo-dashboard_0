"""Opt-in delivery adapters. Never called by the browser or agent analysis itself."""
import os, json, smtplib, urllib.request
from email.message import EmailMessage
from .db import rows, now

def dispatch(db):
    for n in rows(db,"SELECT n.*,a.message,a.recommendation,a.severity,a.status alert_status FROM notifications n JOIN alerts a ON a.id=n.alert_id WHERE n.status IN ('pending','failed') AND n.attempts<3 AND n.channel!='in_app'"):
        if n['alert_status']=='resolved':
            db.execute("UPDATE notifications SET status='cancelled' WHERE id=?",(n['id'],)); continue
        enabled=(os.getenv('SMTP_HOST') and os.getenv('NOTIFY_EMAIL')) if n['channel']=='email' else os.getenv(n['channel'].upper()+'_WEBHOOK_URL')
        if not enabled: continue
        try:
            if n['channel']=='email':
                message=EmailMessage(); message['Subject']=f"FranchiseOps | {n['severity'].upper()} alert"; message['From']=os.environ['SMTP_FROM']; message['To']=os.environ['NOTIFY_EMAIL']; message.set_content(n['message']+'\n\n'+n['recommendation'])
                with smtplib.SMTP(os.environ['SMTP_HOST'],int(os.getenv('SMTP_PORT','587')),timeout=15) as smtp:
                    smtp.starttls()
                    if os.getenv('SMTP_USERNAME'): smtp.login(os.environ['SMTP_USERNAME'],os.environ['SMTP_PASSWORD'])
                    smtp.send_message(message)
            else:
                url=os.environ[n['channel'].upper()+'_WEBHOOK_URL']
                if not url.startswith('https://'): raise ValueError('Notification webhooks require HTTPS')
                payload=json.dumps({'idempotency_key':f"notification-{n['id']}",'channel':n['channel'],'message':n['message'],'recommendation':n['recommendation'],'severity':n['severity']}).encode()
                headers={'Content-Type':'application/json','Idempotency-Key':f"notification-{n['id']}"}
                if os.getenv('NOTIFY_WEBHOOK_TOKEN'): headers['Authorization']='Bearer '+os.environ['NOTIFY_WEBHOOK_TOKEN']
                with urllib.request.urlopen(urllib.request.Request(url,payload,headers),timeout=15) as response:
                    if response.status>=300: raise ValueError('Delivery rejected')
            db.execute("UPDATE notifications SET status='delivered',attempts=attempts+1,sent_at=?,error='' WHERE id=?",(now(),n['id']))
        except Exception as e:
            db.execute("UPDATE notifications SET status='failed',attempts=attempts+1,error=? WHERE id=?",(type(e).__name__,n['id']))
    db.commit()
