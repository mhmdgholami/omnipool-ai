from __future__ import annotations
import hashlib,time
from backend.db import db
from backend.models import TrendFeatures
from backend.quant.scoring import compute_trend_score,freshness_score,saturation_score
from backend.services.dexscreener import dex_adapter

SEEDS=[
 ('Robot Boxing','Humanoid fighting clips moving from robotics circles into meme culture.',90,78,93,12,88),
 ('Tiny Mic Interviews','Tiny microphone interviews mutating into a reusable reaction format.',80,70,86,17,82),
 ('AI Pigeon','An AI-agent pigeon joke spreading through profile pictures and replies.',76,68,91,9,84),
]

def _id(source,title): return hashlib.blake2s(f'{source}:{title}'.encode(),digest_size=8).hexdigest()
def _trend(title,summary,source,velocity,cross,novelty,saturation,memeability):
    ts=time.time(); f=TrendFeatures(velocity,min(100,45+velocity*.35),cross,novelty,saturation,memeability,freshness_score(12))
    return {'id':_id(source,title),'title':title,'summary':summary,'source':source,'score':compute_trend_score(f),'velocity':f.velocity,'acceleration':f.acceleration,'cross_source':f.cross_source,'novelty':f.novelty,'saturation':f.saturation,'memeability':f.memeability,'freshness':f.freshness,'created_at':ts,'updated_at':ts}

async def scan_trends():
    for title,summary,v,c,n,s,m in SEEDS:
        db.upsert_trend(_trend(title,summary,'demo_culture',v,c,n,s,m))
    for i,item in enumerate((await dex_adapter.scan())[:20]):
        db.upsert_trend(_trend(item['title'] or 'Solana signal',item['summary'],'dexscreener',max(40,88-i*2),35,max(45,78-i),saturation_score(i//4),60))
    return list_trends(30)

def list_trends(limit=30):
    return db.rows('SELECT * FROM trends ORDER BY score DESC,updated_at DESC LIMIT ?',(min(max(int(limit),1),100),))
