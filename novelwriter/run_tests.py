#!/usr/bin/env python3
"""Run novelWriter Tests."""  # noqa: CPY001

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys

from pathlib import Path

if __name__ == "__main__":
    """Parse command line options and run the commands."""
    parser = argparse.ArgumentParser(usage="run_tests.py [--flags]")
    parser.add_argument("-o", action="store_true", help="Run off screen")
    parser.add_argument("-r", action="store_true", help="Generate xml coverage report")
    parser.add_argument("--html", action="store_true", help="Generate html coverage report")
    parser.add_argument("-t", action="store_true", help="Generate terminal coverage report")
    parser.add_argument("-u", action="store_true", help="Generate uncovered terminal report")
    parser.add_argument("-l", action="store_true", help="Generate uncovered terminal report with missing lines")
    parser.add_argument("--failed", action="store_true", help="Re-run failed tests")
    parser.add_argument("--step", action="store_true", help="Run tests stepwise")
    parser.add_argument("-m", help="Test modules", metavar="MARKEXPR")
    parser.add_argument("-k", help="Test filters", metavar="EXPRESSION")

    args = parser.parse_args()

    env = os.environ.copy()
    env["QT_SCALE_FACTOR"] = "1.0"
    tmpConf = Path(__file__).parent / ".coveragerc"

    if args.r or args.t or args.u:
        cmd = ["coverage", "run"]
        if args.failed or args.step:
            cmd += ["--append"]
        cmd += ["-m"]
    else:
        cmd = [sys.executable, "-m"]

    cmd += ["pytest", "-vv"]
    if args.o:
        env["QT_QPA_PLATFORM"] = "offscreen"
    if args.failed:
        cmd += ["--last-failed"]
    if args.step:
        cmd += ["--stepwise"]
    if args.m:
        cmd += ["-m", args.m]
    if args.k:
        cmd += ["-k", args.k]

    print("Calling:", shlex.join(cmd))
    subprocess.call(cmd, env=env)

    if args.r:
        subprocess.call(["coverage", "xml"])
    if args.html:
        subprocess.call(["coverage", "html"])
    if args.t and not args.u:
        subprocess.call(["coverage", "report"])
    if args.u:
        subprocess.call(["coverage", "report", "--skip-covered"])
    if args.l:
        subprocess.call(["coverage", "report", "--skip-covered", "--show-missing"])

    tmpConf.unlink(missing_ok=True)
