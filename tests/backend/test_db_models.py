"""Tests for app/backend/database/models.py — ORM model constraints and relationships."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool

from app.backend.database.models import Base, HedgeFundFlow, HedgeFundFlowRun


@pytest.fixture
def engine():
    e = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(e)
    yield e
    Base.metadata.drop_all(e)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


class TestHedgeFundFlowModel:
    def test_create_minimal_flow(self, session):
        flow = HedgeFundFlow(name="Flow A", nodes=[], edges=[])
        session.add(flow)
        session.commit()
        assert flow.id is not None

    def test_id_is_auto_generated(self, session):
        f1 = HedgeFundFlow(name="F1", nodes=[], edges=[])
        f2 = HedgeFundFlow(name="F2", nodes=[], edges=[])
        session.add_all([f1, f2])
        session.commit()
        assert f1.id != f2.id

    def test_optional_fields_default_none(self, session):
        flow = HedgeFundFlow(name="Flow", nodes=[], edges=[])
        session.add(flow)
        session.commit()
        assert flow.description is None
        assert flow.viewport is None
        assert flow.data is None

    def test_is_template_default_false(self, session):
        flow = HedgeFundFlow(name="Flow", nodes=[], edges=[])
        session.add(flow)
        session.commit()
        assert flow.is_template is False

    def test_json_fields_stored_correctly(self, session):
        nodes = [{"id": "n1", "type": "analyst"}]
        edges = [{"id": "e1", "source": "n1", "target": "n2"}]
        flow = HedgeFundFlow(name="Flow", nodes=nodes, edges=edges)
        session.add(flow)
        session.commit()
        session.expire(flow)
        fetched = session.get(HedgeFundFlow, flow.id)
        assert fetched.nodes == nodes
        assert fetched.edges == edges


class TestHedgeFundFlowRunModel:
    @pytest.fixture
    def parent_flow(self, session):
        flow = HedgeFundFlow(name="Parent Flow", nodes=[], edges=[])
        session.add(flow)
        session.commit()
        return flow

    def test_create_run_with_valid_flow_id(self, session, parent_flow):
        run = HedgeFundFlowRun(flow_id=parent_flow.id, status="IDLE", run_number=1)
        session.add(run)
        session.commit()
        assert run.id is not None

    def test_run_status_default(self, session, parent_flow):
        run = HedgeFundFlowRun(flow_id=parent_flow.id, run_number=1)
        session.add(run)
        session.commit()
        assert run.status == "IDLE"

    def test_run_results_stored_as_json(self, session, parent_flow):
        results = {"decisions": {"AAPL": "buy"}, "confidence": 0.8}
        run = HedgeFundFlowRun(flow_id=parent_flow.id, results=results, run_number=1)
        session.add(run)
        session.commit()
        session.expire(run)
        fetched = session.get(HedgeFundFlowRun, run.id)
        assert fetched.results == results

    def test_multiple_runs_for_same_flow(self, session, parent_flow):
        for i in range(3):
            run = HedgeFundFlowRun(flow_id=parent_flow.id, run_number=i + 1)
            session.add(run)
        session.commit()
        count = session.query(HedgeFundFlowRun).filter_by(flow_id=parent_flow.id).count()
        assert count == 3
