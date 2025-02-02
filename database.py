import json
from datetime import datetime
from typing import List, Literal, Optional

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
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[WeightRecord]:
        """
        指定期間の体重記録を取得

        Parameters
        ----------
        start_date : Optional[datetime], optional
            取得開始日, by default None
        end_date : Optional[datetime], optional
            取得終了日, by default None

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

                # 期間指定がある場合のみフィルタリング
                if start_date and end_date:
                    if start_date <= record.timestamp <= end_date:
                        result.append(record)
                else:
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

    def export_data(self, export_path: Optional[str] = None) -> str:
        """
        ユーザーの体重データをJSONファイルとしてエクスポート

        Parameters
        ----------
        export_path : Optional[str], default None
            エクスポート先のパス, Noneの場合は現在の日時でファイル名を生成

        Returns
        -------
        str
            エクスポートされたファイルのパス
        """
        try:
            # データの取得
            data = self.ref.get()
            if data is None:
                st.error(f"ユーザー {self.user_type} のデータが見つかりません")

            # エクスポートパスの設定
            if export_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = (
                    f"weight_tracker_{self.user_type}_{timestamp}.json"
                )

            # JSONとしてエクスポート
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return export_path

        except Exception as e:
            st.error(f"データエクスポートエラー: {str(e)}")
