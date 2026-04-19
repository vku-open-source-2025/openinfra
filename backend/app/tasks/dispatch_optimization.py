"""Background optimization tasks for dispatch orders."""

import asyncio
import logging

from app.celery_app import app as celery_app
from app.domain.services.dispatch_optimizer import (
    optimize_dispatch_orders as domain_optimize_dispatch_orders,
)

logger = logging.getLogger(__name__)


async def optimize_dispatch_orders_async(
    *,
    triggered_by: str,
    max_orders: int = 500,
    force_reestimate_eta: bool = False,
):
    """Compatibility wrapper for API endpoints and legacy imports."""
    return await domain_optimize_dispatch_orders(
        triggered_by=triggered_by,
        max_orders=max_orders,
        force_reestimate_eta=force_reestimate_eta,
    )


@celery_app.task(name="app.tasks.dispatch_optimization.optimize_dispatch_orders")
def run_dispatch_optimization_task() -> dict:
    """Periodic optimization job for pending dispatch orders."""
    result = asyncio.run(
        optimize_dispatch_orders_async(
            triggered_by="scheduler",
            max_orders=500,
            force_reestimate_eta=False,
        )
    )
    logger.info("Dispatch optimization completed: %s", result)
    return result


# Backward-compatible symbol used by task imports and scheduling references.
optimize_dispatch_orders = run_dispatch_optimization_task
