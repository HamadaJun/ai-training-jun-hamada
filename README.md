# 若手AIエンジニア研修（テンプレート）

## 前提条件

| ツール | バージョン | 備考 |
|--------|-----------|------|
| Python | 3.10 以上 | `python3 --version`（Windows: `python --version`）で確認 |
| Git | 2.x | `git --version` で確認 |
| AWS CLI | v2 | `aws --version` で確認。認証設定は `training-requirements.md` 参照 |

## Quickstart（最短導線）

受講者は基本的に「その日の `README` を読む → `app.py` を編集する → 画面 or CLIで動作確認 → PR提出」の繰り返しです。

### 1) 今日やるDayを決める

- `day01/README.md` 〜 `day10/README.md` のいずれかを開きます

### 2) 編集するファイルは原則この2つだけ

- **実装**：`dayXX/app.py`
- **提出用メモ**：`dayXX/README.md`

### 3) 動作確認（おすすめ：共通画面）

0. `.env.example` を `.env` にコピーして値を設定
   - `.env` はコミットしません

1. venvを作成・有効化（初回のみ）
   - `python3 -m venv .venv`（Windows: `python -m venv .venv`）
   - `source .venv/bin/activate`（Windows: `.venv\Scripts\activate`）
   - `pip install -U pip`

2. 依存関係をインストール
   - `pip install -r requirements.txt`

3. Runner APIを起動
   - `uvicorn backend.main:app --reload --port 8000`

4. 共通画面を起動
   - `streamlit run ui/app.py`

5. メニューからDayを選んで入力→実行

### 4) 代替：CLIで直接動作確認

- 例（Day02）
  - `python -m day02.app --prompt "Hello" --region <region> --model-id <model_id>`

---

## ドキュメント

- `training-requirements.md`：研修要件
- `curriculum.md`：カリキュラム
- `assignments.md`：課題一覧
- `github-operation.md`：GitHub運用
- `self-review-checklist.md`：セルフレビュー

---

## 共通画面（UI） + 課題ランナー（FastAPI）

このテンプレートには、各Day課題のCLIを共通画面から実行して、結果（stdout/stderr/exit code）を確認できるフレームが含まれます。

### 1. 依存関係の導入

- venvを作成・有効化（初回のみ）
  - `python3 -m venv .venv`（Windows: `python -m venv .venv`）
  - `source .venv/bin/activate`（Windows: `.venv\Scripts\activate`）
  - `pip install -U pip`
- 依存関係をインストール
  - `pip install -r requirements.txt`

### 2. Runner API（FastAPI）起動

- `uvicorn backend.main:app --reload --port 8000`

起動確認：

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

### 3. 共通画面（Streamlit）起動

- `streamlit run ui/app.py`

### 4. 最終課題のチャットUI

- `streamlit run final/chat_ui.py`

---

## 受講者が実装する場所

各Dayの課題は、`python -m dayXX.app` のCLIとして実装します。

- 例：Day02は `day02/app.py` を編集し、`python -m day02.app --prompt ...` が動くように実装します。

---

## よくある詰まりポイント

- Runner APIを起動していない
  - `uvicorn backend.main:app --reload --port 8000` を起動してください
- 共通画面がRunner APIに繋がらない
  - `ui/app.py` の左メニュー `Runner API base URL` が `http://127.0.0.1:8000` になっているか確認してください
- Dayを実装していないのに共通画面から実行した
  - `NotImplementedError` が出ます。`dayXX/app.py` の未実装関数（docstring付き）を埋めてください
