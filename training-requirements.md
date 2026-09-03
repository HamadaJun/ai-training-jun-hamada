# 研修要件（確定版・ドラフト）：新入社員向け / AWS Bedrock / 公開データRAG / 2〜3週間

## 1. 前提

- 受講者：新入社員メイン（未経験者想定）
- LLM基盤：AWS Bedrock（社内AWS環境で利用可能）
- 社内ドキュメント：利用不可
- RAGを行う場合：公開データを用いる（出典/ライセンス確認を含む）
- 研修ゴール：今後のAI案件に参画できる基礎体力（実装・設計・検証・改善の流れを一通り経験）

---

## 2. 研修の目的

- Python未経験者を、LLMアプリ/エージェント開発の実装担当として立ち上げる
- Bedrockを前提に、LLMアプリの作法（安全性・評価・運用観点）を最初から身につける
- LangChain / LangGraphを用い、「ツール実行 + 状態遷移 + 失敗時の復帰」を含む最小実用エージェントを作れるようにする
- 以下を獲得できている状態を目指し、開発案件やAIコンサル案件への参画につなげる
  - AIに関する基礎的な知識の獲得
  - AIを活用した開発（コーディングやテスト、設計）
  - AIエージェントのアーキテクチャ理解
  - 簡単なAIエージェントの開発
  - AWSで構築する際のアーキテクチャ理解

---

## 3. 到達目標

### 3.1 Must（必須到達）

- AIに関する基礎的な知識を説明できる
  - 代表的な用語（LLM、トークン、コンテキスト、温度、Embedding、RAG、Tool calling、評価）
  - 品質/コスト/レイテンシ/安全性の基本的なトレードオフ
- Pythonでアプリ開発の基礎ができる
  - 仮想環境、依存管理、型/例外、ファイルI/O、HTTP/JSON、ログ
- BedrockでLLM呼び出しができる
  - boto3/SDK利用、モデル指定、パラメータ調整、エラー処理、コスト意識
- AIを活用した開発ができる
  - LLMを使ったコーディング支援（分解、実装、リファクタ、レビュー観点の整理）
  - テスト作成/テスト観点の洗い出し（正常系・異常系・回帰）
  - 設計の言語化（要件→インターフェース→実装の流れ）
- LLMアプリの基本設計ができる
  - プロンプト設計、構造化出力（JSON/Pydantic）、入力バリデーション、失敗パターンの把握
- LangChainでチェーン/ツール呼び出しを組める
  - Prompt + Model + Parser、Tool calling、（必要に応じて）Retriever連携
- LangGraphでエージェントを構築できる
  - state設計、node/edge、条件分岐、リトライ/フォールバック、簡易ガード
- AIエージェントのアーキテクチャを説明できる
  - Planner/Executor、ReAct、ツール実行、状態遷移、メモリ/コンテキスト管理、ガード
  - 失敗パターン（幻覚、ツール誤用、ループ、コンテキスト不足）と基本対策
- 公開データでRAGを構築できる（RAG採用時）
  - 分割、埋め込み、ベクトル検索、根拠提示（引用/参照元）
- 簡易評価と改善ができる
  - テストケース作成、失敗分類、ログ/トレースで原因特定、改善案の反映

### 3.2 Should（できると良い）

- プロンプトインジェクション等の攻撃/事故パターンを想定し、対策（制限・サニタイズ・許可リスト）を入れられる
- 速度/コストの最適化（短いプロンプト、キャッシュ、段階的推論など）を1つでも実施できる

---

## 4. 成果物（Deliverables）

- 最終課題アプリ（必須）
  - LangGraphベースのエージェント
  - Tool calling（少なくとも1つ以上）
  - 構造化出力（JSON等）
  - 失敗時の挙動（リトライ or フォールバック）を実装
  - （RAG採用時）公開データを使い、出典を提示
- README（必須）
  - セットアップ、実行方法、環境変数（AWS認証/リージョン等）、注意点
- 設計メモ（必須）
  - 状態遷移図、主要プロンプト、失敗例と対策、評価結果（簡易でOK）

---

## 4.1 GitHub運用要件（受講者向け）

- このリポジトリをGitHubにPushし、受講者はGitHub上で課題提出/レビューを行う
- 提出物
  - 各課題：指定ディレクトリ配下にコード/ノート（必要なら）/短い振り返り
  - 最終課題：アプリ一式 + README + 設計メモ
- ブランチ運用（推奨）
  - 受講者は課題ごとにブランチを切り、Pull Requestで提出する
  - レビューコメントを受け、必要に応じて修正してマージする
- 秘密情報の取り扱い
  - APIキー/認証情報をコミットしない（環境変数またはローカル設定のみ）
  - ログ/成果物に機密情報や個人情報を含めない
- 再現性
  - READMEにセットアップ/実行方法を記載し、第三者が手順どおりに動かせる状態にする
  - 依存関係とPythonバージョンを明記する

## 5. AWS Bedrock前提の要件（運用/安全含む）

### 5.1 認証・権限

運営は以下のいずれかの認証方式を事前に決定し、受講者に周知する。

#### 認証方式の選択肢

**A) IAMユーザー（アクセスキー）— 推奨**

**手順1：アクセスキーの発行（運営が実施）**

1. AWS Console > **IAM** > **ユーザー** > 対象ユーザーを選択
2. **セキュリティ認証情報** タブ > **アクセスキーを作成**
3. `Access Key ID`（`AKIA...`）と `Secret Access Key` を控える

> Secret Access Key は作成時にしか表示されないため、必ずこの時点で保存すること

**手順2：ローカルPCに認証情報を設定（受講者が実施）**

```bash
aws configure --profile training
# 以下を対話形式で入力：
#   AWS Access Key ID: AKIA...
#   AWS Secret Access Key: xxxxxxxx
#   Default region name: ap-northeast-1
#   Default output format: json
```

上記コマンドにより `~/.aws/credentials`（Windows: `C:\Users\<ユーザー名>\.aws\credentials`）に以下が設定される：

```ini
[training]
aws_access_key_id = AKIA...
aws_secret_access_key = ...
```

**手順3：プロファイルの有効化**

```bash
export AWS_PROFILE=training
```

Windows（PowerShell）の場合：

```powershell
$env:AWS_PROFILE = "training"
```

**手順4：動作確認**

```bash
# 認証が通るか確認
aws sts get-caller-identity

# Bedrockのモデル一覧が取れるか確認
aws bedrock list-foundation-models --region ap-northeast-1 --query "modelSummaries[].modelId" --output table
```

> 注意：アクセスキーは研修終了後に無効化すること

**B) IAM Identity Center（SSO）**

```bash
aws configure sso --profile training
# 初回設定後:
aws sso login --profile training
export AWS_PROFILE=training
```

Windows（PowerShell）の場合：

```powershell
aws configure sso --profile training
# 初回設定後:
aws sso login --profile training
$env:AWS_PROFILE = "training"
```

**C) AssumeRole（既存ロールを一時的に引き受ける）**

```bash
aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/BedrockTrainingRole \
  --role-session-name training-session
# 返却された一時認証情報を環境変数に設定
export AWS_ACCESS_KEY_ID=<AccessKeyId>
export AWS_SECRET_ACCESS_KEY=<SecretAccessKey>
export AWS_SESSION_TOKEN=<SessionToken>
```

Windows（PowerShell）の場合：

```powershell
aws sts assume-role `
  --role-arn arn:aws:iam::123456789012:role/BedrockTrainingRole `
  --role-session-name training-session
# 返却された一時認証情報を環境変数に設定
$env:AWS_ACCESS_KEY_ID = "<AccessKeyId>"
$env:AWS_SECRET_ACCESS_KEY = "<SecretAccessKey>"
$env:AWS_SESSION_TOKEN = "<SessionToken>"
```

#### 最小権限IAMポリシー例

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvoke",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:ap-northeast-1::foundation-model/*"
    },
    {
      "Sid": "BedrockListModels",
      "Effect": "Allow",
      "Action": [
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    }
  ]
}
```

> 本番環境では `Resource` を特定モデル（例: `arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0`）に限定することを推奨

### 5.2 モデル選定の扱い

- 研修では「推奨モデル（1〜2種）」を固定し、混乱を避ける
- モデル差分（応答品質/コスト/レイテンシ）を比較するミニ演習を入れる

### 5.3 コスト管理

- 1人あたりの日次上限や「やってはいけない使い方（無限ループ、巨大プロンプト）」を明文化
- ログに推定トークン/呼び出し回数を残す（可能な範囲で）

### 5.4 安全設計（最低限）

- ツール実行は許可リストで制限（実行可能コマンドや外部アクセスを無制限にしない）
- 重要情報を入力しない/ログに残さない（PII/機密）
- プロンプトインジェクション対策の基本（命令の優先順位、コンテキストの分離）

---

## 6. 研修スコープ

### 6.1 In scope

- Python基礎、LLMアプリ基礎、Bedrock呼び出し
- LangChain / LangGraph（エージェント構築）
- 公開データを使ったRAG（必要に応じて）
- デバッグ、評価、改善サイクル

### 6.2 Out of scope（深追いしない）

- 学習（Fine-tuning等）中心
- 大規模MLOps/本番運用の完全構築（ただし観点は触れる）
- 社内データ連携（今回は不可）

---

## 7. 評価基準（Rubricの骨子）

- 動作：再現手順どおりに動く / 想定ケースを満たす
- 設計：state設計と分岐が妥当 / 失敗時挙動がある
- 品質：入力検証、例外処理、ログ、構造化出力
- 安全性：ツール制限、データ取り扱い配慮
- 改善：失敗例→原因→対策の記録がある

---

## 8. 公開データRAGの方針（データ例）

- データ条件
  - ライセンスが明確
  - 文書構造が扱いやすい（PDF/HTML/markdown等）
  - 参照元URLを提示できる
- 例（候補）
  - 公開ドキュメント（政府統計の解説、自治体公開資料、製品マニュアル、OSSドキュメント等）
  - Wikipedia等は可否判断が必要（方針次第）
