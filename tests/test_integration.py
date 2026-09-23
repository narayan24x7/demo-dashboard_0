from pathlib import Path
import json,sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'engine'))
from pipeline import REGISTRY,FILES

def test_all_agents_exported_and_same_outlets():
 meta=json.loads((ROOT/'dist/data/meta.json').read_text())
 assert set(a['id'] for a in meta['agents'])==set(REGISTRY)
 for key in REGISTRY:
  rows=json.loads((ROOT/'dist/data'/f'{key}.json').read_text())
  assert len({r['Outlet_ID'] for r in rows})==750
  assert all(r.get('Region') for r in rows)

def test_no_duplicate_business_keys():
 for key in ['data','inventory','forecast']:
  d=pd.read_csv(FILES[key]);keys=['Outlet_ID','Month']+(['SKU_ID'] if key!='data' else [])
  assert len(d)==30000
  assert not d.duplicated(keys).any()

def test_revenue_reconciles_and_scores_are_bounded():
 sales=pd.read_csv(FILES['data']);bench=pd.read_csv(FILES['benchmark']);scores=pd.read_csv(FILES['score'])
 assert abs(sales.Sales_Revenue_INR.sum()-bench.Total_Sales.sum())<.02
 assert scores.Performance_Score.between(0,100).all()

def test_operational_issue_labels_are_readable():
 d=pd.read_csv(FILES['operations']);issues=d.loc[d.Issue_Count>0,'Detected_Issues']
 assert not issues.isna().any()
 assert not issues.str.contains('True|False').any()
