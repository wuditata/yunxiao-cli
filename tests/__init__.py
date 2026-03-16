import contextlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def run_cli(args: list[str]) -> tuple[int, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC)
    command = [sys.executable, "-m", "yunxiao_cli.main", *args]
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout + result.stderr


def run_cli_main(args: list[str]) -> tuple[int, str]:
    from yunxiao_cli.main import main

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = main(args)
    return code, output.getvalue()


def run_cli_json(args: list[str]) -> dict:
    code, output = run_cli_main(args)
    if code != 0:
        raise AssertionError(output)
    return json.loads(output)
