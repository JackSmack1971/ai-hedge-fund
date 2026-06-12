import importlib
import sys
import types


def test_import_graph_service_does_not_trigger_dotenv_or_colorama(monkeypatch):
    dotenv_stub = types.ModuleType("dotenv")

    def load_dotenv():
        raise AssertionError("load_dotenv should not be called during graph import")

    dotenv_stub.load_dotenv = load_dotenv

    colorama_stub = types.ModuleType("colorama")

    def init(*args, **kwargs):
        raise AssertionError("colorama.init should not be called during graph import")

    colorama_stub.init = init

    monkeypatch.setitem(sys.modules, "dotenv", dotenv_stub)
    monkeypatch.setitem(sys.modules, "colorama", colorama_stub)
    sys.modules.pop("src.main", None)
    sys.modules.pop("app.backend.services.graph", None)

    module = importlib.import_module("app.backend.services.graph")

    assert hasattr(module, "create_graph")
