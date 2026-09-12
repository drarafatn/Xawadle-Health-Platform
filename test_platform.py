from pathlib import Path
import numpy as np
from src.ingestion import prepare
from src.biostatistics import descriptive, key_metrics, epidemiology_scenarios
from src.benchmarking import classification_metrics, fairness_metrics

DATA=Path(__file__).parents[1]/'data'

def test_quality_and_reconciliation():
    data, report=prepare(DATA)
    assert not report.passed
    assert any(not c['passed'] and 'gender' in c['name'].lower() for c in report.checks)
    assert data['services'].loc[data['services'].indicator=='OPD over 5 years','total'].iloc[0]==450
    assert len(report.missing_fields)>0

def test_descriptive_statistics():
    out=descriptive([1,2,3,4])
    assert out['mean']==2.5 and out['median']==2.5
    assert round(out['std'],6)==round(np.std([1,2,3,4],ddof=1),6)

def test_key_metrics():
    data,_=prepare(DATA); m=key_metrics(data['services'],data['epi'])
    assert m['opd_total']==935
    assert round(m['malnutrition_rate'],3)==0.25

def test_proxy_table_is_labeled():
    data,_=prepare(DATA); out=epidemiology_scenarios(data['services'],data['epi'])
    assert len(out)==2 and 'proxy' in out.iloc[0]['scenario'].lower()

def test_benchmark_metrics_and_fairness():
    y=[1,1,0,0]; p=[1,0,1,0]; g=['F','F','M','M']
    m=classification_metrics(y,p)
    assert m['accuracy']==0.5 and m['sensitivity']==0.5
    f=fairness_metrics(y,p,g)
    assert set(f.group)=={'F','M'}
