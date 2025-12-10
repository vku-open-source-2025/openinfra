#!/usr/bin/env python3
"""
Celery CLI - Command-line interface for running Celery workers and beat scheduler.

Usage:
    python scripts/celery_cli.py worker [--loglevel INFO] [--concurrency 4]
    python scripts/celery_cli.py beat [--loglevel INFO]
    python scripts/celery_cli.py both [--loglevel INFO] [--concurrency 4]
    python scripts/celery_cli.py flower [--port 5555]

Examples:
    # Start worker only
    python scripts/celery_cli.py worker

    # Start worker with debug logging
    python scripts/celery_cli.py worker --loglevel DEBUG

    # Start beat scheduler only
    python scripts/celery_cli.py beat

    # Start both worker and beat in separate processes
    python scripts/celery_cli.py both

    # Start Flower monitoring (optional)
    python scripts/celery_cli.py flower
"""

import argparse
import os
import sys
import subprocess
import signal
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_environment():
    """Check if required environment variables are set."""
    required_vars = ["REDIS_URL", "MONGODB_URL", "DATABASE_NAME"]
    missing = []

    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print("⚠ Warning: Missing environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nUsing defaults or values from .env file")
        print()


def run_worker(loglevel="info", concurrency=None, pool="prefork"):
    """Run Celery worker."""
    check_environment()

    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "app.celery_app",
        "worker",
        f"--loglevel={loglevel}",
    ]

    if concurrency:
        cmd.append(f"--concurrency={concurrency}")

    if pool:
        cmd.append(f"--pool={pool}")

    print("=" * 70)
    print("Starting Celery Worker")
    print("=" * 70)
    print(f"Log Level: {loglevel}")
    if concurrency:
        print(f"Concurrency: {concurrency}")
    print(f"Pool: {pool}")
    print()

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n✓ Worker stopped")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Worker failed with exit code {e.returncode}")
        sys.exit(1)


def run_beat(loglevel="info"):
    """Run Celery beat scheduler."""
    check_environment()

    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "app.celery_app",
        "beat",
        f"--loglevel={loglevel}",
    ]

    print("=" * 70)
    print("Starting Celery Beat Scheduler")
    print("=" * 70)
    print(f"Log Level: {loglevel}")
    print()

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n✓ Beat scheduler stopped")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Beat scheduler failed with exit code {e.returncode}")
        sys.exit(1)


def run_both(loglevel="info", concurrency=None, pool="prefork"):
    """Run both worker and beat in separate processes."""
    import multiprocessing

    check_environment()

    def run_worker_process():
        """Worker process function."""
        cmd = [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "app.celery_app",
            "worker",
            f"--loglevel={loglevel}",
        ]
        if concurrency:
            cmd.append(f"--concurrency={concurrency}")
        if pool:
            cmd.append(f"--pool={pool}")
        subprocess.run(cmd)

    def run_beat_process():
        """Beat process function."""
        cmd = [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "app.celery_app",
            "beat",
            f"--loglevel={loglevel}",
        ]
        subprocess.run(cmd)

    print("=" * 70)
    print("Starting Celery Worker + Beat Scheduler")
    print("=" * 70)
    print(f"Log Level: {loglevel}")
    if concurrency:
        print(f"Concurrency: {concurrency}")
    print(f"Pool: {pool}")
    print()

    processes = []

    def signal_handler(sig, frame):
        """Handle shutdown signals."""
        print("\n\nShutting down...")
        for p in processes:
            if p.is_alive():
                p.terminate()
        for p in processes:
            p.join(timeout=5)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start worker process
    worker_process = multiprocessing.Process(
        target=run_worker_process, name="celery-worker"
    )
    worker_process.start()
    processes.append(worker_process)
    print("✓ Worker process started (PID: {})".format(worker_process.pid))

    # Start beat process
    beat_process = multiprocessing.Process(target=run_beat_process, name="celery-beat")
    beat_process.start()
    processes.append(beat_process)
    print("✓ Beat process started (PID: {})".format(beat_process.pid))
    print("\nPress Ctrl+C to stop both processes\n")

    # Wait for processes
    try:
        worker_process.join()
        beat_process.join()
    except KeyboardInterrupt:
        signal_handler(None, None)


def run_flower(port=5555, broker=None):
    """Run Flower monitoring tool (optional)."""
    import importlib.util

    flower_spec = importlib.util.find_spec("flower")
    if flower_spec is None:
        print("❌ Flower is not installed")
        print("Install it with: pip install flower")
        sys.exit(1)

    check_environment()

    broker_url = broker or os.getenv("REDIS_URL", "redis://localhost:6379/0")

    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "app.celery_app",
        "flower",
        f"--port={port}",
        f"--broker={broker_url}",
    ]

    print("=" * 70)
    print("Starting Flower Monitoring")
    print("=" * 70)
    print(f"Port: {port}")
    print(f"Broker: {broker_url}")
    print(f"URL: http://localhost:{port}")
    print()

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n✓ Flower stopped")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Flower failed with exit code {e.returncode}")
        sys.exit(1)


def show_status():
    """Show Celery status and active tasks."""
    check_environment()

    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "app.celery_app",
        "inspect",
        "active",
    ]

    print("=" * 70)
    print("Celery Status")
    print("=" * 70)
    print()

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print("⚠ No active workers found")
        print("Start a worker with: python scripts/celery_cli.py worker")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Celery CLI - Run Celery workers and beat scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Worker command
    worker_parser = subparsers.add_parser("worker", help="Start Celery worker")
    worker_parser.add_argument(
        "--loglevel",
        default="info",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level (default: info)",
    )
    worker_parser.add_argument(
        "--concurrency",
        type=int,
        help="Number of worker processes/threads (default: auto)",
    )
    worker_parser.add_argument(
        "--pool",
        default="prefork",
        choices=["prefork", "threads", "solo", "gevent", "eventlet"],
        help="Pool implementation (default: prefork)",
    )

    # Beat command
    beat_parser = subparsers.add_parser("beat", help="Start Celery beat scheduler")
    beat_parser.add_argument(
        "--loglevel",
        default="info",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level (default: info)",
    )

    # Both command
    both_parser = subparsers.add_parser(
        "both", help="Start both worker and beat scheduler"
    )
    both_parser.add_argument(
        "--loglevel",
        default="info",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level (default: info)",
    )
    both_parser.add_argument(
        "--concurrency",
        type=int,
        help="Number of worker processes/threads (default: auto)",
    )
    both_parser.add_argument(
        "--pool",
        default="prefork",
        choices=["prefork", "threads", "solo", "gevent", "eventlet"],
        help="Pool implementation (default: prefork)",
    )

    # Flower command
    flower_parser = subparsers.add_parser("flower", help="Start Flower monitoring")
    flower_parser.add_argument(
        "--port", type=int, default=5555, help="Flower port (default: 5555)"
    )
    flower_parser.add_argument(
        "--broker", help="Broker URL (default: from REDIS_URL env var)"
    )

    # Status command
    subparsers.add_parser("status", help="Show Celery status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Convert loglevel to lowercase for Celery
    loglevel = args.loglevel.lower() if hasattr(args, "loglevel") else "info"

    if args.command == "worker":
        run_worker(
            loglevel=loglevel,
            concurrency=getattr(args, "concurrency", None),
            pool=getattr(args, "pool", "prefork"),
        )
    elif args.command == "beat":
        run_beat(loglevel=loglevel)
    elif args.command == "both":
        run_both(
            loglevel=loglevel,
            concurrency=getattr(args, "concurrency", None),
            pool=getattr(args, "pool", "prefork"),
        )
    elif args.command == "flower":
        run_flower(port=args.port, broker=getattr(args, "broker", None))
    elif args.command == "status":
        show_status()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
