# Weight Tracker

2人のユーザーで体重を管理・共有できるWebアプリケーションです。食後経過時間も記録でき、機械学習による体重予測機能も実装されています。

## 機能一覧

### データ管理機能
- 体重の記録（日付、時刻指定可能）
- 食後経過時間の記録（30分～3時間30分以上）
- データの編集・削除
- JSONフォーマットでのデータエクスポート

### グラフ機能
- 2人分の体重推移を1つのグラフで表示
- 表示期間の自由な選択（デフォルト1週間）
- 1ヶ月先までの体重予測表示（オプション）
- 食後経過時間を考慮した高精度な予測モデル

### セキュリティ機能
- デバイスベースの認証システム
- パスワードによるアクセス制限
- 試行回数制限付きログイン（3回失敗で15分ロック）
- 30分無操作でセッションタイムアウト

## 技術スタック

- **フロントエンド**: Streamlit
- **バックエンド**: Python
- **データベース**: Firebase Realtime Database
- **ホスティング**: Streamlit Cloud
- **予測モデル**: scikit-learn (Gradient Boosting)

## 必要要件

- Python 3.8以上
- Firebase Project
- Streamlit Cloudアカウント（無料プラン可）

## セットアップ手順

### 1. リポジトリのクローン
```bash
git clone https://github.com/yourusername/weight-tracker.git
cd weight-tracker
```

### 2. 仮想環境の作成とパッケージのインストール
```bash
python -m venv .venv
source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Firebase設定
1. [Firebase Console](https://console.firebase.google.com/)で新規プロジェクトを作成
2. Realtime Databaseを有効化
3. プロジェクト設定からサービスアカウントキーを生成

### 4. 環境変数の設定
`.streamlit/secrets.toml`ファイルを作成し、以下の内容を設定：

```toml
[firebase]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "your-private-key"
client_email = "your-client-email"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "your-auth-provider-url"
client_x509_cert_url = "your-client-cert-url"
universe_domain = "googleapis.com"

[app]
database_url = "https://your-project-id-default-rtdb.firebaseio.com"
user_type = ["user1", "user2"]
```

## デプロイ手順

### Streamlit Cloudへのデプロイ
1. [Streamlit Cloud](https://streamlit.io/cloud)にアクセス
2. GitHubアカウントでログイン
3. "Create app"をクリック
4. リポジトリとブランチを選択
5. メインファイル（main.py）を指定
6. Advanced Settingsで環境変数を設定
   - `.streamlit/secrets.toml`の内容をコピー

## 開発ガイドライン

### コードスタイル
- PEP 8に準拠
- Docstring: NumPy形式
- 型ヒント必須

### ブランチ戦略
- main: プロダクション用
- feature/*: 新機能開発用
- fix/*: 機能修正用

## プロジェクト構成
```
WeightTracker/
├── .streamlit/
│   └── secrets.toml
├── .gitignore
├── README.md
├── components.py      # UIコンポーネント
├── database.py       # データベース操作
├── main.py          # メインアプリケーション
├── models.py        # データモデル
├── requirements.txt  # 依存パッケージ
└── visualization.py # グラフ・予測機能
```

