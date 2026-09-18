from __future__ import annotations
import resource,time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.config import settings
from backend.db import db
from backend.models import CampaignCreate,ContributionCreate,GenerateRequest
from backend.services.ai import generate_concepts
from backend.services.campaigns import graduate,list_campaigns,refund
from backend.services.trends import list_trends,scan_trends
from backend.services.sources import source_status
from backend.solana.adapter import build_graduation_plan

ROOT=Path(__file__).resolve().parents[1]; FRONTEND=ROOT/'frontend'
@asynccontextmanager
async def lifespan(app):
    db.init()
    try: await scan_trends()
    except Exception: pass
    yield
app=FastAPI(title='OMNIPOOL AI',version='0.1.0',lifespan=lifespan,docs_url='/api/docs')
app.mount('/static',StaticFiles(directory=FRONTEND),name='static')
@app.get('/')
def index(): return FileResponse(FRONTEND/'index.html')
@app.get('/api/health')
def health():
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {'ok':True,'env':settings.app_env,'rss_mb':round(rss/1024,2),'time':time.time()}
@app.get('/api/trends')
def trends(limit:int=30): return list_trends(limit)
@app.get('/api/sources')
def sources(): return source_status()
@app.post('/api/trends/scan')
async def scan(): return await scan_trends()
@app.post('/api/generate')
async def generate(req:GenerateRequest):
    trend=db.row('SELECT * FROM trends WHERE id=?',(req.trend_id,)) if req.trend_id else None
    if not trend and req.title: trend={'id':f'custom-{int(time.time()*1000)}','title':req.title[:80],'summary':(req.summary or req.title)[:300],'score':75.,'novelty':80.,'saturation':15.}
    if not trend: raise HTTPException(404,'trend_not_found')
    try: return await generate_concepts(trend)
    except Exception as e: raise HTTPException(502,f'generation_failed:{type(e).__name__}')
@app.get('/api/campaigns')
def campaigns(): return list_campaigns()
@app.post('/api/campaigns')
def create_campaign(req:CampaignCreate):
    c=db.row('SELECT * FROM concepts WHERE id=?',(req.concept_id,))
    if not c: raise HTTPException(404,'concept_not_found')
    return db.create_campaign(c,req.creator_wallet,req.duration_minutes)
@app.post('/api/campaigns/{campaign_id}/contribute')
def contribute(campaign_id:str,req:ContributionCreate):
    try: return db.contribute(campaign_id,req.wallet,req.amount_sol)
    except KeyError as e: raise HTTPException(404,str(e))
    except ValueError as e: raise HTTPException(409,str(e))
@app.post('/api/campaigns/{campaign_id}/graduate')
def graduate_route(campaign_id:str):
    try: return {'campaign':graduate(campaign_id),'plan':build_graduation_plan(campaign_id)}
    except KeyError as e: raise HTTPException(404,str(e))
    except ValueError as e: raise HTTPException(409,str(e))
@app.post('/api/campaigns/{campaign_id}/refund/{wallet}')
def refund_route(campaign_id:str,wallet:str):
    try: return refund(campaign_id,wallet)
    except KeyError as e: raise HTTPException(404,str(e))
    except ValueError as e: raise HTTPException(409,str(e))
