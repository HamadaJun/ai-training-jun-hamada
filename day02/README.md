# Day 02

## 受講者が実装する場所

- `day02/app.py` の `invoke_bedrock()`

## 目的

- AWS BedrockでLLMを呼び出せるようにする
- 失敗時に原因切り分け（認証/権限/設定/ネットワーク）できるようにする
- モデル/リージョン/主要パラメータを設定として扱う習慣をつける

## ゴール（完了条件）

- `python -m day02.app --prompt "..."` が動く
- 失敗時に原因切り分けができる（ログ/メッセージがある）

## 機能要件

CLIは次の仕様を満たしてください。

コマンド

- `python -m day02.app` で起動できること（モジュール名は固定）

必須オプション

- `--prompt`：ユーザー入力（文字列、必須）

任意オプション

- `--region`：AWSリージョン（未指定の場合は環境変数 `AWS_REGION` を利用）
- `--model-id`：BedrockのモデルID（未指定の場合は環境変数 `BEDROCK_MODEL_ID` を利用）
- `--temperature`：温度（0.0〜1.0、デフォルト `0.2`）
- `--max-tokens`：最大トークン（整数、デフォルト `512`）
- `--timeout-sec`：タイムアウト秒（整数、デフォルト `30`）

出力

- 正常時：標準出力にモデルの回答本文のみを出力する
- 失敗時：標準エラー出力にエラーメッセージを出力する

終了コード

- 正常終了：`0`
- 入力不備（`--prompt` なし、型不正、範囲外など）：`2`
- Bedrock呼び出し失敗（認証/権限/ネットワーク/タイムアウト等）：`1`

ログ

- 実行開始時に、`region` / `model-id` / `temperature` / `max-tokens` / `timeout-sec` をINFOで出す
- 例外発生時に、例外種別と要点（原因切り分けに必要な情報）をERRORで出す

### エラー条件（最低限この3つを扱う）

- 入力不備（`--prompt` が空 or 未指定）
- AWS認証/権限系の失敗
- タイムアウト

## 実装タスク

- `day02/app.py` の `invoke_bedrock()` を実装し、機能要件を満たす
- `region` / `model-id` を引数または環境変数で扱えるようにする

## 実行方法

### 必要な環境変数

```bash
# 1. .env.example を .env にコピーして設定
cp .env.example .env

# 2. AWS認証（IAMユーザーのアクセスキーを使用）
#    ~/.aws/credentials に以下を設定（詳細は training-requirements.md 参照）
#    [training]
#    aws_access_key_id = AKIA...
#    aws_secret_access_key = ...
export AWS_PROFILE=training

# 3. リージョン・モデルID（.env で設定済みなら不要）
export AWS_REGION=ap-northeast-1
export BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

Windows（PowerShell）の場合：

```powershell
# 1. .env.example を .env にコピーして設定
copy .env.example .env

# 2. AWS認証
$env:AWS_PROFILE = "training"

# 3. リージョン・モデルID（.env で設定済みなら不要）
$env:AWS_REGION = "ap-northeast-1"
$env:BEDROCK_MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
```

### 実行コマンド例

```bash
# 基本的な実行
python -m day02.app --prompt "日本の首都はどこですか？"

# リージョンとモデルを明示的に指定
python -m day02.app --prompt "Hello" --region ap-northeast-1 --model-id anthropic.claude-3-haiku-20240307-v1:0

# パラメータを調整
python -m day02.app --prompt "短い俳句を作ってください" --temperature 0.8 --max-tokens 100
```

### 期待する出力例

```
日本の首都は東京です。
```

---

**以下は受講者が記入してください**

## 提出物

- `day02/app.py`
- `day02/README.md`

## セルフレビュー

- 正常系：短い入力で回答が返る
- 異常系：認証/権限がない場合に、原因が推測できるエラーになっている
- 境界：長文入力でもクラッシュせず、エラーなら理由が分かる
- 再実行：同じ入力を2回実行し、破綻しない（多少の揺れは許容）

## Bedrock確認

- モデル：
- リージョン：
- 主要パラメータ：

## リサーチメモ（任意）

調べたURLや、理解した要点をメモしてください。

- Bedrockのモデル呼び出し方法（boto3等）
- 利用する認証方式（研修の指示に従う）
- タイムアウト/リトライの考え方
