from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import List


def build_parser() -> argparse.ArgumentParser:
    """Day01のCLI引数を定義します。

    原則として受講者はこの関数を編集せず、要件変更がある場合のみ調整します。
    """
    p = argparse.ArgumentParser(prog="day01")
    p.add_argument("--name", required=True)
    p.add_argument("--repeat", type=int, default=1)
    p.add_argument("--format", choices=["text", "json"], default="text")
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2 で終了）。"""
    if not args.name:
        raise ValueError("--name is required")
    if not (1 <= args.repeat <= 10):
        raise ValueError("--repeat must be between 1 and 10")


def run(name: str, repeat: int, fmt: str) -> str:
    """課題ロジック本体です（Day01は完成形の見本として実装済み）。"""
    outputs: List[str] = [f"Hello, {name}" for _ in range(repeat)]
    if fmt == "json":
        return json.dumps({"name": name, "repeat": repeat, "outputs": outputs}, ensure_ascii=False)
    return "\n".join(outputs)


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    引数解析→検証→実行→終了コードの責務を持ちます。受講者は原則編集不要です。
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        _validate_args(args)
    except Exception as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 2

    logging.info("name=%s repeat=%s format=%s", args.name, args.repeat, args.format)

    try:
        out = run(args.name, args.repeat, args.format)
        print(out)
        return 0
    except Exception as e:
        logging.error("%s", e)
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
