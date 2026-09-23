import unittest, tempfile, os, io, json, csv, sqlite3
from pathlib import Path
from datetime import date, timedelta
from franchiseops.db import connect, initialize
from franchiseops.seed import seed
from franchiseops.agents import analyze, run_agents
from franchiseops.imports import import_csv
from franchiseops.server import application
from franchiseops.notifications import dispatch

class FranchiseOpsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=Path(self.tmp.name)/'test.db'
        self.old=os.environ.get('FRANCHISEOPS_DB'); os.environ['FRANCHISEOPS_DB']=str(self.path)
        self.db=connect(); initialize(self.db); seed(self.db)
    def tearDown(self):
        self.db.close(); self.tmp.cleanup()
        if self.old is None: os.environ.pop('FRANCHISEOPS_DB',None)
        else: os.environ['FRANCHISEOPS_DB']=self.old
    def request(self,path,method='GET',payload=None,token=None,query=''):
        b=json.dumps(payload or {}).encode(); status=[]
        env={'PATH_INFO':path,'REQUEST_METHOD':method,'CONTENT_LENGTH':str(len(b)),'wsgi.input':io.BytesIO(b),'QUERY_STRING':query,'REMOTE_ADDR':'test'}
        result=b''.join(application(env,lambda s,h:status.append(s)))
        return int(status[0].split()[0]),result
    def test_seed_is_idempotent(self):
        seed(self.db); self.assertEqual(self.db.execute('SELECT count(*) FROM sales').fetchone()[0],540)
    def test_agent_outputs_and_safety_override(self):
        d=analyze(self.db); self.assertEqual(len(d['intelligence']),6)
        rajkot=next(x for x in d['intelligence'] if x['outlet_id']==5)
        self.assertEqual(rajkot['risk'],'High'); self.assertLess(rajkot['score'],80)
    def test_forecast_and_replenishment(self):
        r=next(x for x in analyze(self.db)['inventory'] if x['outlet_id']==2 and x['product']=='Rice (kg)')
        self.assertGreater(r['replenish'],0); self.assertEqual(r['history_days'],28); self.assertAlmostEqual(r['forecast_7d'],r['daily_demand']*7,delta=.1)
    def test_roi_uses_margin(self):
        c=next(x for x in analyze(self.db)['marketing'] if x['outlet_id']==2)
        self.assertEqual(c['roi'],-28); self.assertEqual(c['roas'],1.8)
    def test_zero_spend_and_no_history(self):
        self.db.execute('UPDATE campaigns SET spend=0'); self.db.execute('DELETE FROM movements'); self.db.commit()
        d=analyze(self.db); self.assertIsNone(d['marketing'][0]['roi']); self.assertIsNone(d['inventory'][0]['daily_demand']); json.dumps(d,allow_nan=False)
    def test_empty_dataset_no_fake_scores(self):
        for table in ['sales','movements','inventory','staff','campaigns','audits']: self.db.execute(f'DELETE FROM {table}')
        self.db.commit(); d=analyze(self.db)
        self.assertIsNone(d['intelligence'][0]['score']); self.assertEqual(d['intelligence'][0]['risk'],'No data')
    def test_runs_deduplicate_and_preserve_actions(self):
        run_agents(self.db); count=self.db.execute('SELECT count(*) FROM alerts').fetchone()[0]
        self.db.execute("UPDATE alerts SET status='resolved',owner='Manager',notes='Verified' WHERE id=1"); self.db.commit(); run_agents(self.db)
        self.assertEqual(count,self.db.execute('SELECT count(*) FROM alerts').fetchone()[0]); self.assertEqual(self.db.execute('SELECT status FROM alerts WHERE id=1').fetchone()[0],'resolved')
    def test_escalation(self):
        run_agents(self.db); self.db.execute("UPDATE alerts SET due_date='2000-01-01',severity='medium' WHERE id=1");self.db.commit();run_agents(self.db)
        self.assertEqual(self.db.execute('SELECT severity FROM alerts WHERE id=1').fetchone()[0],'critical')
    def test_csv_transaction_rollback(self):
        old=self.db.execute('SELECT revenue FROM sales WHERE outlet_id=1 ORDER BY date DESC').fetchone()[0]
        content=f'outlet_id,date,revenue,transactions,cost\n1,{date.today()},123,1,20\n999,{date.today()},100,1,20\n'
        with self.assertRaises(sqlite3.IntegrityError): import_csv(self.db,'sales',content)
        self.assertEqual(old,self.db.execute('SELECT revenue FROM sales WHERE outlet_id=1 ORDER BY date DESC').fetchone()[0])
    def test_bad_numbers_rejected(self):
        for val in ['nan','inf','-1']:
            with self.assertRaises(ValueError): import_csv(self.db,'sales',f'outlet_id,date,revenue,transactions,cost\n1,2026-01-01,{val},1,20\n')
    def test_upsert_sales(self):
        content=f'outlet_id,date,revenue,transactions,cost\n1,{date.today()},123,1,20\n'
        import_csv(self.db,'sales',content); import_csv(self.db,'sales',content)
        self.assertEqual(self.db.execute('SELECT count(*) FROM sales').fetchone()[0],540)
        self.assertEqual(self.db.execute('SELECT revenue FROM sales WHERE outlet_id=1 AND date=?',(str(date.today()),)).fetchone()[0],123)
    def test_public_dashboard_and_filters(self):
        code,body=self.request('/api/dashboard',query='outlet=2'); self.assertEqual(code,200)
        d=json.loads(body); self.assertEqual(len(d['performance']),1);self.assertTrue(all(x['outlet_id']==2 for x in d['inventory']))
    def test_invalid_dates_and_unknown_routes(self):
        self.assertEqual(self.request('/api/dashboard',query='start=bad')[0],400)
        self.assertEqual(self.request('/api/missing')[0],404)
    def test_public_agents_and_import(self):
        self.assertEqual(self.request('/api/run','POST')[0],200)
        sample=f'outlet_id,date,revenue,transactions,cost\n1,{date.today()},123,1,20\n'
        code,body=self.request('/api/import','POST',{'dataset':'sales','csv':sample})
        self.assertEqual(code,200); self.assertEqual(json.loads(body)['rows'],1)
    def test_action_requires_closure_evidence(self):
        run_agents(self.db)
        self.assertEqual(self.request('/api/actions','PATCH',{'id':1,'status':'resolved'})[0],400)
        self.assertEqual(self.request('/api/actions','PATCH',{'id':1,'status':'resolved','notes':'Follow-up inspection passed','owner':'Manager'})[0],200)
    def test_latest_audit_replaces_prior_finding(self):
        self.db.execute("INSERT INTO audits(outlet_id,date,category,score,finding,critical) VALUES(5,?,'Food safety',100,'Follow up passed',0)",(str(date.today()),));self.db.commit()
        r=[x for x in analyze(self.db)['audit'] if x['outlet_id']==5 and x['category']=='Food safety'];self.assertEqual(len(r),1);self.assertEqual(r[0]['critical'],0)
    def test_export_formula_escape(self):
        self.db.execute("UPDATE staff SET name='=1+1' WHERE id=1"); self.db.commit()
        code,b=self.request('/api/export',query='dataset=staff');self.assertEqual(code,200);self.assertIn("'=1+1",b.decode())
    def test_notifications_are_not_sent_by_agent_run(self):
        run_agents(self.db)
        self.assertGreater(self.db.execute("SELECT count(*) FROM notifications WHERE channel='email' AND status='pending'").fetchone()[0],0)
    def test_removed_login_routes(self):
        self.assertEqual(self.request('/api/login','POST',{'username':'x','password':'bad'})[0],404)
        self.assertEqual(self.request('/api/logout','POST')[0],404)

    def test_briefing_without_model(self):
        from unittest.mock import patch
        from franchiseops.briefing import brief
        with patch.dict(os.environ, {'OLLAMA_MODEL':''}):
            result=brief(self.db)
        self.assertEqual(result['mode'],'deterministic'); self.assertIn('6 outlets',result['text'])
    def test_model_failure_falls_back(self):
        from unittest.mock import patch
        from franchiseops.briefing import brief
        with patch.dict(os.environ, {'OLLAMA_MODEL':'test'}), patch('urllib.request.urlopen',side_effect=OSError('offline')):
            result=brief(self.db)
        self.assertEqual(result['mode'],'deterministic-fallback')
    def test_model_adapter_parses_response(self):
        from unittest.mock import patch
        from franchiseops.briefing import brief
        response=io.StringIO(json.dumps({'response':'Review the critical food-safety finding.'}))
        with patch.dict(os.environ, {'OLLAMA_MODEL':'test'}), patch('urllib.request.urlopen',return_value=response):
            result=brief(self.db)
        self.assertEqual(result['mode'],'ollama'); self.assertIn('food-safety',result['text'])
    def test_all_dataset_export_import_roundtrip(self):
        from franchiseops.imports import SCHEMAS
        for dataset in SCHEMAS:
            code,body=self.request('/api/export',query='dataset='+dataset)
            self.assertEqual(code,200); self.assertGreater(import_csv(self.db,dataset,body.decode()),0)
    def test_notification_dispatch_disabled(self):
        from unittest.mock import patch
        run_agents(self.db)
        with patch.dict(os.environ, {'SMTP_HOST':'','SMS_WEBHOOK_URL':'','MOBILE_WEBHOOK_URL':''}), patch('urllib.request.urlopen') as network:
            dispatch(self.db);network.assert_not_called()
    def test_public_dashboard_run_and_briefing(self):
        self.assertEqual(self.request('/api/dashboard')[0],200)
        self.assertEqual(self.request('/api/run','POST')[0],200)
        self.assertEqual(self.request('/api/brief','POST')[0],200)

if __name__=='__main__': unittest.main()
