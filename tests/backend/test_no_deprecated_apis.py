"""Guards against reintroducing APIs deprecated by pinned Pydantic/FastAPI versions (#21/#22)."""

from pathlib import Path

import app.backend

BACKEND_DIR = Path(app.backend.__file__).parent


def _backend_sources():
    return [p for p in BACKEND_DIR.rglob("*.py") if "alembic" not in p.parts]


def test_no_pydantic_from_orm_usage():
    offenders = [str(p) for p in _backend_sources() if ".from_orm(" in p.read_text(encoding="utf-8")]
    assert offenders == [], f"Use Model.model_validate() instead of deprecated .from_orm(): {offenders}"


def test_no_fastapi_on_event_usage():
    offenders = [str(p) for p in _backend_sources() if ".on_event(" in p.read_text(encoding="utf-8")]
    assert offenders == [], f"Use a lifespan handler instead of deprecated @app.on_event: {offenders}"


def test_app_uses_lifespan_handler():
    from app.backend.main import app, lifespan

    assert app.router.lifespan_context is not None
    assert callable(lifespan)


def test_importing_main_does_not_run_ddl(monkeypatch):
    """Schema creation must happen in the lifespan (startup), not at import time.

    app.backend.main is already imported by other tests, so a fresh import can't
    be observed directly; instead assert no module-level create_all call exists.
    """
    source = (BACKEND_DIR / "main.py").read_text(encoding="utf-8")
    module_level_calls = [line for line in source.splitlines() if line.startswith("Base.metadata.create_all")]
    assert module_level_calls == [], "create_all must not run as an import side effect"
