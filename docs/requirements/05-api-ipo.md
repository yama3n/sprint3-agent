# API・IPO一覧（詳細設計）: 引合書整理エージェント

> Vモデル: 詳細設計 / 対応する検証: 単体テスト
> 先にAPIの全体像（一覧・認証）を示し、その上で業務フローごとのデータの流れ（Input/Process/Output）がどのAPIで実現されるかを整理する。

> 認証・認可の方針（認証方式・トークン有効期限・権限モデル）は `02-requirement.md` 4章 非機能要件（セキュリティ）で定義する。ローカル・単一ユーザーのPoCを前提とし、ロール別の権限モデルは持たない（`user` = ログイン済みの唯一のユーザー）。ここでは各APIが「認証を要するか・どの権限が必要か」を詳細設計として整理する。
>
> AGENT-01／AGENT-02（`agent-plan.md`）自体はフロントエンドから直接呼び出すツールではなく、引合作成・資料追加のAPI呼び出しをトリガーにバックエンド内で起動されるバックグラウンド処理として扱う。そのため両エージェントの「ツール一覧」はREST APIとしては公開せず、進捗の可視化のみ `GET /inquiries/{inquiry_id}/agent-status` で提供する（`agent_runs`テーブルを参照）。

## 1. API一覧

| # | エンドポイント | メソッド | 機能 | 認証 | 必要権限 |
|---|--------------|---------|------|------|---------|
| 1 | `/auth/login` | POST | ログイン（SCR-00） | 不要 | - |
| 2 | `/auth/logout` | POST | ログアウト（SCR-00〜05共通ヘッダー） | 要 | user |
| 3 | `/inquiries` | GET | 引合一覧取得・状態フィルタ（FUNC-05, FUNC-07／SCR-01） | 要 | user |
| 4 | `/inquiries` | POST | 書類アップロード・引合自動生成（FUNC-01／SCR-02） | 要 | user |
| 5 | `/inquiries/{inquiry_id}` | GET | 引合詳細取得（FUNC-02〜07／SCR-03） | 要 | user |
| 6 | `/inquiries/{inquiry_id}/files` | POST | 資料追加アップロード（FUNC-01／SCR-05） | 要 | user |
| 7 | `/inquiries/{inquiry_id}/agent-status` | GET | エージェント処理進捗取得（SCR-02進捗表示） | 要 | user |
| 8 | `/inquiries/{inquiry_id}/fields/{field_id}` | PATCH | 案件全体項目（A項目）の値修正・確定（FUNC-08／SCR-04） | 要 | user |
| 9 | `/inquiries/{inquiry_id}/items/{item_id}/fields/{field_id}` | PATCH | 品目項目（B項目）の値修正・確定（FUNC-08／SCR-04） | 要 | user |
| 10 | `/inquiries/{inquiry_id}/confirm` | POST | 成果物確定（構造化JSONをfinalへ）（FUNC-09／SCR-03） | 要 | user |
| 11 | `/inquiries/{inquiry_id}/exports` | POST | 出力形式選択・成果物生成（FUNC-05, FUNC-09／SCR-03） | 要 | user |
| 12 | `/inquiries/{inquiry_id}/exports/{export_id}/download` | GET | 成果物ダウンロード（FUNC-05／SCR-03） | 要 | user |

> フローは「ユースケース（ユーザーが1つの目的を達成する単位）」で切る。開始トリガーから結果が出るまでを1フローとし、画面・APIを複数跨いでよい。粒度は 02-requirement.md の機能のまとまりとほぼ対応する。

### FLOW-01 新規アップロード〜自動整理

**対応機能(②)**: FUNC-01, FUNC-02, FUNC-03, FUNC-04, FUNC-06, FUNC-07

| ステップ | Input | Process | Output | 対応API | 対応テーブル(④) |
|---------|-------|---------|--------|---------|----------------|
| 1 | 担当者が選択したファイル一式（xlsx/pdf/eml混在可） | ファイル形式を検証し、引合IDを新規発行してファイルを保存する | 新規引合レコード＋アップロード済みファイル一覧 | `POST /inquiries` | `inquiries`, `inquiry_files` |
| 2 | 保存されたファイル一式（バックグラウンド起動） | AGENT-01がファイルをパースし、固定項目（A14/B8/拡張項目2種）の候補値・出典を抽出する | ExtractionResultの保存、実行ログの記録 | （バックエンド内部処理。フロントからは呼び出さない） | `parsed_documents`, `extraction_results`, `agent_runs` |
| 3 | ExtractionResult | AGENT-02が資料横断で統合・矛盾検知・訂正評価・限定的Web補完を行い、各項目のステータスを判定する | 構造化JSON（確認中状態）の保存 | （バックエンド内部処理。フロントからは呼び出さない） | `inquiry_fields`, `inquiry_item_fields`, `field_candidates`, `inquiry_notes`, `agent_runs` |
| 4 | アップロード画面での進捗確認（ポーリング） | 現在の処理段階（アップロード中／AI解析中／構造化中／要確認項目整理中／完了）を取得する | 進捗率（%）・状態テキストの表示更新 | `GET /inquiries/{inquiry_id}/agent-status` | `agent_runs` |
| 5 | 処理完了の検知 | SCR-03への自動遷移に伴い、引合詳細を取得する | 案件サマリー・品目一覧・その他特記事項・要確認件数の表示 | `GET /inquiries/{inquiry_id}` | `inquiries`, `inquiry_fields`, `inquiry_item_fields`, `field_candidates`, `inquiry_notes` |

### FLOW-02 要確認項目の確認・修正

**対応機能(②)**: FUNC-06, FUNC-07, FUNC-08

| ステップ | Input | Process | Output | 対応API | 対応テーブル(④) |
|---------|-------|---------|--------|---------|----------------|
| 1 | 案件サマリーの行／品目一覧のセル／要確認チップのクリック | クリックした項目（または要確認全体）の状態に応じて、根拠確認モード／確認・修正モード／要確認一覧（overview）のいずれで開くかを判定する | Inspector表示用データ（値・候補・出典・要確認理由） | `GET /inquiries/{inquiry_id}`（取得済みデータから表示。追加のAPI呼び出しは発生しない） | `inquiry_fields`, `inquiry_item_fields`, `field_candidates` |
| 2 | 確認・修正モードでの候補カードクリック | 選択候補を出典プレビュー・確定する値の入力欄に反映する（フロント内の状態切替のみ） | 出典プレビューの表示切替 | - | - |
| 3 | 「この値を確定する」クリック（修正値または選択候補） | 対象項目の値を確定し、`status`を`ok`に、`confirmed_by`を`user`に更新する。選択された候補の`is_selected`を`true`にする | 該当項目が確認不要状態に遷移し、左側の表示が更新される | `PATCH /inquiries/{inquiry_id}/fields/{field_id}`（A項目）<br>`PATCH /inquiries/{inquiry_id}/items/{item_id}/fields/{field_id}`（B項目） | `inquiry_fields` または `inquiry_item_fields`, `field_candidates` |

### FLOW-03 資料追加アップロード

**対応機能(②)**: FUNC-01（追加）

| ステップ | Input | Process | Output | 対応API | 対応テーブル(④) |
|---------|-------|---------|--------|---------|----------------|
| 1 | 既存引合画面（SCR-03）で「資料を追加」→ SCR-05で追加ファイルを選択 | ファイル形式を検証し、既存の`inquiry_id`に紐づけて保存する | 追加ファイルが同一引合に紐づく | `POST /inquiries/{inquiry_id}/files` | `inquiry_files` |
| 2 | 保存された追加ファイル（バックグラウンド起動） | AGENT-01が追加ファイルのみをパース・抽出し、AGENT-02が`load_existing_inquiry`で既存構造化JSONを取得した上で統合・再判定する | 構造化JSONの更新（既存の確定済み項目は保持しつつ、新規候補で要確認になった項目のみ更新） | （バックエンド内部処理） | `parsed_documents`, `extraction_results`, `inquiry_fields`, `inquiry_item_fields`, `field_candidates`, `agent_runs` |
| 3 | 処理完了の検知 | SCR-03への遷移に伴い、更新後の引合詳細を取得する | 更新後の案件サマリー・品目一覧の表示 | `GET /inquiries/{inquiry_id}` | `inquiries`, `inquiry_fields`, `inquiry_item_fields`, `field_candidates` |

### FLOW-04 成果物確定・出力

**対応機能(②)**: FUNC-09, FUNC-05

| ステップ | Input | Process | Output | 対応API | 対応テーブル(④) |
|---------|-------|---------|--------|---------|----------------|
| 1 | 「確定する」クリック→確定確認モーダルで確定 | その時点の構造化JSONの状態を`final`（確定済み）として保存する | `inquiries.status`が`final`に更新され、バッジ表示が変わる | `POST /inquiries/{inquiry_id}/confirm` | `inquiries` |
| 2 | 出力形式選択モーダルで形式を選び「出力開始」（Scope 1ではExcelのみ有効） | 確定済みの構造化JSONから成果物ファイルを生成する（`_final`接尾辞を付与） | `exports`レコードの作成、生成ファイルの保存 | `POST /inquiries/{inquiry_id}/exports` | `exports` |
| 3 | 生成完了通知（トースト） | ダウンロードを開始する | 成果物ファイルの取得 | `GET /inquiries/{inquiry_id}/exports/{export_id}/download` | `exports` |

### FLOW-05 引合一覧の確認

**対応機能(②)**: FUNC-05, FUNC-07

| ステップ | Input | Process | Output | 対応API | 対応テーブル(④) |
|---------|-------|---------|--------|---------|----------------|
| 1 | SCR-01表示、フィルタタブ（すべて／確認中／確定済み）選択 | 状態別に引合を絞り込み、各引合の要確認件数を集計する | 引合テーブル（依頼元企業・案件名・依頼日時・状態バッジ・要確認件数・最終更新日時） | `GET /inquiries?status={draft\|final}` | `inquiries`, `inquiry_fields`, `inquiry_item_fields` |

### FLOW-06 ログイン・ログアウト

**対応機能(②)**: 非機能要件（4章・セキュリティ）

| ステップ | Input | Process | Output | 対応API | 対応テーブル(④) |
|---------|-------|---------|--------|---------|----------------|
| 1 | メールアドレス・パスワード入力 | 認証情報を検証しセッションを開始する | SCR-01（進捗確認）への遷移 | `POST /auth/login` | `users` |
| 2 | サイドバーの「ログアウト」→確認モーダルで確定 | セッションを破棄する | SCR-00（ログイン画面）への遷移 | `POST /auth/logout` | - |

## 3. エンドポイント詳細

> 正確な型・JSON構造・バリデーションは oval スキーマを SSOT とする。ここでは契約の意味（フィールドの意味・エラーの意味論）を定義し、型はスキーマを参照する。

### ログイン

- **Method**: POST
- **Path**: `/auth/login`
- **目的**: メールアドレス・パスワードでログインし、セッションを開始する（SCR-00）
- **認証**: 不要
- **必要権限**: -
- **対応テーブル(④)**: `users`
- **対応フロー**: FLOW-06
- **スキーマ（型のSSOT）**: `schemas/auth-login`（oval）

#### リクエスト

| パラメータ | 必須 | 意味 |
|-----------|------|------|
| email | Yes | ログインID（メールアドレス） |
| password | Yes | パスワード（平文で送信しTLS上で保護する。サーバー側は`password_hash`と照合） |

（型・構造・バリデーションは上記 oval スキーマを参照）

#### レスポンス（成功）

| フィールド | 意味 |
|-----------|------|
| session_token | 以降のAPI呼び出しに使うセッショントークン |
| user | ログインしたユーザーの表示情報（display_name等） |

（型・構造は oval スキーマを参照）

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 400 | メールアドレス／パスワードが未入力 | `VALIDATION_ERROR` |
| 401 | メールアドレスまたはパスワードが誤っている | `INVALID_CREDENTIALS` |
| 500 | サーバー内部エラー | `INTERNAL_ERROR` |

---

### ログアウト

- **Method**: POST
- **Path**: `/auth/logout`
- **目的**: 現在のセッションを破棄する
- **認証**: 要
- **必要権限**: user
- **対応テーブル(④)**: -
- **対応フロー**: FLOW-06
- **スキーマ（型のSSOT）**: `schemas/auth-logout`（oval）

#### リクエスト

| パラメータ | 必須 | 意味 |
|-----------|------|------|
| （なし。認証ヘッダーのセッショントークンのみ使用） | - | - |

#### レスポンス（成功）

| フィールド | 意味 |
|-----------|------|
| （なし） | 204 No Contentを返す |

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 401 | セッションが無効または期限切れ | `UNAUTHORIZED` |

---

### 引合一覧取得

- **Method**: GET
- **Path**: `/inquiries`
- **目的**: 全引合を状態別に一覧取得する（SCR-01）
- **認証**: 要
- **必要権限**: user
- **対応テーブル(④)**: `inquiries`, `inquiry_fields`, `inquiry_item_fields`
- **対応フロー**: FLOW-05
- **スキーマ（型のSSOT）**: `schemas/inquiry-list`（oval）

#### リクエスト

| パラメータ | 必須 | 意味 |
|-----------|------|------|
| status | No | `draft`（確認中）／`final`（確定済み）で絞り込む。未指定時は全件 |
| page / per_page | No | ページネーション（一覧の件数増加に備える） |

（型・構造・バリデーションは上記 oval スキーマを参照）

#### レスポンス（成功）

| フィールド | 意味 |
|-----------|------|
| items | 引合の配列（依頼元企業・案件名・依頼日時・状態・要確認件数・最終更新日時を含む） |
| total_count | 絞り込み条件に一致する総件数（フィルタタブの件数表示に使用） |

（型・構造は oval スキーマを参照）

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 401 | 未ログイン | `UNAUTHORIZED` |
| 500 | サーバー内部エラー | `INTERNAL_ERROR` |

---

### 書類アップロード・引合自動生成

- **Method**: POST
- **Path**: `/inquiries`
- **目的**: 書類（xlsx/pdf/eml、複数ファイル・形式混在可）を一括アップロードし、新規の引合を自動生成してAI処理（AGENT-01/AGENT-02）を起動する（SCR-02）
- **認証**: 要
- **必要権限**: user
- **対応テーブル(④)**: `inquiries`, `inquiry_files`
- **対応フロー**: FLOW-01
- **スキーマ（型のSSOT）**: `schemas/inquiry-create`（oval）

#### リクエスト

| パラメータ | 必須 | 意味 |
|-----------|------|------|
| files | Yes | アップロードするファイル一式（1件以上、xlsx/pdf/eml形式のみ許可） |

（型・構造・バリデーションは上記 oval スキーマを参照。ファイルサイズ・件数の上限値は02-requirement.md 4章の方針どおりMVPでは設定しない）

#### レスポンス（成功）

| フィールド | 意味 |
|-----------|------|
| inquiry_id | 自動生成された引合ID |
| status | 生成直後の状態（常に`draft`） |
| agent_run_id | 起動されたAGENT-01実行ログのID（進捗取得APIで使用） |

（型・構造は oval スキーマを参照）

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 400 | 非対応形式のファイルが含まれる、またはファイルが1件も指定されていない | `UNSUPPORTED_FILE_TYPE` / `NO_FILES` |
| 401 | 未ログイン | `UNAUTHORIZED` |
| 500 | サーバー内部エラー | `INTERNAL_ERROR` |

---

### 引合詳細取得

- **Method**: GET
- **Path**: `/inquiries/{inquiry_id}`
- **目的**: 案件サマリー・品目一覧・その他特記事項・各項目の状態/候補/出典を含む引合詳細を取得する（SCR-03、およびSCR-04 Inspectorの表示元）
- **認証**: 要
- **必要権限**: user
- **対応テーブル(④)**: `inquiries`, `inquiry_fields`, `inquiry_item_fields`, `field_candidates`, `inquiry_notes`, `field_definitions`
- **対応フロー**: FLOW-01, FLOW-02, FLOW-03
- **スキーマ（型のSSOT）**: `schemas/inquiry-detail`（oval）

#### リクエスト

| パラメータ | 必須 | 意味 |
|-----------|------|------|
| inquiry_id | Yes（パス） | 対象引合のID |

#### レスポンス（成功）

| フィールド | 意味 |
|-----------|------|
| inquiry | 依頼元企業・案件名・引合ID・依頼日時・状態（確認中／確定済み） |
| case_fields | A項目14件それぞれの値・状態（確認不要／要確認）・要確認理由・候補・出典・Web補完フラグ |
| items | 品目ごとのB項目8件（同上の構造） |
| case_notes / item_notes | 案件全体／品目固有のその他特記事項（出典付き） |
| review_summary | 要確認件数・Web補完件数（ステータスサマリーチップ表示用） |

（型・構造は oval スキーマを参照）

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 401 | 未ログイン | `UNAUTHORIZED` |
| 404 | 指定した引合が存在しない | `INQUIRY_NOT_FOUND` |
| 500 | サーバー内部エラー | `INTERNAL_ERROR` |

---

### 資料追加アップロード

- **Method**: POST
- **Path**: `/inquiries/{inquiry_id}/files`
- **目的**: 既存の引合に追加資料をアップロードし、AI処理を再実行する（SCR-05）
- **認証**: 要
- **必要権限**: user
- **対応テーブル(④)**: `inquiry_files`
- **対応フロー**: FLOW-03
- **スキーマ（型のSSOT）**: `schemas/inquiry-files-add`（oval）

#### リクエスト

| パラメータ | 必須 | 意味 |
|-----------|------|------|
| inquiry_id | Yes（パス） | 追加先の引合ID |
| files | Yes | 追加するファイル一式（1件以上、xlsx/pdf/eml形式のみ許可） |

（型・構造・バリデーションは上記 oval スキーマを参照）

#### レスポンス（成功）

| フィールド | 意味 |
|-----------|------|
| inquiry_id | 対象引合ID |
| agent_run_id | 起動されたAGENT-01実行ログのID |

（型・構造は oval スキーマを参照）

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 400 | 非対応形式のファイルが含まれる、またはファイルが1件も指定されていない | `UNSUPPORTED_FILE_TYPE` / `NO_FILES` |
| 401 | 未ログイン | `UNAUTHORIZED` |
| 404 | 指定した引合が存在しない | `INQUIRY_NOT_FOUND` |
| 500 | サーバー内部エラー | `INTERNAL_ERROR` |

---

### エージェント処理進捗取得

- **Method**: GET
- **Path**: `/inquiries/{inquiry_id}/agent-status`
- **目的**: AGENT-01/AGENT-02の実行状況をポーリング取得し、進捗バー・進捗率（%）・状態テキストを更新する（SCR-02）
- **認証**: 要
- **必要権限**: user
- **対応テーブル(④)**: `agent_runs`
- **対応フロー**: FLOW-01, FLOW-03
- **スキーマ（型のSSOT）**: `schemas/agent-status`（oval）

#### リクエスト

| パラメータ | 必須 | 意味 |
|-----------|------|------|
| inquiry_id | Yes（パス） | 対象引合のID |

#### レスポンス（成功）

| フィールド | 意味 |
|-----------|------|
| stage | 現在の処理段階（`uploading` / `extracting`（AGENT-01実行中） / `structuring`（AGENT-02実行中） / `reviewing`（要確認項目整理中） / `completed` / `failed`） |
| progress_percent | 進捗率（0〜100） |
| error_message | `failed`時のみ、担当者向けのエラー内容 |

（型・構造は oval スキーマを参照）

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 401 | 未ログイン | `UNAUTHORIZED` |
| 404 | 指定した引合が存在しない | `INQUIRY_NOT_FOUND` |
| 500 | サーバー内部エラー | `INTERNAL_ERROR` |

---

### 案件全体項目（A項目）の値修正・確定

- **Method**: PATCH
- **Path**: `/inquiries/{inquiry_id}/fields/{field_id}`
- **目的**: 要確認のA項目について、候補選択または手動修正した値を確定し、状態を「確認不要」に遷移させる（SCR-04 確認・修正モード）
- **認証**: 要
- **必要権限**: user
- **対応テーブル(④)**: `inquiry_fields`, `field_candidates`
- **対応フロー**: FLOW-02
- **スキーマ（型のSSOT）**: `schemas/inquiry-field-update`（oval）

#### リクエスト

| パラメータ | 必須 | 意味 |
|-----------|------|------|
| inquiry_id | Yes（パス） | 対象引合のID |
| field_id | Yes（パス） | 対象の固定項目ID |
| value | Yes | 確定する値（候補選択時は候補の値、手動編集時は入力値。空欄も許容し、その場合は要確認〔理由: missing〕に戻す） |
| selected_candidate_id | No | 候補カードから選択した場合の候補ID（`field_candidates.is_selected`の更新に使用） |

（型・構造・バリデーションは上記 oval スキーマを参照）

#### レスポンス（成功）

| フィールド | 意味 |
|-----------|------|
| field_id | 更新した項目ID |
| value | 確定後の値 |
| status | 更新後の状態（`value`が空の場合は`review`、それ以外は`ok`） |
| confirmed_by | `user`固定（担当者による確定であることを示す） |

（型・構造は oval スキーマを参照）

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 401 | 未ログイン | `UNAUTHORIZED` |
| 404 | 指定した引合または項目が存在しない | `INQUIRY_NOT_FOUND` / `FIELD_NOT_FOUND` |
| 500 | サーバー内部エラー | `INTERNAL_ERROR` |

---

### 品目項目（B項目）の値修正・確定

- **Method**: PATCH
- **Path**: `/inquiries/{inquiry_id}/items/{item_id}/fields/{field_id}`
- **目的**: 要確認のB項目（品目ごと）について、候補選択または手動修正した値を確定し、状態を「確認不要」に遷移させる（SCR-04 確認・修正モード）
- **認証**: 要
- **必要権限**: user
- **対応テーブル(④)**: `inquiry_item_fields`, `field_candidates`
- **対応フロー**: FLOW-02
- **スキーマ（型のSSOT）**: `schemas/inquiry-item-field-update`（oval）

#### リクエスト

| パラメータ | 必須 | 意味 |
|-----------|------|------|
| inquiry_id | Yes（パス） | 対象引合のID |
| item_id | Yes（パス） | 対象の品目ID |
| field_id | Yes（パス） | 対象の固定項目ID |
| value | Yes | 確定する値 |
| selected_candidate_id | No | 候補カードから選択した場合の候補ID |

（型・構造・バリデーションは上記 oval スキーマを参照）

#### レスポンス（成功）

| フィールド | 意味 |
|-----------|------|
| item_id / field_id | 更新した品目・項目ID |
| value | 確定後の値 |
| status | 更新後の状態（`ok` または `review`） |
| confirmed_by | `user`固定 |

（型・構造は oval スキーマを参照）

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 401 | 未ログイン | `UNAUTHORIZED` |
| 404 | 指定した引合・品目・項目が存在しない | `INQUIRY_NOT_FOUND` / `ITEM_NOT_FOUND` / `FIELD_NOT_FOUND` |
| 500 | サーバー内部エラー | `INTERNAL_ERROR` |

---

### 成果物確定

- **Method**: POST
- **Path**: `/inquiries/{inquiry_id}/confirm`
- **目的**: 担当者の確認・修正が完了した時点の構造化JSONを「確定済み」状態として保存する（SCR-03「確定する」ボタン）
- **認証**: 要
- **必要権限**: user
- **対応テーブル(④)**: `inquiries`
- **対応フロー**: FLOW-04
- **スキーマ（型のSSOT）**: `schemas/inquiry-confirm`（oval）

#### リクエスト

| パラメータ | 必須 | 意味 |
|-----------|------|------|
| inquiry_id | Yes（パス） | 確定対象の引合ID |

#### レスポンス（成功）

| フィールド | 意味 |
|-----------|------|
| inquiry_id | 対象引合ID |
| status | `final`（確定済み） |
| confirmed_at | 確定日時 |

（型・構造は oval スキーマを参照）

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 401 | 未ログイン | `UNAUTHORIZED` |
| 404 | 指定した引合が存在しない | `INQUIRY_NOT_FOUND` |
| 500 | サーバー内部エラー | `INTERNAL_ERROR` |

> 厳密なロック制御・確定解除操作はMVP対象外（02-requirement.md FUNC-09）のため、確定済み状態でも再度本APIを呼び出すことで再確定できる（エラーにしない）。

---

### 出力形式選択・成果物生成

- **Method**: POST
- **Path**: `/inquiries/{inquiry_id}/exports`
- **目的**: 選択した形式（Scope 1ではExcelのみ有効）で、その時点の構造化JSONから成果物を生成する（SCR-03 出力形式選択モーダル）
- **認証**: 要
- **必要権限**: user
- **対応テーブル(④)**: `exports`
- **対応フロー**: FLOW-04
- **スキーマ（型のSSOT）**: `schemas/inquiry-export-create`（oval）

#### リクエスト

| パラメータ | 必須 | 意味 |
|-----------|------|------|
| inquiry_id | Yes（パス） | 対象引合のID |
| format | Yes | 出力形式。`excel`のみ有効（`word`/`pdf`はScope 2のため受理しない） |

（型・構造・バリデーションは上記 oval スキーマを参照）

#### レスポンス（成功）

| フィールド | 意味 |
|-----------|------|
| export_id | 生成された成果物レコードのID（ダウンロードAPIで使用） |
| file_name | 生成ファイル名（`inquiries.status`に応じて`_draft`／`_final`の接尾辞を含む） |

（型・構造は oval スキーマを参照）

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 400 | `word`/`pdf`等、Scope 1で非対応の出力形式が指定された | `UNSUPPORTED_FORMAT` |
| 401 | 未ログイン | `UNAUTHORIZED` |
| 404 | 指定した引合が存在しない | `INQUIRY_NOT_FOUND` |
| 500 | サーバー内部エラー | `INTERNAL_ERROR` |

---

### 成果物ダウンロード

- **Method**: GET
- **Path**: `/inquiries/{inquiry_id}/exports/{export_id}/download`
- **目的**: 生成済みの成果物ファイルをダウンロードする（SCR-03）
- **認証**: 要
- **必要権限**: user
- **対応テーブル(④)**: `exports`
- **対応フロー**: FLOW-04
- **スキーマ（型のSSOT）**: `schemas/inquiry-export-download`（oval）

#### リクエスト

| パラメータ | 必須 | 意味 |
|-----------|------|------|
| inquiry_id | Yes（パス） | 対象引合のID |
| export_id | Yes（パス） | ダウンロード対象の成果物レコードID |

#### レスポンス（成功）

| フィールド | 意味 |
|-----------|------|
| （ファイルバイナリ） | `Content-Disposition: attachment`でファイル本体を返す |

（型・構造は oval スキーマを参照）

#### レスポンス（エラー）

| ステータス | 意味 | エラーコード |
|-----------|------|------------|
| 401 | 未ログイン | `UNAUTHORIZED` |
| 404 | 指定した引合または成果物が存在しない | `INQUIRY_NOT_FOUND` / `EXPORT_NOT_FOUND` |
| 500 | サーバー内部エラー | `INTERNAL_ERROR` |

---

## 次のステップ

→ 設計フェーズ完了。Build フェーズに進む。
