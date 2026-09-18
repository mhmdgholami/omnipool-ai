from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from backend.config import settings
from backend.domain.money import lamports_to_sol, sol_to_lamports


class Database:
    """Small transactional store for the single-node alpha.

    SQLite is intentionally limited to one application replica. The cloud scaling
    path in ARCHITECTURE.md moves this interface to PostgreSQL before horizontal
    API scaling.
    """

    def __init__(self, path: str | None = None) -> None:
        self.path = path or settings.database_path
        self._write_lock = threading.Lock()
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def conn(self):
        connection = sqlite3.connect(self.path, timeout=5.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")
        try:
            yield connection
        finally:
            connection.close()

    def init(self) -> None:
        with self._write_lock, self.conn() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=NORMAL")
            self._create_tables(connection)
            self._upgrade_schema(connection)
            connection.execute("PRAGMA user_version=3")

    def _create_tables(self, connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS trends (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                source TEXT NOT NULL,
                score REAL NOT NULL,
                confidence REAL NOT NULL DEFAULT 0,
                risk REAL NOT NULL DEFAULT 0,
                velocity REAL NOT NULL,
                acceleration REAL NOT NULL,
                cross_source REAL NOT NULL,
                novelty REAL NOT NULL,
                saturation REAL NOT NULL,
                memeability REAL NOT NULL,
                freshness REAL NOT NULL,
                evidence_count INTEGER NOT NULL DEFAULT 1,
                source_count INTEGER NOT NULL DEFAULT 1,
                risk_flags TEXT NOT NULL DEFAULT '[]',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS concepts (
                id TEXT PRIMARY KEY,
                trend_id TEXT NOT NULL,
                name TEXT NOT NULL,
                ticker TEXT NOT NULL,
                thesis TEXT NOT NULL,
                visual_prompt TEXT NOT NULL,
                target_sol REAL NOT NULL,
                novelty_score REAL NOT NULL,
                momentum_score REAL NOT NULL,
                saturation_score REAL NOT NULL,
                risk_flags TEXT NOT NULL,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                concept_id TEXT NOT NULL,
                creator_wallet TEXT NOT NULL,
                name TEXT NOT NULL,
                ticker TEXT NOT NULL,
                thesis TEXT NOT NULL,
                target_lamports INTEGER NOT NULL,
                raised_lamports INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                expires_at REAL NOT NULL,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS contributions (
                id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                wallet TEXT NOT NULL,
                amount_lamports INTEGER NOT NULL,
                idempotency_key TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_trends_score
                ON trends(score DESC);
            CREATE INDEX IF NOT EXISTS idx_campaigns_status
                ON campaigns(status, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_contributions_campaign
                ON contributions(campaign_id, status);
            """
        )

    @staticmethod
    def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
        return {
            str(row["name"])
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }

    @staticmethod
    def _add_column(
        connection: sqlite3.Connection,
        table: str,
        definition: str,
    ) -> None:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")

    def _upgrade_schema(self, connection: sqlite3.Connection) -> None:
        trend_columns = self._columns(connection, "trends")
        trend_additions = {
            "confidence": "confidence REAL NOT NULL DEFAULT 0",
            "risk": "risk REAL NOT NULL DEFAULT 0",
            "evidence_count": "evidence_count INTEGER NOT NULL DEFAULT 1",
            "source_count": "source_count INTEGER NOT NULL DEFAULT 1",
            "risk_flags": "risk_flags TEXT NOT NULL DEFAULT '[]'",
        }
        for name, definition in trend_additions.items():
            if name not in trend_columns:
                self._add_column(connection, "trends", definition)

        campaign_columns = self._columns(connection, "campaigns")
        if "target_lamports" not in campaign_columns and "target_sol" in campaign_columns:
            self._add_column(
                connection,
                "campaigns",
                "target_lamports INTEGER NOT NULL DEFAULT 0",
            )
            self._add_column(
                connection,
                "campaigns",
                "raised_lamports INTEGER NOT NULL DEFAULT 0",
            )
            connection.execute(
                """
                UPDATE campaigns
                SET target_lamports = CAST(ROUND(target_sol * 1000000000) AS INTEGER),
                    raised_lamports = CAST(ROUND(raised_sol * 1000000000) AS INTEGER)
                """
            )

        contribution_columns = self._columns(connection, "contributions")
        if "amount_lamports" not in contribution_columns and "amount_sol" in contribution_columns:
            self._add_column(
                connection,
                "contributions",
                "amount_lamports INTEGER NOT NULL DEFAULT 0",
            )
            connection.execute(
                """
                UPDATE contributions
                SET amount_lamports = CAST(ROUND(amount_sol * 1000000000) AS INTEGER)
                """
            )

        contribution_columns = self._columns(connection, "contributions")
        if "idempotency_key" not in contribution_columns:
            self._add_column(connection, "contributions", "idempotency_key TEXT")
            connection.execute(
                """
                UPDATE contributions
                SET idempotency_key = 'legacy:' || id
                WHERE idempotency_key IS NULL
                """
            )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_contributions_idempotency
            ON contributions(idempotency_key)
            """
        )

    def rows(self, sql: str, params: tuple = ()) -> list[dict]:
        with self.conn() as connection:
            return [dict(row) for row in connection.execute(sql, params).fetchall()]

    def row(self, sql: str, params: tuple = ()) -> dict | None:
        with self.conn() as connection:
            result = connection.execute(sql, params).fetchone()
            return dict(result) if result else None

    def execute(self, sql: str, params: tuple = ()) -> None:
        with self._write_lock, self.conn() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(sql, params)
            except Exception:
                connection.execute("ROLLBACK")
                raise
            else:
                connection.execute("COMMIT")

    def upsert_trend(self, trend: dict) -> None:
        self.execute(
            """
            INSERT INTO trends (
                id, title, summary, source, score, confidence, risk,
                velocity, acceleration, cross_source, novelty, saturation,
                memeability, freshness, evidence_count, source_count,
                risk_flags, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                summary=excluded.summary,
                source=excluded.source,
                score=excluded.score,
                confidence=excluded.confidence,
                risk=excluded.risk,
                velocity=excluded.velocity,
                acceleration=excluded.acceleration,
                cross_source=excluded.cross_source,
                novelty=excluded.novelty,
                saturation=excluded.saturation,
                memeability=excluded.memeability,
                freshness=excluded.freshness,
                evidence_count=excluded.evidence_count,
                source_count=excluded.source_count,
                risk_flags=excluded.risk_flags,
                updated_at=excluded.updated_at
            """,
            (
                trend["id"],
                trend["title"],
                trend["summary"],
                trend["source"],
                trend["score"],
                trend.get("confidence", 0.0),
                trend.get("risk", 0.0),
                trend["velocity"],
                trend["acceleration"],
                trend["cross_source"],
                trend["novelty"],
                trend["saturation"],
                trend["memeability"],
                trend["freshness"],
                trend.get("evidence_count", 1),
                trend.get("source_count", 1),
                json.dumps(trend.get("risk_flags", []), separators=(",", ":")),
                trend["created_at"],
                trend["updated_at"],
            ),
        )

    def insert_concept(self, concept: dict) -> None:
        self.execute(
            """
            INSERT OR REPLACE INTO concepts (
                id, trend_id, name, ticker, thesis, visual_prompt,
                target_sol, novelty_score, momentum_score,
                saturation_score, risk_flags, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                concept["id"],
                concept["trend_id"],
                concept["name"],
                concept["ticker"],
                concept["thesis"],
                concept["visual_prompt"],
                concept["target_sol"],
                concept["novelty_score"],
                concept["momentum_score"],
                concept["saturation_score"],
                json.dumps(concept["risk_flags"], separators=(",", ":")),
                concept["created_at"],
            ),
        )

    @staticmethod
    def _campaign_to_public(row: sqlite3.Row | dict) -> dict:
        data = dict(row)
        target_lamports = int(data.pop("target_lamports"))
        raised_lamports = int(data.pop("raised_lamports"))
        data["target_sol"] = lamports_to_sol(target_lamports)
        data["raised_sol"] = lamports_to_sol(raised_lamports)
        return data

    def create_campaign(
        self,
        concept: dict,
        creator_wallet: str,
        duration_minutes: int,
    ) -> dict:
        created_at = time.time()
        campaign_id = str(uuid4())
        target_lamports = sol_to_lamports(Decimal(str(concept["target_sol"])))

        self.execute(
            """
            INSERT INTO campaigns (
                id, concept_id, creator_wallet, name, ticker, thesis,
                target_lamports, raised_lamports, status, expires_at, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'funding', ?, ?)
            """,
            (
                campaign_id,
                concept["id"],
                creator_wallet,
                concept["name"],
                concept["ticker"],
                concept["thesis"],
                target_lamports,
                created_at + duration_minutes * 60,
                created_at,
            ),
        )
        return self.get_campaign(campaign_id) or {}

    def get_campaign(self, campaign_id: str) -> dict | None:
        with self.conn() as connection:
            row = connection.execute(
                "SELECT * FROM campaigns WHERE id=?",
                (campaign_id,),
            ).fetchone()
            return self._campaign_to_public(row) if row else None

    def list_campaigns(self, limit: int = 100) -> list[dict]:
        with self.conn() as connection:
            rows = connection.execute(
                """
                SELECT * FROM campaigns
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (min(max(limit, 1), 100),),
            ).fetchall()
            return [self._campaign_to_public(row) for row in rows]

    def expire_campaigns(self, now: float | None = None) -> None:
        timestamp = time.time() if now is None else now
        self.execute(
            """
            UPDATE campaigns
            SET status='expired'
            WHERE status='funding' AND expires_at<=?
            """,
            (timestamp,),
        )

    def contribute(
        self,
        campaign_id: str,
        wallet: str,
        amount_sol: Decimal,
        idempotency_key: str | None = None,
    ) -> dict:
        amount_lamports = sol_to_lamports(amount_sol)
        key = idempotency_key or str(uuid4())
        expired = False
        accepted_lamports = 0
        replayed = False

        with self._write_lock, self.conn() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                previous = connection.execute(
                    """
                    SELECT campaign_id, wallet, amount_lamports
                    FROM contributions
                    WHERE idempotency_key=?
                    """,
                    (key,),
                ).fetchone()
                if previous:
                    if previous["campaign_id"] != campaign_id or previous["wallet"] != wallet:
                        raise ValueError("idempotency_key_conflict")
                    accepted_lamports = int(previous["amount_lamports"])
                    replayed = True
                    connection.execute("COMMIT")
                else:
                    campaign = connection.execute(
                        "SELECT * FROM campaigns WHERE id=?",
                        (campaign_id,),
                    ).fetchone()
                    if not campaign:
                        raise KeyError("campaign_not_found")
                    if campaign["status"] != "funding":
                        raise ValueError("campaign_not_funding")

                    if float(campaign["expires_at"]) <= time.time():
                        connection.execute(
                            "UPDATE campaigns SET status='expired' WHERE id=?",
                            (campaign_id,),
                        )
                        connection.execute("COMMIT")
                        expired = True
                    else:
                        room = max(
                            0,
                            int(campaign["target_lamports"])
                            - int(campaign["raised_lamports"]),
                        )
                        accepted_lamports = min(amount_lamports, room)
                        if accepted_lamports <= 0:
                            raise ValueError("target_reached")

                        connection.execute(
                            """
                            INSERT INTO contributions (
                                id, campaign_id, wallet, amount_lamports,
                                idempotency_key, status, created_at
                            )
                            VALUES (?, ?, ?, ?, ?, 'committed', ?)
                            """,
                            (
                                str(uuid4()),
                                campaign_id,
                                wallet,
                                accepted_lamports,
                                key,
                                time.time(),
                            ),
                        )
                        raised = int(campaign["raised_lamports"]) + accepted_lamports
                        status = (
                            "ready"
                            if raised >= int(campaign["target_lamports"])
                            else "funding"
                        )
                        connection.execute(
                            """
                            UPDATE campaigns
                            SET raised_lamports=?, status=?
                            WHERE id=?
                            """,
                            (raised, status, campaign_id),
                        )
                        connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

        if expired:
            raise ValueError("campaign_expired")

        campaign = self.get_campaign(campaign_id) or {}
        campaign["accepted_sol"] = lamports_to_sol(accepted_lamports)
        campaign["idempotent_replay"] = replayed
        return campaign

    def graduate_campaign(self, campaign_id: str) -> dict:
        with self._write_lock, self.conn() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                campaign = connection.execute(
                    "SELECT * FROM campaigns WHERE id=?",
                    (campaign_id,),
                ).fetchone()
                if not campaign:
                    raise KeyError("campaign_not_found")

                if campaign["status"] == "ready":
                    connection.execute(
                        "UPDATE campaigns SET status='live' WHERE id=?",
                        (campaign_id,),
                    )
                elif campaign["status"] != "live":
                    raise ValueError("campaign_not_ready")

                connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

        return self.get_campaign(campaign_id) or {}

    def refund_campaign(self, campaign_id: str, wallet: str) -> dict:
        with self._write_lock, self.conn() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                campaign = connection.execute(
                    "SELECT status FROM campaigns WHERE id=?",
                    (campaign_id,),
                ).fetchone()
                if not campaign:
                    raise KeyError("campaign_not_found")
                if campaign["status"] not in ("expired", "refunding"):
                    raise ValueError("campaign_not_refundable")

                rows = connection.execute(
                    """
                    SELECT amount_lamports, status
                    FROM contributions
                    WHERE campaign_id=? AND wallet=?
                    """,
                    (campaign_id, wallet),
                ).fetchall()
                if not rows:
                    raise ValueError("nothing_to_refund")

                committed = sum(
                    int(row["amount_lamports"])
                    for row in rows
                    if row["status"] == "committed"
                )
                refunded = sum(
                    int(row["amount_lamports"])
                    for row in rows
                    if row["status"] == "refunded"
                )

                if committed:
                    connection.execute(
                        """
                        UPDATE contributions
                        SET status='refunded'
                        WHERE campaign_id=? AND wallet=? AND status='committed'
                        """,
                        (campaign_id, wallet),
                    )
                connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

        total = committed if committed else refunded
        return {
            "campaign_id": campaign_id,
            "wallet": wallet,
            "refunded_sol": lamports_to_sol(total),
            "idempotent_replay": committed == 0 and refunded > 0,
        }


db = Database()
