from __future__ import annotations
import sys,time,tracemalloc
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.models import TrendFeatures
from backend.quant.scoring import compute_trend_score
f=TrendFeatures(80,70,75,88,12,82,91)
tracemalloc.start(); started=time.perf_counter()
for _ in range(250_000): compute_trend_score(f)
elapsed=time.perf_counter()-started
_,peak=tracemalloc.get_traced_memory()
print({'iterations':250000,'seconds':round(elapsed,3),'peak_mb':round(peak/1024/1024,3)})
