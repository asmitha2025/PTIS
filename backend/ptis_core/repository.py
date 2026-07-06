from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from .models import LinkDecision, VehicleObservation, utc_now_iso


class _ConnectionContext:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def __enter__(self) -> sqlite3.Connection:
        return self.connection

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()


class SQLiteEventStore:
    """Small durable event store for local verification and pilots."""

    def __init__(self, path: str | Path, vehicle_salt: str) -> None:
        self.path = path
        self.vehicle_salt = vehicle_salt
        self._connection: sqlite3.Connection | None = None
        if str(path) == ":memory:":
            self._connection = sqlite3.connect(":memory:")
        else:
            self.path = Path(path)
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def record_observation(self, observation: VehicleObservation) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO observations
                    (timestamp, vehicle_hash, junction_id, turned, source, raw_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    observation.timestamp,
                    self.hash_vehicle_id(observation.vehicle_id),
                    observation.junction_id,
                    int(observation.turned),
                    observation.source,
                    json.dumps(observation.__dict__, sort_keys=True),
                ),
            )

    def record_decision(self, decision: LinkDecision) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO decisions
                    (timestamp, link_id, destination_id, activate, confidence,
                     q_commanded_vpm, q_expected_vpm, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    utc_now_iso(),
                    decision.link_id,
                    decision.destination_id,
                    int(decision.activate),
                    decision.confidence,
                    decision.q_commanded_vpm,
                    decision.q_expected_vpm,
                    json.dumps(decision.__dict__, sort_keys=True),
                ),
            )

    def hash_vehicle_id(self, vehicle_id: str) -> str:
        payload = f"{self.vehicle_salt}:{vehicle_id}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def counts(self) -> dict[str, int]:
        with self._connect() as conn:
            obs = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
            dec = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        return {"observations": obs, "decisions": dec}

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    vehicle_hash TEXT NOT NULL,
                    junction_id TEXT NOT NULL,
                    turned INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    raw_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    link_id TEXT NOT NULL,
                    destination_id TEXT NOT NULL,
                    activate INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    q_commanded_vpm REAL NOT NULL,
                    q_expected_vpm REAL NOT NULL,
                    raw_json TEXT NOT NULL
                )
                """
            )

    def _connect(self):
        if self._connection is not None:
            return _ConnectionContext(self._connection)
        return sqlite3.connect(self.path)
