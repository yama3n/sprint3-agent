# UIデザイン ガイドライン（Sprint 3: MUI）

実装ハーネス（build-loop）が全スライスで守る UI デザイン規約。
**デザインの真実源は `docs/requirements/03-spec.md` の「3. デザイントークン」**。
実装は `frontend/src/shared/theme/tokens.ts`（03-spec からの転記）を経由してのみデザイン値を使う。

> このファイルは「ダサくならないためのガードレール」。デザインの自由は design フェーズ
> （`/design-spec` のデザイン適用パス）で行使済み。**Build 中に新しいデザイン判断をしない。**

## 大原則

1. デザイン値（色・フォント・サイズ・radius・影）は `tokens.ts` 経由のみ。hex 直書き・インライン style でのデザイン指定は禁止
2. トークンにない色・サイズが必要になったら、勝手に足さず reviewer 指摘 or `BLOCKED` として記録し、研修者の判断を仰ぐ
3. 迷ったら「静かな方」を選ぶ（装飾を足すより削る）

## 色（色相2つルール）

- 使える色相は **main と error の2つだけ**。それ以外の違いはすべて main の濃淡で表現する
- success / info / warning の色を追加しない（意味の強調は main の濃淡と文言で表現）
- 純白 `#FFFFFF`・純黒 `#000000` を直接使わない（`background` / `text-primary` トークンを使う）

## 脱・標準MUI チェックリスト（createTheme 必須設定）

「素の MUI」に見える主因を必ず上書きする:

| 設定 | 必須値 | 理由 |
|------|--------|------|
| `palette.primary` | tokens の main 濃淡（`#1976d2` の残存禁止） | デフォルト青が「素のMUI」最大の署名 |
| `palette.secondary` | main の濃淡を割り当て（デフォルト紫 `#9c27b0` の残存禁止） | 未設定だと紫が残る |
| `palette.error` | tokens の error | |
| `palette.background.default` | tokens の background（白のまま禁止） | |
| `typography.fontFamily` | tokens の font-body（Roboto のまま禁止・日本語フォールバック必須） | フォント無指定は一目でわかる |
| `shape.borderRadius` | tokens の radius | デフォルト値ではなく「選んだ値」にする |
| `components.MuiButton` | `textTransform: 'none'`・`disableElevation: true` | 大文字化ボタンと影ボタンが第2の署名 |
| Card / Paper | `variant="outlined"` を基本（影は1段階まで） | 影の重なりが安っぽさの主因 |

## 画面の規律

- **primary（塗り）ボタンは1画面に1つまで**。他のアクションは outlined / text にする
- ページタイトル相当（h1）は1画面に1つ。見出しレベルを飛ばさない
- 基本は左揃え。中央揃えは空状態・確認ダイアログなどに限定
- radius・影・罫線色は全画面で各1種類（トークン値のみ）
- フォントサイズはトークンの5種のみ。ウェイトは3種まで

## 3状態の設計（未完成感をなくす）

一覧・詳細など各画面に以下を必ず実装する:

- **空状態**: 「データがありません」で終わらせず、次の行動へ誘導する（例:「最初のタスクを作成しましょう」+ アクション）
- **ローディング**: skeleton または明示的なメッセージ
- **エラー**: 原因と直し方を書く（「エラーが発生しました」だけの表示は禁止）

## Never リスト（アプリUIでやらないこと）

- グラデーション背景・ガラスモーフィズム・装飾ブロブ
- アプリ内のヒーローセクション（LP ではない）
- 見出し・ボタン・ラベルへの絵文字（✨ 🎉 等）
- 等幅カード＋アイコンのグリッドを「とりあえず」並べる
- placeholder だけのフォーム（ラベルは常時表示）
- bounce・parallax 等の過剰アニメーション（transition は opacity/transform のみ・150〜250ms）
- トークン外の hex 直書き・インライン style でのデザイン指定

## reviewer チェックリスト（UI を含むスライス）

- [ ] デザイン値がすべて `tokens.ts` 経由（hex 直書き・インライン style なし）
- [ ] テーマ関連の変更がある場合、脱・標準MUI 必須設定が維持されている
- [ ] primary ボタンが1画面1つ / h1 が1つ
- [ ] 空・ローディング・エラーの3状態がある
- [ ] Never リスト違反がない
- [ ] モック（`docs/requirements/mocks/mockup.html` の該当 `#SCR-xx`）と構成・トーンが一致している
