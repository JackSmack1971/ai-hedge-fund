"""Tests for app/backend/repositories/ — CRUD operations using in-memory SQLite."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.backend.database.models import Base, HedgeFundFlow, HedgeFundFlowRun
from app.backend.repositories.flow_repository import FlowRepository
from app.backend.repositories.flow_run_repository import FlowRunRepository
from app.backend.models.schemas import FlowRunStatus


# ──────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────

@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture
def flow_repo(db_session):
    return FlowRepository(db_session)


@pytest.fixture
def run_repo(db_session):
    return FlowRunRepository(db_session)


@pytest.fixture
def sample_flow(flow_repo):
    return flow_repo.create_flow(
        name="Test Flow",
        nodes=[{"id": "n1"}],
        edges=[],
        description="A test flow",
    )


# ──────────────────────────────────────────────────────────
# FlowRepository tests
# ──────────────────────────────────────────────────────────

class TestFlowRepositoryCreate:
    def test_create_returns_persisted_flow(self, flow_repo):
        flow = flow_repo.create_flow(name="My Flow", nodes=[{"id": "n1"}], edges=[])
        assert flow.id is not None
        assert flow.name == "My Flow"

    def test_create_generates_id(self, flow_repo):
        flow = flow_repo.create_flow(name="Flow A", nodes=[], edges=[])
        assert isinstance(flow.id, int)
        assert flow.id > 0

    def test_create_with_all_fields(self, flow_repo):
        flow = flow_repo.create_flow(
            name="Full Flow",
            nodes=[{"id": "n1"}],
            edges=[{"id": "e1", "source": "n1", "target": "n2"}],
            description="Full description",
            is_template=True,
            tags=["tag1", "tag2"],
        )
        assert flow.description == "Full description"
        assert flow.is_template is True
        assert "tag1" in flow.tags


class TestFlowRepositoryRead:
    def test_get_by_id_existing(self, flow_repo, sample_flow):
        fetched = flow_repo.get_flow_by_id(sample_flow.id)
        assert fetched is not None
        assert fetched.id == sample_flow.id
        assert fetched.name == "Test Flow"

    def test_get_by_id_missing_returns_none(self, flow_repo):
        result = flow_repo.get_flow_by_id(99999)
        assert result is None

    def test_get_all_flows_returns_all(self, flow_repo):
        flow_repo.create_flow(name="Flow A", nodes=[], edges=[])
        flow_repo.create_flow(name="Flow B", nodes=[], edges=[])
        flows = flow_repo.get_all_flows()
        assert len(flows) >= 2

    def test_get_all_flows_empty_table(self, flow_repo):
        flows = flow_repo.get_all_flows()
        assert flows == []


class TestFlowRepositoryUpdate:
    def test_update_name(self, flow_repo, sample_flow):
        updated = flow_repo.update_flow(sample_flow.id, name="Updated Name")
        assert updated is not None
        assert updated.name == "Updated Name"

    def test_update_nonexistent_returns_none(self, flow_repo):
        result = flow_repo.update_flow(99999, name="Ghost")
        assert result is None

    def test_update_persists_to_db(self, flow_repo, sample_flow):
        flow_repo.update_flow(sample_flow.id, description="New description")
        fetched = flow_repo.get_flow_by_id(sample_flow.id)
        assert fetched.description == "New description"


class TestFlowRepositoryDelete:
    def test_delete_existing_flow(self, flow_repo, sample_flow):
        result = flow_repo.delete_flow(sample_flow.id)
        assert result is True
        assert flow_repo.get_flow_by_id(sample_flow.id) is None

    def test_delete_nonexistent_returns_false(self, flow_repo):
        result = flow_repo.delete_flow(99999)
        assert result is False


# ──────────────────────────────────────────────────────────
# FlowRunRepository tests
# ──────────────────────────────────────────────────────────

class TestFlowRunRepositoryCreate:
    def test_create_run_with_valid_flow(self, flow_repo, run_repo, sample_flow):
        run = run_repo.create_flow_run(flow_id=sample_flow.id)
        assert run.id is not None
        assert run.flow_id == sample_flow.id
        assert run.status == FlowRunStatus.IDLE.value

    def test_create_run_with_request_data(self, flow_repo, run_repo, sample_flow):
        data = {"tickers": ["AAPL"], "model": "gpt-4o"}
        run = run_repo.create_flow_run(flow_id=sample_flow.id, request_data=data)
        assert run.request_data == data


class TestFlowRunRepositoryRead:
    def test_get_by_id_existing(self, flow_repo, run_repo, sample_flow):
        run = run_repo.create_flow_run(flow_id=sample_flow.id)
        fetched = run_repo.get_flow_run_by_id(run.id)
        assert fetched is not None
        assert fetched.id == run.id

    def test_get_by_id_missing_returns_none(self, run_repo):
        assert run_repo.get_flow_run_by_id(99999) is None

    def test_get_runs_by_flow_id(self, flow_repo, run_repo, sample_flow):
        run_repo.create_flow_run(flow_id=sample_flow.id)
        run_repo.create_flow_run(flow_id=sample_flow.id)
        runs = run_repo.get_flow_runs_by_flow_id(sample_flow.id)
        assert len(runs) == 2

    def test_get_runs_empty_flow(self, run_repo):
        runs = run_repo.get_flow_runs_by_flow_id(99999)
        assert runs == []


class TestFlowRunRepositoryUpdate:
    def test_update_status(self, flow_repo, run_repo, sample_flow):
        run = run_repo.create_flow_run(flow_id=sample_flow.id)
        updated = run_repo.update_flow_run(run.id, status=FlowRunStatus.IN_PROGRESS)
        assert updated is not None
        assert updated.status == FlowRunStatus.IN_PROGRESS.value

    def test_update_nonexistent_returns_none(self, run_repo):
        result = run_repo.update_flow_run(99999, status=FlowRunStatus.COMPLETE)
        assert result is None

    def test_update_to_complete(self, flow_repo, run_repo, sample_flow):
        run = run_repo.create_flow_run(flow_id=sample_flow.id)
        results_data = {"signal": "bullish", "confidence": 80}
        updated = run_repo.update_flow_run(
            run.id,
            status=FlowRunStatus.COMPLETE,
            results=results_data,
        )
        assert updated.status == FlowRunStatus.COMPLETE.value
        assert updated.results == results_data
