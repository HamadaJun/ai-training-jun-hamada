from __future__ import annotations

import argparse
import logging
from pathlib import Path
import re
import sys
from typing import List, Tuple


def build_parser() -> argparse.ArgumentParser:
    """Day05のCLI引数を定義します（質問文）。"""
    p = argparse.ArgumentParser(prog="day05")
    p.add_argument("--question", required=True)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.question or not args.question.strip():
        raise ValueError("--question is required")


def answer_with_rag(question: str) -> str:
    """RAGで質問に回答し、指定フォーマットのテキストを返します。

    この関数を実装すると、`python -m day05.app --question ...` が動くようになります。

    要件（READMEの出力フォーマット）：
    - 標準出力に次の形で出すための文字列を返す
      1) `Answer:` 行
      2) `Sources:` 行
      3) `- <URL or ファイル名> (excerpt: "...")` を最低1件（ヒットなしなら `- (none)`）

    実装ガイド：
    - `day05/data/` 配下の `.txt` を読み込み、検索対象とする
    - 最初は単純なキーワード検索でもOK（高品質でなくてよい）
    - ヒットがない場合の挙動を必ず実装する
    """
    normalized_question = " ".join(question.split())
    if not normalized_question:
        raise ValueError("question must not be empty")

    data_dir = Path(__file__).parent / "data"
    documents = sorted(data_dir.glob("*.txt"))
    if not documents:
        raise FileNotFoundError(f"no .txt documents found in {data_dir}")

    question_terms = {
        term.casefold()
        for term in re.findall(r"[A-Za-z0-9_]+|[ぁ-んァ-ン一-龯]{2,}", normalized_question)
    }
    matches: List[Tuple[Path, str, int]] = []
    for document in documents:
        content = document.read_text(encoding="utf-8")
        for line_number, line in enumerate(content.splitlines(), start=1):
            excerpt = line.strip()
            if not excerpt:
                continue
            score = sum(term in excerpt.casefold() for term in question_terms)
            if score:
                matches.append((document, excerpt, score))

    matches.sort(key=lambda item: item[2], reverse=True)
    if not matches:
        return (
            "Answer: 該当する根拠が見つかりませんでした。\n"
            "Sources:\n"
            "- (none)"
        )

    selected = matches[:3]
    answer = selected[0][1]
    source_lines = [
        f'- day05/data/{document.name} (excerpt: "{excerpt}")'
        for document, excerpt, _ in selected
    ]
    return "Answer: " + answer + "\nSources:\n" + "\n".join(source_lines)


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    受講者は `answer_with_rag()` を実装します。
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
        out = answer_with_rag(args.question)
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
