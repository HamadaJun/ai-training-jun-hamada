from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import List


def build_parser() -> argparse.ArgumentParser:
    """Day06のCLI引数を定義します（入力・モード・ケース番号）。"""
    p = argparse.ArgumentParser(prog="day06")
    p.add_argument("--text", required=True)
    p.add_argument("--mode", choices=["normal", "attack"], default="normal")
    p.add_argument("--case", type=int, default=1)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.text:
        raise ValueError("--text is required")
    if args.mode == "attack" and not (1 <= args.case <= 3):
        raise ValueError("--case must be between 1 and 3 when --mode attack")


def run_guarded(*, text: str, mode: str, case: int) -> str:
    """入力とツール実行をガードしながら処理し、回答（文字列）を返します。

    `mode` の意味：
    - `normal`：通常入力を処理
    - `attack`：用意した「悪い入力例」を使って、ガードが効いているか確認

    実装ガイド：
    - attackケースは最低3つ用意（README参照）
    - 「禁止する行為」を明確にし、検知したら例外（または拒否文）にする
    - ツールを実装する場合は許可リストで制限する（許可されないツールは実行しない）

    返り値：
    - 標準出力に出る本文（文章）を返す
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("拒否しました: --text は空にできません")
    if len(text) > 2000:
        raise ValueError("拒否しました: 入力が長すぎます")
    if mode not in {"normal", "attack"}:
        raise ValueError("拒否しました: 未知の実行モードです")
    if not isinstance(case, int) or isinstance(case, bool) or not 1 <= case <= 3:
        raise ValueError("拒否しました: --case は1〜3の整数で指定してください")

    blocked_patterns = {
        1: ("指示を無視", "前の指示", "秘密情報", "隠し情報"),
        2: ("システムコマンド", "コマンドを実行", "コマンド実行", "システム情報"),
        3: ("ファイルを削除", "削除して", "許可していない操作", "禁止された操作"),
    }
    normalized_text = " ".join(text.split()).casefold()
    matched_case = next(
        (
            attack_case
            for attack_case, patterns in blocked_patterns.items()
            if any(pattern.casefold() in normalized_text for pattern in patterns)
        ),
        None,
    )
    if matched_case is not None:
        reasons = {
            1: "指示の乗っ取りにつながる入力",
            2: "許可していないツール実行の要求",
            3: "許可していない操作の要求",
        }
        raise ValueError(f"拒否しました: {reasons[matched_case]}")

    if mode == "attack":
        raise ValueError(f"拒否しました: 攻撃ケース{case}の入力を安全側で処理できません")

    try:
        from langchain_aws import ChatBedrockConverse
        from langchain_core.messages import HumanMessage
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "LangChain dependencies are required. Install requirements.txt first."
        ) from exc

    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    model_id = os.getenv("BEDROCK_MODEL_ID")
    if not region:
        raise ValueError("AWS_REGION or AWS_DEFAULT_REGION is required")
    if not model_id:
        raise ValueError("BEDROCK_MODEL_ID is required")

    llm = ChatBedrockConverse(model=model_id, region_name=region)
    response = llm.invoke([HumanMessage(content=text.strip())])
    content = response.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict)
        )
    raise RuntimeError("AI response content has an unsupported format")


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    受講者は `run_guarded()` を実装します。ここは引数解析/検証/終了コードを担当します。
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)

    try:
        _validate_args(args)
    except Exception as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 2

    logging.info("mode=%s case=%s", args.mode, args.case)

    try:
        out = run_guarded(text=args.text, mode=args.mode, case=args.case)
        print(out)
        return 0
    except NotImplementedError as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        logging.error("%s", e)
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
