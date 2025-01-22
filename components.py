from datetime import datetime, timedelta
from typing import Optional, Tuple

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
                if self.db.add_record(weight, time_after_meal):
                    st.success("記録を保存しました")
                    st.rerun()


class DateRangeSelector:
    """
    期間選択コンポーネント
    """

    @staticmethod
    def render() -> Tuple[datetime, datetime]:
        """
        期間選択UIを描画

        Returns
        -------
        Tuple[datetime, datetime]
            選択された開始日と終了日
        """
        st.subheader("期間選択")

        # デフォルトで1週間を表示
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input(
                "開始日", value=start_date, max_value=end_date
            )

        with col2:
            end_date = st.date_input(
                "終了日", value=end_date, min_value=start_date
            )

        # datetime型に変換
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

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
                            if self.db.update_record(
                                record.id, new_weight, new_time
                            ):
                                st.success("記録を更新しました")
                                st.rerun()

                    with col2:
                        if st.form_submit_button("削除", type="primary"):
                            if self.db.delete_record(record.id):
                                st.success("記録を削除しました")
                                st.rerun()
