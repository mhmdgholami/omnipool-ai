from __future__ import annotations
import json,re,time
from uuid import uuid4
import httpx
from backend.config import settings
from backend.db import db

def _ticker(name):
    clean=re.sub(r'[^A-Za-z0-9]','',name).upper()
    return (clean or 'IDEA')[:8]

def _fallback(trend):
    base=trend['title'].split()[0].title(); names=[f'{base} Mode',f'Proof of {base}',f'{base} Signal']; out=[]
    for i,name in enumerate(names):
        out.append({'id':str(uuid4()),'trend_id':trend['id'],'name':name,'ticker':_ticker(name),'thesis':f"A community launch around {trend['title'].lower()} that proves demand before a tradable token exists.",'visual_prompt':f'Minimal internet-native symbol for {name}, dark background, high contrast, no text','target_sol':[25,40,60][i],'novelty_score':max(50,trend.get('novelty',80)-i*4),'momentum_score':max(50,trend.get('score',75)-i*3),'saturation_score':min(100,trend.get('saturation',15)+i*4),'risk_flags':['demo_generation'],'created_at':time.time()})
    return out

def _extract_text(payload):
    parts=[]
    for item in payload.get('output',[]):
        if not isinstance(item,dict): continue
        for content in item.get('content',[]):
            if content.get('type')=='output_text' and content.get('text'): parts.append(content['text'])
    return ''.join(parts)

async def generate_concepts(trend):
    if not settings.openai_api_key:
        concepts=_fallback(trend)
    else:
        prompt=("Return ONLY a JSON array of exactly 3 launch concepts. Keys: name,ticker,thesis,visual_prompt,target_sol,novelty_score,momentum_score,saturation_score,risk_flags. "
                "No guaranteed-profit language, no impersonation, ticker max 8 alphanumeric chars, target_sol 5-250.
"
                f"Trend: {trend['title']}
Summary: {trend['summary']}
Momentum: {trend.get('score',75)}
Saturation: {trend.get('saturation',15)}")
        timeout=httpx.Timeout(15.0,connect=4.0)
        async with httpx.AsyncClient(timeout=timeout,limits=httpx.Limits(max_connections=2,max_keepalive_connections=1)) as client:
            r=await client.post('https://api.openai.com/v1/responses',headers={'Authorization':f'Bearer {settings.openai_api_key}','Content-Type':'application/json'},json={'model':settings.openai_model,'input':prompt})
            r.raise_for_status(); raw=_extract_text(r.json()).strip()
        try: data=json.loads(raw)
        except json.JSONDecodeError:
            m=re.search(r'\[.*\]',raw,re.S); data=json.loads(m.group(0)) if m else []
        concepts=[]
        for item in data[:3]:
            concepts.append({'id':str(uuid4()),'trend_id':trend['id'],'name':str(item.get('name','Idea'))[:48],'ticker':_ticker(str(item.get('ticker') or item.get('name','IDEA'))),'thesis':str(item.get('thesis',''))[:500],'visual_prompt':str(item.get('visual_prompt',''))[:500],'target_sol':min(250,max(5,float(item.get('target_sol',40)))),'novelty_score':min(100,max(0,float(item.get('novelty_score',trend.get('novelty',80))))),'momentum_score':min(100,max(0,float(item.get('momentum_score',trend.get('score',75))))),'saturation_score':min(100,max(0,float(item.get('saturation_score',trend.get('saturation',15))))),'risk_flags':[str(x)[:80] for x in item.get('risk_flags',[])][:8],'created_at':time.time()})
        if len(concepts)!=3: concepts=_fallback(trend)
    for c in concepts: db.insert_concept(c)
    return concepts
