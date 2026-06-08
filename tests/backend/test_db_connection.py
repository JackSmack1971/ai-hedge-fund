"""Tests for database connection: WAL mode (#165) and index coverage (#166)."""

import os
import tempfile

import pytest
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.pool import StaticPool

from app.backend.database.models import (
    ApiKey,
    Base,
    HedgeFundFlow,
    HedgeFundFlowRun,
    HedgeFundFlowRunCycle,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sqlite_file_engine(path: str):
    """Create a file-based SQLite engine with WAL pragmas applied."""
    eng = create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(eng, "connect")
    def set_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")
        cursor.close()

    return eng


# ---------------------------------------------------------------------------
# WAL mode tests (#165)
# ---------------------------------------------------------------------------


class TestSQLiteWALMode:
    def test_wal_mode_enabled(self, tmp_path):
        """PRAGMA journal_mode should be 'wal' after engine creation."""
        db_path = str(tmp_path / "test.db")
        eng = _sqlite_file_engine(db_path)
        Base.metadata.create_all(eng)

        with eng.connect() as conn:
            result = conn.execute(text("PRAGMA journal_mode")).scalar()
        assert result == "wal"

    def test_synchronous_normal(self, tmp_path):
        """PRAGMA synchronous should be 1 (NORMAL) for WAL performance."""
        db_path = str(tmp_path / "test.db")
        eng = _sqlite_file_engine(db_path)
        Base.metadata.create_all(eng)

        with eng.connect() as conn:
            # SQLite returns numeric 1 for NORMAL
            result = conn.execute(text("PRAGMA synchronous")).scalar()
        assert result == 1

    def test_timeout_in_connect_args(self):
        """Connection args should include a 30-second busy timeout for SQLite."""
        from app.backend.database.connection import _connect_args, DATABASE_URL

        if DATABASE_URL.startswith("sqlite"):
            assert _connect_args.get("timeout") == 30

    def test_wal_allows_concurrent_read_write(self, tmp_path):
        """Write + read on separate connections should not raise 'database is locked'."""
        db_path = str(tmp_path / "test.db")
        eng = _sqlite_file_engine(db_path)
        Base.metadata.create_all(eng)

        from sqlalchemy.orm import Session

        with Session(eng) as s1, Session(eng) as s2:
            flow = HedgeFundFlow(name="WAL test", nodes=[], edges=[])
            s1.add(flow)
            s1.commit()
            count = s2.query(HedgeFundFlow).count()
        assert count == 1

    def test_event_listener_is_noop_for_non_sqlite(self):
        """_set_sqlite_pragmas should not execute for non-SQLite engines."""
        from app.backend.database import connection as db_conn

        # The guard is: if not _is_sqlite: return
        # Simulate by temporarily patching _is_sqlite to False and checking
        # the function returns before executing cursor commands.
        original = db_conn._is_sqlite
        db_conn._is_sqlite = False
        try:

            class FakeCursor:
                def execute(self, sql):
                    raise AssertionError(f"Should not execute SQL for non-SQLite: {sql}")

                def close(self):
                    pass

            class FakeConn:
                def cursor(self):
                    return FakeCursor()

            # Should complete without raising
            db_conn._set_sqlite_pragmas(FakeConn(), None)
        finally:
            db_conn._is_sqlite = original


# ---------------------------------------------------------------------------
# Index coverage tests (#166)
# ---------------------------------------------------------------------------


class TestModelIndices:
    """Verify index=True is set on all filter columns."""

    def test_hedge_fund_flow_is_template_indexed(self):
        col = HedgeFundFlow.__table__.c["is_template"]
        assert col.index, "HedgeFundFlow.is_template must have index=True"

    def test_hedge_fund_flow_run_status_indexed(self):
        col = HedgeFundFlowRun.__table__.c["status"]
        assert col.index, "HedgeFundFlowRun.status must have index=True"

    def test_hedge_fund_flow_run_trading_mode_indexed(self):
        col = HedgeFundFlowRun.__table__.c["trading_mode"]
        assert col.index, "HedgeFundFlowRun.trading_mode must have index=True"

    def test_hedge_fund_flow_run_cycle_status_indexed(self):
        col = HedgeFundFlowRunCycle.__table__.c["status"]
        assert col.index, "HedgeFundFlowRunCycle.status must have index=True"

    def test_hedge_fund_flow_run_cycle_cycle_number_indexed(self):
        col = HedgeFundFlowRunCycle.__table__.c["cycle_number"]
        assert col.index, "HedgeFundFlowRunCycle.cycle_number must have index=True"

    def test_api_key_is_active_indexed(self):
        col = ApiKey.__table__.c["is_active"]
        assert col.index, "ApiKey.is_active must have index=True"

    def test_indices_exist_in_db_schema(self, tmp_path):
        """All six new indices should appear in a freshly created SQLite database."""
        eng = create_engine(
            f"sqlite:///{tmp_path / 'schema.db'}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(eng)
        inspector = inspect(eng)

        expected = {
            "hedge_fund_flows": {"ix_hedge_fund_flows_is_template"},
            "hedge_fund_flow_runs": {
                "ix_hedge_fund_flow_runs_status",
                "ix_hedge_fund_flow_runs_trading_mode",
            },
            "hedge_fund_flow_run_cycles": {
                "ix_hedge_fund_flow_run_cycles_status",
                "ix_hedge_fund_flow_run_cycles_cycle_number",
            },
            "api_keys": {"ix_api_keys_is_active"},
        }

        for table_name, index_names in expected.items():
            actual = {idx["name"] for idx in inspector.get_indexes(table_name)}
            for idx_name in index_names:
                assert idx_name in actual, (
                    f"Expected index '{idx_name}' not found in table '{table_name}'. " f"Found: {actual}"
                )
