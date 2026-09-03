# 参考ドキュメント

LangChain / LangGraph の公式ドキュメント（Python）と、研修で理解しやすいように
「何を・なぜ・どう使うか」を丁寧に説明し、実コード中心でサンプルをまとめます。

## LangChain

- どんなものか:
  - LLM呼び出しや前後処理を「Runnable」や「Chain」でつなげ、入出力のパイプラインを作るためのライブラリ。
  - 「入力 → プロンプト → LLM → 解析/整形」という流れを、可読性の高い形で書けるのが強み。
- 研修での使い所:
  - Day04の「ツール呼び出しの入口」「入出力の流れを整理する」の学習に相当。
  - 小さく分けて組み上げる思想が、後のLangGraph（状態遷移）にもつながる。
- 公式ドキュメント（Overview）: `https://docs.langchain.com/oss/python/langchain/overview`
- Install: `https://docs.langchain.com/oss/python/langchain/install`
- Quickstart: `https://docs.langchain.com/oss/python/langchain/quickstart`
- API Reference（Python）: `https://reference.langchain.com/python/`

### サンプル1: プロンプト → LLM → 出力整形の最小構成

ポイント:
- `ChatPromptTemplate` で「プロンプトの型」を固定する
- LLMは `ChatBedrock`（AWS）または `ChatOpenAI` などに差し替え可能
- `StrOutputParser()` でメッセージを文字列に戻す

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Bedrockを使う場合（研修で推奨）
# from langchain_aws import ChatBedrock
# llm = ChatBedrock(model_id="anthropic.claude-3-5-sonnet-20240620-v1:0")

# OpenAIを使う場合（比較用）
# from langchain_openai import ChatOpenAI
# llm = ChatOpenAI(model="gpt-4o-mini")

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a concise assistant."),
        ("user", "Q: {question}\nA:"),
    ]
)

chain = prompt | llm | StrOutputParser()

result = chain.invoke({"question": "RAGとは？"})
print(result)
```

### サンプル2: Tool呼び出しの最小例（関数を道具化）

ポイント:
- `@tool` を付けた関数は「ツール」として扱える
- 実際の検索処理・DB問い合わせ・ファイル読込などをツール化して使う

```python
from langchain_core.tools import tool

@tool
def search_docs(query: str) -> str:
    # 本来は検索処理を実装する
    return f"[search result for: {query}]"

print(search_docs.invoke({"query": "RAG"}))
```

## LangGraph

- どんなものか:
  - 複数ステップの処理を「状態（state）」として保持し、ノードとエッジで状態遷移を表現するフレームワーク。
  - 「今どんな情報を保持しているか」を明示できるため、分岐や失敗時復帰に強い。
- 研修での使い所:
  - Day07/08の「条件分岐」「失敗時フォールバック」の構造化。
  - ログや失敗理由を state に残すことで、原因追跡がしやすい。
- 公式ドキュメント（Overview）: `https://docs.langchain.com/oss/python/langgraph/overview`
- Install: `https://docs.langchain.com/oss/python/langgraph/install`
- Quickstart: `https://docs.langchain.com/oss/python/langgraph/quickstart`
- API Reference（Python）: `https://reference.langchain.com/python/langgraph/`

### サンプル1: 直列2ステップの状態遷移

ポイント:
- `State` に入出力を保持する
- ノード関数は「stateを受けてstateを返す」形にする

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    question: str
    answer: str

def step_answer(state: State) -> State:
    return {"question": state["question"], "answer": f"Q={state['question']} / A=..."}

def step_finalize(state: State) -> State:
    return state

g = StateGraph(State)
g.add_node("answer", step_answer)
g.add_node("finalize", step_finalize)
g.set_entry_point("answer")
g.add_edge("answer", "finalize")
g.add_edge("finalize", END)

app = g.compile()
print(app.invoke({"question": "RAGとは？"}))
```

### サンプル2: 条件分岐（RAGヒット有無で分岐）

ポイント:
- `add_conditional_edges` で分岐を定義する
- state に判断材料（例: `has_hit`）を入れると分岐が明確になる

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    question: str
    has_hit: bool
    answer: str

def classify(state: State) -> State:
    # 本来は検索結果の有無で判定する
    return {"question": state["question"], "has_hit": "RAG" in state["question"], "answer": ""}

def rag(state: State) -> State:
    return {**state, "answer": "RAGの根拠付き回答..."}

def fallback(state: State) -> State:
    return {**state, "answer": "根拠が見つからないため追加質問が必要です。"}

g = StateGraph(State)
g.add_node("classify", classify)
g.add_node("rag", rag)
g.add_node("fallback", fallback)
g.set_entry_point("classify")
g.add_conditional_edges("classify", lambda s: "rag" if s["has_hit"] else "fallback")
g.add_edge("rag", END)
g.add_edge("fallback", END)

app = g.compile()
print(app.invoke({"question": "RAGとは？"}))
```
