from __future__ import annotations

from typing import Any, Dict, List


def run_agent(message: str, history: List[Dict[str, str]] | None = None) -> Dict[str, Any]:
    """チャットUI（`final/chat_ui.py`）から呼び出されるエージェントの入口です。

    受講者が実装する場所は基本的にこの関数（またはこの関数が呼ぶ下位関数）です。

    実装の方針（例）：
    - LangGraphでstateを持つフローを構築
    - ツール（RAG検索、計算、日付取得など）をTool callingで呼び出す
    - 失敗時フォールバック（検索ヒットなし、JSON破損など）を入れる

    引数：
    - message: ユーザーの最新発話
    - history: これまでの会話履歴（role/contentの配列）

    戻り値（辞書）：
    - reply: str（ユーザーに見せる本文）
    - meta: dict（任意。デバッグ用情報や構造化出力を入れてよい）

    注意：
    - APIキーや認証情報をコードに直書きしない
    - 例外は握りつぶさず、UI側で原因が分かるよう meta に入れるか適切にエラー化する
    """
    # TODO(TRAINEE): Replace this stub with your LangGraph agent implementation.
    history = history or []
    return {
        "reply": "(agent not implemented yet) You said: " + message,
        "meta": {"history_len": len(history)},
    }
