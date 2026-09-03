from __future__ import annotations

import argparse
import logging
import sys
from typing import List

from final.agent import run_agent


def build_parser() -> argparse.ArgumentParser:
    """Day10のCLI引数を定義します（最終課題に渡す入力）。"""
    p = argparse.ArgumentParser(prog="day10")
    p.add_argument("--text", required=True)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.text:
        raise ValueError("--text is required")


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    `final.agent.run_agent()` を呼び出して統合の入口にします。受講者は主に final 側を実装します。
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
        result = run_agent(args.text, history=[])
        reply = str(result.get("reply", ""))
        print(reply)
        return 0
    except Exception as e:
        logging.error("%s", e)
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
