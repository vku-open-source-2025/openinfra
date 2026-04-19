"""Regression guards for dispatch optimizer scheduler wiring."""

import importlib.util
from pathlib import Path

from app.celery_app import app as celery_app


def _load_dispatch_optimization_module():
    module_path = Path(__file__).resolve().parents[2] / "app" / "tasks" / "dispatch_optimization.py"
    spec = importlib.util.spec_from_file_location(
        "dispatch_optimization_scheduler_wiring_under_test", module_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load dispatch_optimization module for tests")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dispatch_optimization = _load_dispatch_optimization_module()


def test_dispatch_scheduler_task_name_matches_exported_task_name():
    schedule_task_name = celery_app.conf.beat_schedule["optimize-dispatch-orders"]["task"]
    exported_task_name = dispatch_optimization.optimize_dispatch_orders.name

    assert schedule_task_name == exported_task_name


def test_backward_compatible_optimize_dispatch_orders_symbol_exists_and_callable():
    assert hasattr(dispatch_optimization, "optimize_dispatch_orders")
    assert callable(dispatch_optimization.optimize_dispatch_orders)
    assert (
        dispatch_optimization.optimize_dispatch_orders
        is dispatch_optimization.run_dispatch_optimization_task
    )
