from __future__ import annotations

import argparse
import logging
import sys
from typing import List, Literal, TypedDict


class GraphState(TypedDict, total=False):
    input: str
    status: str
    output: str
    errors: List[str]
    steps: int
    retries: int
    failure_kind: str


def build_parser() -> argparse.ArgumentParser:
    """Day08のCLI引数を定義します（入力と上限設定）。"""
    p = argparse.ArgumentParser(prog="day08")
    p.add_argument("--text", required=True)
    p.add_argument("--max-steps", type=int, default=10)
    p.add_argument("--max-retry", type=int, default=1)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.text:
        raise ValueError("--text is required")
    if not (1 <= args.max_steps <= 50):
        raise ValueError("--max-steps must be between 1 and 50")
    if not (0 <= args.max_retry <= 5):
        raise ValueError("--max-retry must be between 0 and 5")


def run_graph(*, text: str, max_steps: int, max_retry: int) -> str:
    """失敗時復帰（リトライ/フォールバック）付きのフローを実行します。

    実装ガイド：
    - 失敗パターンを1つ以上作り、復帰パスへ入ることを確認する
      - 例：JSONが壊れる→再生成
      - 例：検索ヒットなし→聞き返し
    - `max_steps` / `max_retry` を上限として必ず反映し、無限ループを防ぐ
    - 上限到達時は明示的に失敗（例外）してよい（mainがexit code=1にする）
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("--text is required")
    if not 1 <= max_steps <= 50:
        raise ValueError("--max-steps must be between 1 and 50")
    if not 0 <= max_retry <= 5:
        raise ValueError("--max-retry must be between 0 and 5")

    try:
        from langgraph.graph import END, START, StateGraph
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "LangGraph is required. Install requirements.txt first."
        ) from exc

    def attempt(state: GraphState) -> GraphState:
        steps = state.get("steps", 0) + 1
        if steps > max_steps:
            raise RuntimeError(f"最大ステップ数に到達しました: {max_steps}")

        value = state["input"].casefold()
        errors = state.get("errors", [])
        if "不完全なjson" in value:
            error = f"JSONパース失敗 (retry={state.get('retries', 0)})"
            logging.warning("step=%s failure=json_parse", steps)
            if state.get("retries", 0) < max_retry:
                return {
                    "status": "retry",
                    "failure_kind": "json_parse",
                    "steps": steps,
                    "retries": state.get("retries", 0) + 1,
                    "errors": errors + [error],
                }
            return {
                "status": "fallback",
                "failure_kind": "json_parse",
                "steps": steps,
                "errors": errors + [error],
            }

        if "存在しない情報" in value or "検索ヒットなし" in value:
            logging.warning("step=%s failure=search_no_hit", steps)
            return {
                "status": "fallback",
                "failure_kind": "search_no_hit",
                "steps": steps,
                "errors": errors + ["検索結果なし"],
            }

        logging.info("step=%s status=success", steps)
        return {
            "status": "success",
            "steps": steps,
            "output": f"処理が完了しました: {state['input']}",
        }

    def retry(state: GraphState) -> GraphState:
        logging.info(
            "retry=%s/%s failure=%s",
            state.get("retries", 0),
            max_retry,
            state.get("failure_kind", "unknown"),
        )
        return {}

    def fallback(state: GraphState) -> GraphState:
        if state.get("failure_kind") == "json_parse":
            output = "JSONを解釈できなかったため、簡易形式で処理しました。"
        else:
            output = "検索結果が見つかりませんでした。別のキーワードを指定してください。"
        logging.info("fallback failure=%s", state.get("failure_kind", "unknown"))
        return {"output": output}

    def route(state: GraphState) -> Literal["retry", "fallback", "success"]:
        return state.get("status", "fallback")  # type: ignore[return-value]

    graph = StateGraph(GraphState)
    graph.add_node("attempt", attempt)
    graph.add_node("retry", retry)
    graph.add_node("fallback", fallback)
    graph.add_edge(START, "attempt")
    graph.add_conditional_edges(
        "attempt",
        route,
        {"retry": "retry", "fallback": "fallback", "success": END},
    )
    graph.add_edge("retry", "attempt")
    graph.add_edge("fallback", END)

    result = graph.compile().invoke(
        {"input": text.strip(), "errors": [], "steps": 0, "retries": 0}
    )
    output = result.get("output")
    if not isinstance(output, str):
        raise RuntimeError("処理結果を生成できませんでした")
    return output


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    受講者は `run_graph()` を実装します。ここは引数解析/検証/上限の適用/終了コードを担当します。
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)

    try:
        _validate_args(args)
    except Exception as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 2

    logging.info("max-steps=%s max-retry=%s", args.max_steps, args.max_retry)

    try:
        out = run_graph(text=args.text, max_steps=args.max_steps, max_retry=args.max_retry)
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
