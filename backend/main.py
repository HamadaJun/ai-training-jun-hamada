from __future__ import annotations

import shlex
import subprocess
import time
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    module: str = Field(..., description="Python module to execute, e.g. day01.app")
    args: List[str] = Field(default_factory=list)
    timeout_sec: int = Field(default=30, ge=1, le=300)


class RunResponse(BaseModel):
    command: List[str]
    returncode: int
    stdout: str
    stderr: str
    duration_ms: int


load_dotenv()
app = FastAPI(title="Training Runner API", version="0.1.0")


ALLOWED_MODULES = {
    "day01.app",
    "day02.app",
    "day03.app",
    "day04.app",
    "day05.app",
    "day06.app",
    "day07.app",
    "day08.app",
    "day09.app",
    "day10.app",
    "final.chat_ui",
}


def _build_command(module: str, args: List[str]) -> List[str]:
    return ["python", "-m", module, *args]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
def run(req: RunRequest) -> RunResponse:
    if req.module not in ALLOWED_MODULES:
        raise HTTPException(status_code=400, detail=f"module not allowed: {req.module}")

    cmd = _build_command(req.module, req.args)
    start = time.perf_counter()

    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=req.timeout_sec,
        )
        duration_ms = int((time.perf_counter() - start) * 1000)
        return RunResponse(
            command=cmd,
            returncode=p.returncode,
            stdout=p.stdout,
            stderr=p.stderr,
            duration_ms=duration_ms,
        )
    except subprocess.TimeoutExpired as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        stdout = (e.stdout or "") if isinstance(e.stdout, str) else ""
        stderr = (e.stderr or "") if isinstance(e.stderr, str) else ""
        stderr = (stderr + "\n" if stderr else "") + f"Timeout: {req.timeout_sec} seconds"
        return RunResponse(
            command=cmd,
            returncode=124,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
        )


@app.get("/run-spec")
def run_spec() -> dict:
    return {
        "example": {
            "module": "day01.app",
            "args": ["--name", "Taro", "--repeat", "2", "--format", "json"],
            "timeout_sec": 20,
        },
        "notes": [
            "This API executes `python -m <module> ...` as a subprocess.",
            "Returned returncode=124 means timeout.",
        ],
    }


@app.get("/debug/command")
def debug_command(module: str, args: Optional[str] = None) -> dict:
    parsed = shlex.split(args) if args else []
    cmd = _build_command(module, parsed)
    return {"command": cmd}
