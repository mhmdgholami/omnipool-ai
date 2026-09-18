from __future__ import annotations
import json, sqlite3, threading, time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4
from backend.config import settings

class Database:
    """SQLite store with bounded result sizes and short-lived connections."""
    def __init__(self, path: str | None = None) -> None:
        self.path = path or settings.database_path
        self._write_lock = threading.Lock()
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def conn(self):
        c = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        try:
            yield c
        finally:
            c.close()

    def init(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS trends (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, summary TEXT NOT NULL, source TEXT NOT NULL,
          score REAL NOT NULL, velocity REAL NOT NULL, acceleration REAL NOT NULL, cross_source REAL NOT NULL,
          novelty REAL NOT NULL, saturation REAL NOT NULL, memeability REAL NOT NULL, freshness REAL NOT NULL,
          created_at REAL NOT NULL, updated_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS concepts (
          id TEXT PRIMARY KEY, trend_id TEXT NOT NULL, name TEXT NOT NULL, ticker TEXT NOT NULL, thesis TEXT NOT NULL,
          visual_prompt TEXT NOT NULL, target_sol REAL NOT NULL, novelty_score REAL NOT NULL, momentum_score REAL NOT NULL,
          saturation_score REAL NOT NULL, risk_flags TEXT NOT NULL, created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS campaigns (
          id TEXT PRIMARY KEY, concept_id TEXT NOT NULL, creator_wallet TEXT NOT NULL, name TEXT NOT NULL, ticker TEXT NOT NULL,
          thesis TEXT NOT NULL, target_sol REAL NOT NULL, raised_sol REAL NOT NULL DEFAULT 0, status TEXT NOT NULL,
          expires_at REAL NOT NULL, created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS contributions (
          id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL, wallet TEXT NOT NULL, amount_sol REAL NOT NULL,
          status TEXT NOT NULL, created_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_trends_score ON trends(score DESC);
        CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
        CREATE INDEX IF NOT EXISTS idx_contrib_campaign ON contributions(campaign_id);
        """
        with self.conn() as c:
            c.executescript(schema)

    def rows(self, sql: str, params: tuple = ()) -> list[dict]:
        with self.conn() as c:
            return [dict(r) for r in c.execute(sql, params).fetchall()]

    def row(self, sql: str, params: tuple = ()) -> dict | None:
        with self.conn() as c:
            r = c.execute(sql, params).fetchone()
            return dict(r) if r else None

    def execute(self, sql: str, params: tuple = ()) -> None:
        with self._write_lock, self.conn() as c:
            c.execute("BEGIN IMMEDIATE")
            c.execute(sql, params)
            c.execute("COMMIT")

    def upsert_trend(self, t: dict) -> None:
        self.execute(
            """INSERT INTO trends VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET title=excluded.title,summary=excluded.summary,source=excluded.source,
            score=excluded.score,velocity=excluded.velocity,acceleration=excluded.acceleration,cross_source=excluded.cross_source,
            novelty=excluded.novelty,saturation=excluded.saturation,memeability=excluded.memeability,freshness=excluded.freshness,
            updated_at=excluded.updated_at""",
            (t['id'],t['title'],t['summary'],t['source'],t['score'],t['velocity'],t['acceleration'],t['cross_source'],
             t['novelty'],t['saturation'],t['memeability'],t['freshness'],t['created_at'],t['updated_at'])
        )

    def insert_concept(self, c: dict) -> None:
        self.execute(
            "INSERT OR REPLACE INTO concepts VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (c['id'],c['trend_id'],c['name'],c['ticker'],c['thesis'],c['visual_prompt'],c['target_sol'],
             c['novelty_score'],c['momentum_score'],c['saturation_score'],json.dumps(c['risk_flags']),c['created_at'])
        )

    def create_campaign(self, concept: dict, creator_wallet: str, duration_minutes: int) -> dict:
        campaign = {
            'id': str(uuid4()), 'concept_id': concept['id'], 'creator_wallet': creator_wallet,
            'name': concept['name'], 'ticker': concept['ticker'], 'thesis': concept['thesis'],
            'target_sol': float(concept['target_sol']), 'raised_sol': 0.0, 'status': 'funding',
            'expires_at': time.time() + duration_minutes * 60, 'created_at': time.time()
        }
        self.execute("INSERT INTO campaigns VALUES(?,?,?,?,?,?,?,?,?,?,?)", tuple(campaign.values()))
        return campaign

    def contribute(self, campaign_id: str, wallet: str, amount_sol: float) -> dict:
        with self._write_lock, self.conn() as c:
            c.execute("BEGIN IMMEDIATE")
            row = c.execute("SELECT * FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
            if not row:
                c.execute("ROLLBACK"); raise KeyError("campaign_not_found")
            campaign = dict(row)
            if campaign['status'] != 'funding':
                c.execute("ROLLBACK"); raise ValueError("campaign_not_funding")
            if campaign['expires_at'] <= time.time():
                c.execute("UPDATE campaigns SET status='expired' WHERE id=?", (campaign_id,))
                c.execute("COMMIT"); raise ValueError("campaign_expired")
            accepted = min(float(amount_sol), max(0.0, campaign['target_sol'] - campaign['raised_sol']))
            if accepted <= 0:
                c.execute("ROLLBACK"); raise ValueError("target_reached")
            c.execute("INSERT INTO contributions VALUES(?,?,?,?,?,?)", (str(uuid4()),campaign_id,wallet,accepted,'committed',time.time()))
            raised = campaign['raised_sol'] + accepted
            status = 'ready' if raised + 1e-9 >= campaign['target_sol'] else 'funding'
            c.execute("UPDATE campaigns SET raised_sol=?,status=? WHERE id=?", (raised,status,campaign_id))
            c.execute("COMMIT")
        return self.row("SELECT * FROM campaigns WHERE id=?", (campaign_id,)) or {}

db = Database()
