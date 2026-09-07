from __future__ import annotations

import argparse
from datetime import date
import logging
import os
import re
import sys
from typing import List


def build_parser() -> argparse.ArgumentParser:
    """Day04のCLI引数を定義します（ユーザー入力テキスト）。"""
    p = argparse.ArgumentParser(prog="day04")
    p.add_argument("--text", required=True)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.text:
        raise ValueError("--text is required")
    has_today_request = "今日" in args.text or "today" in args.text.lower()
    has_add_request = len(re.findall(r"[-+]?\d+", args.text)) == 2
    if not has_today_request and not has_add_request:
        raise ValueError("text must request today's date or contain exactly two integers")
    if has_today_request and has_add_request:
        raise ValueError("text must request either today or add, not both")


def run_chain(text: str) -> str:
    """LangChain + Tool calling を使って回答（文字列）を返します。

    この関数を実装すると、`python -m day04.app --text ...` が動くようになります。

    要件（READMEの受け入れ基準）：
    - `today` または `add` のツールを1つ実装し、LLMから1回以上呼び出す
    - ツール引数のバリデーションを入れる（不正なら実行しない）
    - ツール失敗時は安全に失敗する（例外でOK。mainがexit code=1にする）

    ヒント：
    - まずはツールをPython関数として作り、ログで「呼ばれた」ことを確認
    - 次にLLM側のプロンプトで「必要ならツールを使う」よう誘導
    """
    if not text or not text.strip():
        raise ValueError("text must not be empty")
    has_today_request = "今日" in text or "today" in text.lower()
    input_numbers = re.findall(r"[-+]?\d+", text)
    has_add_request = len(input_numbers) == 2
    if has_today_request == has_add_request:
        raise ValueError("text must request either today or add, not both")

    try:
        from langchain.tools import tool
        from langchain_aws import ChatBedrockConverse
        from langchain_core.messages import HumanMessage, ToolMessage
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "LangChain dependencies are required. Install requirements.txt first."
        ) from exc

    @tool
    def today() -> str:
        """Return today's date in ISO 8601 format."""
        result = date.today().isoformat()
        logging.info("tool call: today() -> %s", result)
        return result

    @tool
    def add(a: int, b: int) -> int:
        """Add two integers."""
        if isinstance(a, bool) or not isinstance(a, int):
            raise ValueError("a must be an integer")
        if isinstance(b, bool) or not isinstance(b, int):
            raise ValueError("b must be an integer")
        logging.info("tool call: add(a=%d, b=%d)", a, b)
        return a + b

    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    model_id = os.getenv("BEDROCK_MODEL_ID")
    if not region:
        raise ValueError("AWS_REGION or AWS_DEFAULT_REGION is required")
    if not model_id:
        raise ValueError("BEDROCK_MODEL_ID is required")

    llm = ChatBedrockConverse(
        model=model_id,
        region_name=region,
    )
    tools = [today, add]
    bound_llm = llm.bind_tools(tools, tool_choice="any")
    llm_with_tools = llm.bind_tools(tools)
    if has_today_request:
        expected_tool = "today"
        prompt = (
            f"ユーザー入力: {text}\n"
            "必ず today ツールを1回呼び出してください。"
            "today ツールには引数を渡さないでください。"
        )
    else:
        expected_tool = "add"
        prompt = (
            f"ユーザー入力: {text}\n"
            "必ず add ツールを1回呼び出してください。"
            "入力中の2つの整数をそのまま a と b に指定してください。"
        )
    tool_request = bound_llm.invoke([HumanMessage(content=prompt)])
    tool_calls = getattr(tool_request, "tool_calls", [])
    if not tool_calls:
        raise RuntimeError("LLM did not request the add tool")

    tool_call = next(
        (call for call in tool_calls if call.get("name") == expected_tool),
        None,
    )
    if tool_call is None:
        raise RuntimeError("LLM requested an unsupported tool")

    args = tool_call.get("args")
    if expected_tool == "today":
        if args not in (None, {}):
            raise ValueError("today does not accept arguments")
        result = today.invoke({})
    else:
        expected_args = {"a": int(input_numbers[0]), "b": int(input_numbers[1])}
        if (
            not isinstance(args, dict)
            or set(args) != {"a", "b"}
            or any(isinstance(args[key], bool) or not isinstance(args[key], int) for key in ("a", "b"))
            or args != expected_args
        ):
            raise ValueError("add requires the two integer arguments from the input")
        result = add.invoke(args)
    tool_result = ToolMessage(
        content=str(result),
        tool_call_id=tool_call["id"],
    )
    final_response = llm_with_tools.invoke(
        [HumanMessage(content=prompt), tool_request, tool_result]
    )
    content = final_response.content
    if isinstance(content, str):
        return content
    return "".join(
        block.get("text", "")
        for block in content
        if isinstance(block, dict) and isinstance(block.get("text"), str)
    )


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    受講者は `run_chain()` の実装に集中し、ここは原則編集しません。
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

    try:
        out = run_chain(args.text)
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
