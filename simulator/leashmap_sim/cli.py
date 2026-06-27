"""Command-line entry. See docs/detailed-design/device-simulator.md."""
from __future__ import annotations

import argparse
import sys

import httpx

from .routes import load_route
from .runner import Runner, RunnerConfig

MODES = ["normal", "lost", "offline", "drift", "low_battery", "exit_zone"]


def parse_interval(value: str) -> float:
    """Accepts '5s', '500ms', or a bare number of seconds."""
    v = value.strip().lower()
    if v.endswith("ms"):
        return float(v[:-2]) / 1000.0
    if v.endswith("s"):
        return float(v[:-1])
    return float(v)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="leashmap-sim", description="LeashMap device simulator")
    p.add_argument("--device-id", default="dev_mvp_001")
    p.add_argument("--endpoint", default="http://localhost:8080")
    p.add_argument("--token", default="dev-token", help="device bearer token")
    p.add_argument("--route", default=None, help="route fixture JSON (omit for random walk)")
    p.add_argument("--interval", default="1s", help="upload interval, e.g. 5s / 500ms / 2")
    p.add_argument("--battery", type=float, default=85.0, help="initial battery percent")
    p.add_argument("--mode", choices=MODES, default="normal")
    p.add_argument("--count", type=int, default=20, help="number of points to send")
    p.add_argument("--batch-size", type=int, default=5, help="offline mode batch size")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    route = load_route(args.route) if args.route else None

    cfg = RunnerConfig(
        device_id=args.device_id,
        endpoint=args.endpoint,
        token=args.token,
        mode=args.mode,
        interval=parse_interval(args.interval),
        battery=args.battery,
        count=args.count,
        batch_size=args.batch_size,
        route=route,
    )

    try:
        Runner(cfg).run()
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130
    except httpx.ConnectError:
        print(f"error: cannot reach cloud at {args.endpoint} — is the server running?",
              file=sys.stderr)
        return 1
    except httpx.HTTPStatusError as e:
        print(f"error: server returned {e.response.status_code}: {e.response.text}",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
