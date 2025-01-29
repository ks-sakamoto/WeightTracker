from datetime import datetime
from typing import List

import streamlit as st
from firebase_admin import db

from models import WeightRecord


class WeightDatabase:
    """
    体重データのデータベース操作クラス

    Parameters
    ----------
    user_type : str
        ユーザータイプ (secrets["app"]["user_type"])
    """

    def __init__(self, user_type: str):
        """
        Parameters
        ----------
        user_type : str
            ユーザータイプ
        """
        self.user_type = user_type
        self.ref = db.reference(f"weights/{user_type}")

    def add_record(
        self, weight: float, time_after_meal: float, timestamp: datetime
    ) -> bool:
        """
        新しい体重記録を追加

        Parameters
        ----------
        weight : float
            記録する体重値
        time_after_meal : float
            食後経過時間 (時間単位)
        timestamp : datetime
            記録する日付

        Returns
        -------
        bool
            追加成功でTrue、失敗でFalse
        """
        try:
            record = WeightRecord(
                weight=weight,
                timestamp=timestamp,
                time_after_meal=time_after_meal,
            )
            self.ref.push().set(record.to_dict())
            return True
        except Exception as e:
            st.error(f"データ追加エラー: {str(e)}")
            return False

    def get_records(
        self, start_date: datetime, end_date: datetime
    ) -> List[WeightRecord]:
        """
        指定期間の体重記録を取得

        Parameters
        ----------
        start_date : datetime
            取得開始日
        end_date : datetime
            取得終了日

        Returns
        -------
        List[WeightRecord]
            体重記録のリスト
        """
        try:
            records = self.ref.get() or {}
            result = []

            for record_id, data in records.items():
                record = WeightRecord.from_dict(data)
                record.id = record_id  # レコードIDを設定
                if start_date <= record.timestamp <= end_date:
                    result.append(record)

            return sorted(result, key=lambda x: x.timestamp)
        except Exception as e:
            st.error(f"データ取得エラー: {str(e)}")
            return []

    def update_record(
        self,
        record_id: str,
        weight: float,
        time_after_meal: float,
        timestamp: datetime,
    ) -> bool:
        """
        体重記録を更新

        Parameters
        ----------
        record_id : str
            更新する記録のID
        weight : float
            新しい体重値
        time_after_meal : float
            新しい食後経過時間
        timestamp : datetime
            新しい日付

        Returns
        -------
        bool
            更新成功でTrue、失敗でFalse
        """
        try:
            record_ref = self.ref.child(record_id)
            record = WeightRecord(
                weight=weight,
                timestamp=timestamp,
                time_after_meal=time_after_meal,
                edited=True,
            )
            record_ref.set(record.to_dict())
            return True
        except Exception as e:
            st.error(f"データ更新エラー: {str(e)}")
            return False

    def delete_record(self, record_id: str) -> bool:
        """
        体重記録を削除

        Parameters
        ----------
        record_id : str
            削除する記録のID

        Returns
        -------
        bool
            削除成功でTrue、失敗でFalse
        """
        try:
            self.ref.child(record_id).delete()
            return True
        except Exception as e:
            st.error(f"データ削除エラー: {str(e)}")
            return False
