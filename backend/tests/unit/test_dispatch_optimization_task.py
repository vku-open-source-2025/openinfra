"""Regression tests for dispatch optimization task wrappers."""

import importlib.util
from pathlib import Path

import pytest


def _load_dispatch_optimization_module():
    module_path = Path(__file__).resolve().parents[2] / "app" / "tasks" / "dispatch_optimization.py"
    spec = importlib.util.spec_from_file_location("dispatch_optimization_under_test", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load dispatch_optimization module for tests")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dispatch_optimization = _load_dispatch_optimization_module()


@pytest.mark.asyncio
async def test_async_wrapper_calls_domain_optimizer(monkeypatch):
    captured = {}
    expected = {"optimized": 1, "triggered_by": "manual"}

    async def fake_domain_optimizer(**kwargs):
        captured.update(kwargs)
        return expected

    monkeypatch.setattr(
        dispatch_optimization,
        "domain_optimize_dispatch_orders",
        fake_domain_optimizer,
    )

    result = await dispatch_optimization.optimize_dispatch_orders_async(
        triggered_by="manual",
        max_orders=42,
        force_reestimate_eta=True,
    )

    assert result == expected
    assert captured == {
        "triggered_by": "manual",
        "max_orders": 42,
        "force_reestimate_eta": True,
    }


def test_task_returns_dict_without_recursion(monkeypatch):
    captured = {}
    expected = {"optimized": 3, "triggered_by": "scheduler"}

    async def fake_domain_optimizer(**kwargs):
        captured.update(kwargs)
        return expected

    monkeypatch.setattr(
        dispatch_optimization,
        "domain_optimize_dispatch_orders",
        fake_domain_optimizer,
    )

    result = dispatch_optimization.optimize_dispatch_orders()

    assert dispatch_optimization.optimize_dispatch_orders is dispatch_optimization.run_dispatch_optimization_task
    assert isinstance(result, dict)
    assert result == expected
    assert captured == {
        "triggered_by": "scheduler",
        "max_orders": 500,
        "force_reestimate_eta": False,
    }
