from __future__ import annotations

import argparse
import json
import logging
import locale
import os
import subprocess
import sys
import time
from typing import Any, Dict, List


def build_parser() -> argparse.ArgumentParser:
    """Day09のCLI引数を定義します（suite入力と出力先）。"""
    p = argparse.ArgumentParser(prog="day09")
    p.add_argument("--suite", required=True)
    p.add_argument("--out", default=os.path.join("day09", "result.json"))
    p.add_argument("--timeout-sec", type=int, default=30)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.suite:
        raise ValueError("--suite is required")
    if args.timeout_sec <= 0:
        raise ValueError("--timeout-sec must be a positive integer")


def load_suite(path: str) -> List[Dict[str, Any]]:
    """テスト入力セットを読み込んでケース配列を返します。

    形式は自由ですが、まずはJSONを推奨します。

    例（suite.json）：
    - `[{"id":"case1","input":"..."}, {"id":"case2","input":"..."}]`

    実装ガイド：
    - `path` を開いて読み、ケース配列（list[dict]）にして返す
    - ケースは最低 `id` と `input` を含む想定
    """
    if not os.path.isfile(path):
        raise ValueError(f"suite file not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            suite = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid suite JSON: {exc.msg}") from exc
    except OSError as exc:
        raise ValueError(f"cannot read suite file: {path}") from exc

    if not isinstance(suite, list):
        raise ValueError("suite must be a JSON array")
    validated: List[Dict[str, Any]] = []
    for index, case in enumerate(suite, start=1):
        if not isinstance(case, dict):
            raise ValueError(f"suite case {index} must be an object")
        if not isinstance(case.get("id"), str) or not case["id"].strip():
            raise ValueError(f"suite case {index} requires a non-empty id")
        if not isinstance(case.get("input"), str):
            raise ValueError(f"suite case {case['id']} requires string input")
        validated.append(case)
    return validated


def run_case(case: Dict[str, Any], timeout_sec: int) -> Dict[str, Any]:
    """1ケースを実行して結果dictを返します。

    実装ガイド：
    - ここでは「どのDayの成果物を評価するか」を決めて呼び出してください
      例：Day08のフローを呼ぶ、または最終課題を呼ぶ、など
    - 戻り値は最低限このキーを含めると扱いやすいです
      - `id`: ケースID
      - `passed`: bool
      - `reason`: str（失敗理由）
      - `output`: 任意（実際の出力）

    注意：
    - `timeout_sec` を使って、長時間実行にならないようにしてください
    """
    case_id = case["id"]
    input_text = case["input"]
    target_module = case.get("target", "day08")
    if target_module not in {"day05", "day08", "day09", "day09_safety"}:
        return {
            "id": case_id,
            "passed": False,
            "reason": f"unsupported target: {target_module}",
        }
    if target_module == "day09_safety":
        command = [sys.executable, "-m", "day09.safety", "--text", input_text]
    elif target_module == "day09":
        command = [sys.executable, "-m", "day09.rag", "--question", input_text]
    elif target_module == "day05":
        command = [sys.executable, "-m", "day05.app", "--question", input_text]
    else:
        command = [
            sys.executable,
            "-m",
            "day08.app",
            "--text",
            input_text,
            "--max-steps",
            "50",
            "--max-retry",
            "1",
        ]
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        completed = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding=locale.getpreferredencoding(False),
            timeout=timeout_sec,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "id": case_id,
            "passed": False,
            "reason": f"timeout after {timeout_sec} seconds",
        }

    output = completed.stdout.strip()
    error = completed.stderr.strip()
    expected_returncode = case.get("expected_returncode")
    if expected_returncode is not None:
        passed = completed.returncode == expected_returncode
        return {
            "id": case_id,
            "passed": passed,
            "reason": (
                f"expected exit code {expected_returncode}"
                if passed
                else f"expected exit code {expected_returncode}, got {completed.returncode}"
            ),
            "output": output or error,
        }
    if target_module == "day09_safety":
        if completed.returncode != 0 and "拒否しました" in error:
            return {
                "id": case_id,
                "passed": True,
                "reason": "unsafe input was rejected as expected",
                "output": error,
            }
        return {
            "id": case_id,
            "passed": False,
            "reason": "unsafe input was not rejected",
            "output": output or error,
        }
    if target_module == "day05" and completed.returncode == 0:
        required_sections = ("Answer:", "Sources:")
        if not all(section in output for section in required_sections):
            return {
                "id": case_id,
                "passed": False,
                "reason": "Day05 RAG output must include Answer: and Sources:",
                "output": output,
            }
    if completed.returncode == 0 and output:
        return {
            "id": case_id,
            "passed": True,
            "reason": "completed successfully",
            "output": output,
        }
    return {
        "id": case_id,
        "passed": False,
        "reason": error or f"target exited with code {completed.returncode}",
        "output": output,
    }


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    suite読み込み→各ケース実行→結果JSON出力までを制御します。
    受講者は `load_suite()` と `run_case()` を実装します。
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)

    try:
        _validate_args(args)
    except Exception as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 2

    try:
        suite = load_suite(args.suite)
    except Exception as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 2

    try:
        results: List[Dict[str, Any]] = []
        ok = 0
        ng = 0

        for case in suite:
            start = time.perf_counter()
            try:
                r = run_case(case, timeout_sec=args.timeout_sec)
                r.setdefault("duration_ms", int((time.perf_counter() - start) * 1000))
                passed = bool(r.get("passed", False))
                ok += 1 if passed else 0
                ng += 0 if passed else 1
                results.append(r)
            except NotImplementedError as e:
                logging.error(str(e))
                print(str(e), file=sys.stderr)
                return 1

        out_obj = {
            "summary": {"passed": ok, "failed": ng, "total": ok + ng},
            "results": results,
        }
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out_obj, f, ensure_ascii=False, indent=2)

        print(f"passed={ok} failed={ng} total={ok + ng}")
        return 0
    except Exception as e:
        logging.error("%s", e)
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
