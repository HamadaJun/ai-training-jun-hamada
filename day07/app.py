from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from typing import Any, List, Literal, TypedDict


class GraphState(TypedDict, total=False):
    input: str
    intent: str
    reason: str
    reason_code: str
    output: str
    errors: List[str]


def build_parser() -> argparse.ArgumentParser:
    """Day07のCLI引数を定義します（入力と分類モード）。"""
    p = argparse.ArgumentParser(prog="day07")
    p.add_argument("--text", required=True)
    p.add_argument("--mode", choices=["llm", "rule"], default="rule")
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.text:
        raise ValueError("--text is required")


def run_graph(*, text: str, mode: str) -> str:
    """LangGraphで「分類→分岐→処理」を実行し、最終出力（文字列）を返します。

    mode:
    - `rule`：ルール（キーワード等）でintentを決めて分岐
    - `llm`：LLMでintentを分類して分岐

    受け入れ基準（README）：
    - 分岐が最低2パターンある
    - どの分岐に入ったかがログで分かる
    - 分類不能時のフォールバックがある
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("--text is required")
    if mode not in {"rule", "llm"}:
        raise ValueError("--mode must be rule or llm")

    try:
        from langgraph.graph import END, START, StateGraph
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "LangGraph is required. Install requirements.txt first."
        ) from exc

    def classify_by_rule(state: GraphState) -> GraphState:
        value = state["input"].casefold()
        patterns = {
            "summarize": ("要約", "まとめて", "短くして", "要点"),
            "plan": ("手順", "実装", "分解", "計画", "やり方"),
            "rag": ("教えて", "調べて", "について", "検索", "知りたい"),
        }
        for intent, keywords in patterns.items():
            matched = next((keyword for keyword in keywords if keyword in value), None)
            if matched:
                return {
                    "intent": intent,
                    "reason": f"キーワード「{matched}」を検出",
                    "reason_code": "keyword_match",
                }
        return {
            "intent": "rag",
            "reason": "該当キーワードがないためデフォルト分岐",
            "reason_code": "default_fallback",
        }

    def classify_by_llm_unsafe(state: GraphState) -> GraphState:
        try:
            from langchain_aws import ChatBedrockConverse
            from langchain_core.messages import HumanMessage
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "LangChain AWS dependencies are required for --mode llm."
            ) from exc

        region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
        model_id = os.getenv("BEDROCK_MODEL_ID")
        if not region or not model_id:
            raise ValueError(
                "--mode llm requires AWS_REGION and BEDROCK_MODEL_ID"
            )
        prompt = (
            "Classify the following Japanese request as exactly one of "
            "rag, summarize, plan. Reply with only the label.\n\n"
            f"Request: {state['input']}"
        )
        response = ChatBedrockConverse(
            model=model_id, region_name=region
        ).invoke([HumanMessage(content=prompt)])
        content: Any = response.content
        if isinstance(content, list):
            content = "".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict)
            )
        intent_match = re.search(r"\b(rag|summarize|plan)\b", str(content).casefold())
        if not intent_match:
            return {
                "intent": "rag",
                "reason": "LLMの分類結果を解釈できないためデフォルト分岐",
                "reason_code": "llm_result_unrecognized",
            }
        intent = intent_match.group(1)
        return {
            "intent": intent,
            "reason": f"LLMの分類結果: {intent}",
            "reason_code": "llm_classification",
        }

    def classify_by_llm(state: GraphState) -> GraphState:
        try:
            return classify_by_llm_unsafe(state)
        except Exception as exc:
            error = f"classify: {type(exc).__name__}: {exc}"
            logging.error(error)
            return {
                "intent": "rag",
                "reason": "LLM分類でエラーが発生したためデフォルト分岐",
                "reason_code": "llm_error_fallback",
                "errors": state.get("errors", []) + [error],
            }

    def log_classification(state: GraphState) -> GraphState:
        logging.info(
            "state_updated keys=%s branch=%s reason_code=%s reason=%s",
            ["intent", "reason", "reason_code"],
            state["intent"],
            state["reason_code"],
            state["reason"],
        )
        return {}

    def rag_node(state: GraphState) -> GraphState:
        return {"output": f"RAG分岐: 「{state['input']}」について調べる処理です。"}

    def summarize_node(state: GraphState) -> GraphState:
        return {"output": f"要約分岐: 「{state['input']}」を要約する処理です。"}

    def plan_node(state: GraphState) -> GraphState:
        return {"output": f"タスク分解分岐: 「{state['input']}」の手順を整理する処理です。"}

    def format_output(state: GraphState) -> GraphState:
        logging.info("output_ready intent=%s", state["intent"])
        return {}

    def route(state: GraphState) -> Literal["rag", "summarize", "plan"]:
        return state.get("intent", "rag")  # type: ignore[return-value]

    graph = StateGraph(GraphState)
    graph.add_node("classify", classify_by_llm if mode == "llm" else classify_by_rule)
    graph.add_node("log_classification", log_classification)
    graph.add_node("rag", rag_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("plan", plan_node)
    graph.add_node("format_output", format_output)
    graph.add_edge(START, "classify")
    graph.add_edge("classify", "log_classification")
    graph.add_conditional_edges(
        "log_classification", route, {"rag": "rag", "summarize": "summarize", "plan": "plan"}
    )
    for branch in ("rag", "summarize", "plan"):
        graph.add_edge(branch, "format_output")
    graph.add_edge("format_output", END)

    result = graph.compile().invoke({"input": text.strip(), "errors": []})
    output = result.get("output")
    if not isinstance(output, str):
        raise RuntimeError("Graph did not produce output")
    return output


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    受講者は `run_graph()` を実装します。ここは引数解析/検証/終了コードを担当します。
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)

    try:
        _validate_args(args)
    except Exception as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 2

    logging.info("mode=%s", args.mode)

    try:
        out = run_graph(text=args.text, mode=args.mode)
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
