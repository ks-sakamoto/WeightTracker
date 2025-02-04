from datetime import datetime, timedelta
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

import streamlit as st

from database import WeightDatabase
from models import WeightRecord


class WeightInputForm:
    """
    体重入力のフォームコンポーネント

    Parameters
    ----------
    db : WeightDatabase
        データベース操作インスタンス
    """

    def __init__(self, db: WeightDatabase):
        self.db = db

    def render(self):
        """
        フォームを描画
        """
        with st.form("weight_input_form"):
            st.subheader("体重を記録")

            # 日付入力 - 日本時間で現在時刻を取得
            today = datetime.now(ZoneInfo("Asia/Tokyo")).date()
            input_date = st.date_input("日付", value=today)

            # 体重入力
            weight = st.number_input(
                "体重 (kg)",
                min_value=0.0,
                max_value=100.0,
                step=0.1,
                format="%.1f",
            )

            # 食後経過時間の選択
            time_after_meal = st.selectbox(
                "食後経過時間",
                options=[t[0] for t in WeightRecord.TIME_AFTER_MEAL_OPTIONS],
                format_func=lambda x: dict(
                    WeightRecord.TIME_AFTER_MEAL_OPTIONS
                )[x],
            )

            # 送信ボタン
            submit = st.form_submit_button("記録")

            if submit and weight > 0:
                # タイムスタンプを日本時間で生成
                timestamp = (
                    datetime.now(ZoneInfo("Asia/Tokyo"))
                    if input_date == today
                    else datetime.combine(
                        input_date, datetime.min.time()
                    ).replace(tzinfo=ZoneInfo("Asia/Tokyo"))
                )
                if self.db.add_record(weight, time_after_meal, timestamp):
                    st.success("記録を保存しました")
                    st.rerun()


class DateRangeSelector:
    """
    期間選択コンポーネント
    """

    QUICK_PERIODS = [
        ("1週間", 7),
        ("1か月", 30),
        ("2か月", 60),
        ("3か月", 90),
        ("6か月", 180),
        ("12か月", 365),
    ]

    @staticmethod
    def render() -> Tuple[datetime, datetime]:
        """
        期間選択UIを描画

        Returns
        -------
        Tuple[datetime, datetime]
            選択された開始日と終了日
        """

        # 現在の日本時間を取得
        now = datetime.now(ZoneInfo("Asia/Tokyo"))

        # セッションステートのキーを定義
        if "date_range_start" not in st.session_state:
            # デフォルトで1週間を表示
            st.session_state.date_range_start = now - timedelta(days=7)
            st.session_state.date_range_end = now

        # カスタム入力期間
        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input(
                "表示開始日",
                value=st.session_state.date_range_start.date(),
                max_value=now.date(),
            )

        with col2:
            end_date = st.date_input(
                "表示終了日",
                value=st.session_state.date_range_end.date(),
                min_value=start_date,
                max_value=now.date(),
            )

        # クイック選択ボタン
        cols = st.columns(len(DateRangeSelector.QUICK_PERIODS))

        # クイック選択ボタンの配置
        for col, (label, days) in zip(cols, DateRangeSelector.QUICK_PERIODS):
            with col:
                if st.button(label):
                    st.session_state.date_range_start = now - timedelta(
                        days=days
                    )
                    st.session_state.date_range_end = now
                    st.rerun()

        # datetime型に変換し、日本時間のタイムゾーン情報を追加
        start_datetime = datetime.combine(
            start_date, datetime.min.time()
        ).replace(tzinfo=ZoneInfo("Asia/Tokyo"))
        end_datetime = datetime.combine(end_date, datetime.max.time()).replace(
            tzinfo=ZoneInfo("Asia/Tokyo")
        )

        # セッションステートを更新
        st.session_state.date_range_start = start_datetime
        st.session_state.date_range_end = end_datetime

        return start_datetime, end_datetime


class WeightRecordEditor:
    """
    体重記録編集コンポーネント

    Parameters
    ----------
    db : WeightDatabase
        データベース操作インスタンス
    records : List[WeightRecord]
        表示する記録のリスト
    """

    def __init__(self, db: WeightDatabase, records: list):
        self.db = db
        self.records = records

    def render(self):
        """
        記録編集UIを描画
        """
        st.subheader("記録の編集・削除")

        for i, record in enumerate(self.records):
            with st.expander(
                f"記録 {record.timestamp.strftime('%Y-%m-%d %H:%M')}"
                f"({record.weight}kg, 食後{WeightRecord.get_time_after_meal_display(record.time_after_meal)})"
            ):

                # 編集フォーム
                with st.form(f"edit_form_{i}"):
                    new_date = st.date_input(
                        "日付", value=record.timestamp.date()
                    )

                    new_weight = st.number_input(
                        "体重 (kg)",
                        value=record.weight,
                        min_value=0.0,
                        max_value=100.0,
                        step=0.1,
                        format="%.1f",
                    )

                    new_time = st.selectbox(
                        "食後経過時間",
                        options=[
                            t[0] for t in WeightRecord.TIME_AFTER_MEAL_OPTIONS
                        ],
                        index=[
                            t[0] for t in WeightRecord.TIME_AFTER_MEAL_OPTIONS
                        ].index(record.time_after_meal),
                        format_func=lambda x: dict(
                            WeightRecord.TIME_AFTER_MEAL_OPTIONS
                        )[x],
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.form_submit_button("更新"):
                            timestamp = datetime.combine(
                                new_date, datetime.min.time()
                            )
                            if self.db.update_record(
                                record.id, new_weight, new_time, timestamp
                            ):
                                st.success("記録を更新しました")
                                st.rerun()

                    with col2:
                        if st.form_submit_button("削除", type="primary"):
                            if self.db.delete_record(record.id):
                                st.success("記録を削除しました")
                                st.rerun()
