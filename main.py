import hashlib
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import firebase_admin
import streamlit as st
from firebase_admin import credentials, db

from components import DateRangeSelector, WeightInputForm, WeightRecordEditor
from database import WeightDatabase
from visualization import WeightVisualizer

# Firebaseの初期化
if not firebase_admin._apps:
    # Streamlit Cloudのsecretsから認証情報を取得
    cred_dict = {
        "type": st.secrets["firebase"]["type"],
        "project_id": st.secrets["firebase"]["project_id"],
        "private_key_id": st.secrets["firebase"]["private_key_id"],
        "private_key": st.secrets["firebase"]["private_key"],
        "client_email": st.secrets["firebase"]["client_email"],
        "client_id": st.secrets["firebase"]["client_id"],
        "auth_uri": st.secrets["firebase"]["auth_uri"],
        "token_uri": st.secrets["firebase"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["firebase"][
            "auth_provider_x509_cert_url"
        ],
        "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
        "universe_domain": st.secrets["firebase"]["universe_domain"],
    }
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(
        cred, {"databaseURL": st.secrets["app"]["database_url"]}
    )


def hash_password(password: str, salt: str = "") -> str:
    """
    パスワードをハッシュ化する

    Parameters
    ----------
    password : str
        ハッシュ化するパスワード
    salt : str, optional
        ソルト文字列, by default ""

    Returns
    -------
    str
        ハッシュ化されたパスワード
    """
    return hashlib.sha256((password + salt).encode()).hexdigest()


def verify_user(user_id: str) -> Optional[Dict[str, Any]]:
    """
    ユーザーIDが登録済みか確認する

    Parameters
    ----------
    user_id : str
        確認するユーザーID

    Returns
    -------
    Optional[Dict[str, Any]]
        登録済みの場合はユーザー情報、未登録の場合はNone
    """
    ref = db.reference("users")
    devices = ref.get() or {}
    return devices.get(user_id)


def register_user(user_id: str, password: str) -> bool:
    """
    新しいデバイスを登録する

    Parameters
    ----------
    user_id : str
        登録するユーザーのID (secrets["app"]["user_type"]のいずれか)
    password : str
        設定するパスワード

    Returns
    -------
    bool
        登録成功の場合True、失敗の場合False
    """
    try:
        # secrets.tomlに定義されているユーザーIDかチェック
        if user_id not in st.secrets["app"]["user_type"]:
            st.error("無効なユーザーIDです")
            return False

        ref = db.reference("users")
        users = ref.get() or {}

        # すでに同じユーザーIDが登録されていないか確認
        if user_id in users:
            st.error("このユーザーIDはすでに登録されています")
            return False

        # ソルトを生成
        salt = uuid.uuid4().hex

        users[user_id] = {
            "password": hash_password(password, salt),
            "salt": salt,
            "registered_at": datetime.now().isoformat(),
        }
        ref.set(users)
        return True
    except Exception as e:
        st.error(f"ユーザー登録エラー: {str(e)}")
        return False


def authenticate(user_id: str, password: str) -> bool:
    """
    ユーザー認証を行う

    Parameters
    ----------
    user_id : str
        認証するユーザーID
    password : str
        認証パスワード

    Returns
    -------
    bool
        認証成功の場合True、失敗の場合False
    """
    user_info = verify_user(user_id)
    if user_info and user_info["password"] == hash_password(
        password, user_info["salt"]
    ):
        st.session_state["user_type"] = user_id
        return True
    return False


def login_page():
    """
    ログインページを表示する
    """
    st.title("体重管理アプリ - ログイン")

    # タイムアウト警告の表示
    if st.session_state["show_timeout_warning"]:
        st.warning(
            "セッションがタイムアウトしました。再度ログインしてください。"
        )
        st.session_state["show_timeout_warning"] = False

    # ユーザーIDはsecrets.tomlで定義されたのものから選択
    user_id = st.selectbox(
        "ユーザーID",
        st.secrets["app"]["user_type"],
    )

    # エラーメッセージの表示
    if st.session_state["login_error"]:
        st.error(st.session_state["login_error"])

    # 通常のログインフォーム
    with st.form("login_form"):
        password = st.text_input("パスワード", type="password")

        col1, col2 = st.columns(2)

        with col1:
            login_button = st.form_submit_button(
                "ログイン",
                disabled=is_account_locked(user_id),  # ロック中は無効
            )

        with col2:
            # 登録済みのユーザーかどうかをチェック
            is_registered = verify_user(user_id) is not None
            register_button = st.form_submit_button(
                "新規登録",
                disabled=is_registered,  # 登録済みの場合は無効化。booleanとして渡す
                help="すでに登録済みのユーザーは新規登録できません",
            )

        if login_button:
            if authenticate(user_id, password):
                st.success("ログインに成功しました")
                st.session_state["logged_in"] = True
                reset_login_attempts(user_id)  # 成功時はカウントをリセット
                st.session_state["login_error"] = None
                st.rerun()
            else:
                increment_login_attempts(user_id)  # 失敗時はカウントを増やす
                attempts = st.session_state["login_attempts"][user_id]

                if attempts["locked_until"]:
                    # ロックされた場合
                    remaining_time = get_remaining_lock_time(user_id)
                    st.session_state["login_error"] = (
                        f"アカウントがロックされました。{remaining_time}分後に再度お試しください。"
                    )
                else:
                    remaining_time = 3 - attempts["count"]
                    st.session_state["login_error"] = (
                        f"パスワードが正しくありません。残り試行回数: {remaining_time}回"
                    )
                st.rerun()

        if register_button:
            if register_user(user_id, password):
                st.success("ユーザーが登録されました")
                st.session_state["logged_in"] = True
                st.session_state["user_type"] = user_id
                st.session_state["login_error"] = None
                st.rerun()
            else:
                st.error(
                    "ユーザー登録に失敗しました。すでに登録されているか、パスワードが無効です"
                )


def init_session_state():
    """
    セッション状態を初期化する
    """
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "user_type" not in st.session_state:
        st.session_state["user_type"] = None
    if "last_activity" not in st.session_state:
        st.session_state["last_activity"] = None
    if "show_timeout_warning" not in st.session_state:
        st.session_state["show_timeout_warning"] = False
    if "login_attempts" not in st.session_state:
        st.session_state["login_attempts"] = {}
    if "login_error" not in st.session_state:
        st.session_state["login_error"] = None


def is_account_locked(user_id: str) -> bool:
    """
    アカウントがロック中かどうかを確認する

    Parameters
    ----------
    user_id : str
        ユーザーID

    Returns
    -------
    bool
        ロック中の場合True
    """
    attempts = st.session_state["login_attempts"].get(
        user_id, {"count": 0, "locked_until": None}
    )
    if attempts["locked_until"]:
        if datetime.now() < attempts["locked_until"]:
            return True
    return False


def get_remaining_lock_time(user_id: str) -> int:
    """
    ロック解除までの残り時間 (分) を取得する

    Parameters
    ----------
    user_id : str
        ユーザーID

    Returns
    -------
    int
        残り時間 (分) 。ロックされていない場合は0
    """
    attempts = st.session_state["login_attempts"].get(
        user_id, {"count": 0, "locked_until": None}
    )
    if attempts["locked_until"] and datetime.now() < attempts["locked_until"]:
        return int(
            (attempts["locked_until"] - datetime.now()).total_seconds() / 60
        )
    return 0


def check_login_attempts(user_id: str) -> bool:
    """
    ログイン試行回数をチェックする

    Parameters
    ----------
    user_id : str
        チェックするユーザーID

    Returns
    -------
    bool
        ログイン可能な場合True、ロックされている場合False
    """
    MAX_ATTEMPTS = 3

    attempts = st.session_state["login_attempts"].get(
        user_id, {"count": 0, "locked_until": None}
    )
    current_time = datetime.now()

    # ロック時間のチェック
    if attempts["locked_until"]:
        if current_time < attempts["locked_until"]:
            return False
        else:
            # ロック時間が経過したらリセット
            st.session_state["login_attempts"][user_id] = {
                "count": 0,
                "locked_until": None,
            }
            st.session_state["login_error"] = None
            return True

    return attempts["count"] < MAX_ATTEMPTS


def increment_login_attempts(user_id: str):
    """
    ログイン試行回数をインクリメントし、必要に応じてアカウントをロックする

    Parameters
    ----------
    user_id : str
        ユーザーID
    """
    MAX_ATTEMPTS = 3
    LOCK_TIME_MINUTES = 15

    attempts = st.session_state["login_attempts"].get(
        user_id, {"count": 0, "locked_until": None}
    )
    attempts["count"] += 1

    if attempts["count"] >= MAX_ATTEMPTS:
        attempts["locked_until"] = datetime.now() + timedelta(
            minutes=LOCK_TIME_MINUTES
        )
        st.error(
            f"ログイン試行回数が上限を超えました。{LOCK_TIME_MINUTES}分間ロックされます。"
        )
        time.sleep(5)

    st.session_state["login_attempts"][user_id] = attempts


def reset_login_attempts(user_id: str):
    """
    ログイン試行回数をリセットする

    Parameters
    ----------
    user_id : str
        ユーザーID
    """
    st.session_state["login_attempts"][user_id] = {
        "count": 0,
        "locked_until": None,
    }


def check_session_timeout():
    """
    セッションタイムアウトをチェックする
    30分以上操作がない場合、自動的にログアウトする
    """
    TIMEOUT_MINUTES = 2

    # ログインしていない場合は何もしない
    if not st.session_state["logged_in"]:
        return

    current_time = datetime.now()

    # 最終アクティビティ時刻の更新
    if st.session_state["last_activity"] is None:
        st.session_state["last_activity"] = current_time

    # タイムアウトチェック
    if st.session_state["last_activity"] is not None:
        time_diff = current_time - st.session_state["last_activity"]
        if time_diff.total_seconds() > TIMEOUT_MINUTES * 60:
            # セッションタイムアウト時の処理
            st.session_state["logged_in"] = False
            st.session_state["user_type"] = None
            st.session_state["last_activity"] = None
            st.session_state["show_timeout_warning"] = True
            st.rerun()

    # アクティビティ時刻の更新
    st.session_state["last_activity"] = current_time


def main():
    """
    メインアプリケーション
    """
    init_session_state()
    check_session_timeout()  # セッションタイムアウトのチェック

    if not st.session_state["logged_in"]:
        login_page()
        return

    st.title("体重管理アプリ")
    st.write(f"ログインユーザー: {st.session_state['user_type']}")

    # セッションタイムアウトまでの残り時間を表示
    if st.session_state["last_activity"] is not None:
        remaining_time = (
            2
            - (
                datetime.now() - st.session_state["last_activity"]
            ).total_seconds()
            / 60
        )
        if remaining_time > 0:
            st.sidebar.info(
                f"セッションタイムアウトまで: {int(remaining_time)}分"
            )

    # データベースインスタンスの作成
    db = WeightDatabase(st.session_state["user_type"])

    # サイドバーに入力フォームを配置
    with st.sidebar:
        weight_form = WeightInputForm(db)
        weight_form.render()

        # 予測表示の切り替え
        show_prediction = st.checkbox("予測表示", value=False)

    # メイン画面に期間選択と記録表示
    start_date, end_date = DateRangeSelector.render()

    # 両ユーザーのデータを取得
    db1 = WeightDatabase(st.secrets["app"]["user_type"][0])
    db2 = WeightDatabase(st.secrets["app"]["user_type"][1])
    records1 = db1.get_records()  # 期間指定なしで全データを取得
    records2 = db2.get_records()

    # グラフの表示
    visualizer = WeightVisualizer(
        records1, records2, start_date, end_date, show_prediction
    )
    visualizer.render()

    # 現在のユーザーの記録のみ編集可能
    current_db = WeightDatabase(st.session_state["user_type"])
    current_records = [
        r
        for r in (
            db1
            if st.session_state["user_type"]
            == st.secrets["app"]["user_type"][0]
            else db2
        ).get_records()
        if start_date <= r.timestamp <= end_date
    ]
    editor = WeightRecordEditor(current_db, current_records)
    editor.render()

    if st.button("ログアウト"):
        st.session_state["logged_in"] = False
        st.session_state["user_type"] = None
        st.session_state["last_activity"] = None
        st.rerun()


if __name__ == "__main__":
    main()
