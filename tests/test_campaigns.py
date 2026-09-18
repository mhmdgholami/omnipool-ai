from pathlib import Path
import time
from backend.db import Database

def concept():
    return {'id':'c1','trend_id':'t','name':'Test','ticker':'TEST','thesis':'x','visual_prompt':'x','target_sol':2.0,'novelty_score':80,'momentum_score':80,'saturation_score':10,'risk_flags':[],'created_at':0.0}

def test_campaign_reaches_ready_without_overfunding(tmp_path: Path):
    d=Database(str(tmp_path/'x.db')); d.init(); cpt=concept(); d.insert_concept(cpt)
    c=d.create_campaign(cpt,'wallet',30)
    assert d.contribute(c['id'],'w1',1)['status']=='funding'
    ready=d.contribute(c['id'],'w2',9)
    assert ready['status']=='ready' and ready['raised_sol']==2.0
    rows=d.rows("SELECT * FROM contributions WHERE campaign_id=?",(c['id'],))
    assert round(sum(r['amount_sol'] for r in rows),9)==2.0

def test_expired_campaign_rejects_contribution(tmp_path: Path):
    d=Database(str(tmp_path/'x.db')); d.init(); cpt=concept(); d.insert_concept(cpt)
    c=d.create_campaign(cpt,'wallet',30)
    d.execute("UPDATE campaigns SET expires_at=? WHERE id=?",(time.time()-1,c['id']))
    try: d.contribute(c['id'],'w1',1)
    except ValueError as e: assert str(e)=='campaign_expired'
    else: raise AssertionError('expected campaign_expired')
