#!/usr/bin/env python3

"""Unified launcher for SolBot web services.

Run the Flask control API (`web/app.py`) which serves both the REST API
and the HTML/CSS/JS dashboard. Child processes are spawned with the
current Python interpreter so the active virtualenv (if any) is respected.

The dashboard is accessible at http://localhost:5000/ or http://localhost:5000/dashboard

Press Ctrl+C to stop; the service will be terminated cleanly.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from typing import List, Tuple


ProcessEntry = Tuple[str, subprocess.Popen]


def _start_process(name: str, args: List[str]) -> subprocess.Popen:
    """Start a child process, streaming output to the parent console."""

    env = os.environ.copy()
    # Ensure the working directory is the project root (this file's directory).
    cwd = os.path.dirname(os.path.abspath(__file__))
    return subprocess.Popen(args, cwd=cwd, env=env)


def _terminate_process(proc: subprocess.Popen, name: str, timeout: float = 10.0) -> None:
    """Terminate a process gracefully, escalating to kill if needed."""

    if proc.poll() is not None:
        return

    print(f"Stopping {name} (pid {proc.pid})?", flush=True)
    proc.terminate()

    start = time.time()
    while proc.poll() is None and (time.time() - start) < timeout:
        time.sleep(0.2)

    if proc.poll() is None:
        print(f"{name} did not exit in {timeout:.0f}s; killing?", flush=True)
        proc.kill()


def _run() -> int:
    processes: List[ProcessEntry] = []

    def shutdown(signum: int, frame) -> None:  # type: ignore[override]
        print("\nShutdown signal received; cleaning up?", flush=True)
        for proc_name, proc in processes:
            _terminate_process(proc, proc_name)
        sys.exit(0)

    # Register signal handlers for Ctrl+C and SIGTERM.
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    commands = [
        ("Flask API & Dashboard", [sys.executable, "web/app.py"]),
    ]

    try:
        for name, cmd in commands:
            print(f"Starting {name}: {' '.join(cmd)}", flush=True)
            proc = _start_process(name, cmd)
            processes.append((name, proc))

        # Monitor child processes; exit if any one of them terminates.
        while True:
            for name, proc in processes:
                ret = proc.poll()
                if ret is not None:
                    print(f"{name} exited with code {ret}; shutting down remaining services?", flush=True)
                    for other_name, other_proc in processes:
                        if other_proc is not proc:
                            _terminate_process(other_proc, other_name)
                    return ret if ret is not None else 0
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown(signal.SIGINT, None)  # type: ignore[arg-type]
    finally:
        for name, proc in processes:
            _terminate_process(proc, name)

    return 0


if __name__ == "__main__":
    sys.exit(_run())
