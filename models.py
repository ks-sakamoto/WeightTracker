import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class WeightRecord:
    """
    体重記録のデータモデル

    Parameters
    ----------
    weight : float
        体重値 (kg)
    timestamp : datetime
        記録日時
    time_after_meal : float
        食後経過時間 (時間単位)。例: 1.5は1時間30分を表す
    edited : bool, optional
        編集済みフラグ, by default False

    Attributes
    ----------
    weight : float
        体重値（kg）
    timestamp : datetime
        記録日時
    time_after_meal : float
        食後経過時間（時間単位）
    edited : bool
        編集済みフラグ
    """

    weight: float
    timestamp: datetime
    time_after_meal: float
    edited: bool = False

    # 食後経過時間の選択肢を定義
    TIME_AFTER_MEAL_OPTIONS = [
        (0.5, "30分"),
        (1.0, "1時間"),
        (1.5, "1時間30分"),
        (2.0, "2時間"),
        (2.5, "2時間30分"),
        (3.0, "3時間"),
        (3.5, "3時間30分以上"),
    ]

    def to_dict(self) -> Dict[str, Any]:
        """
        FirebaseのRealtimeデータベース用に辞書形式に変換

        Returns
        -------
        dict[str, Any]
            データベース保存用の辞書
        """
        return {
            "weight": self.weight,
            "timestamp": self.timestamp.replace(microsecond=0).isoformat(),
            "time_after_meal": self.time_after_meal,
            "edited": self.edited,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeightRecord":
        """
        辞書形式のデータからWeightRecordインスタンスを生成

        Parameters
        ----------
        data : Dict[str, Any]
            データベースから取得した辞書データ

        Returns
        -------
        WeightRecord
            生成されたWeightRecordインスタンス
        """
        return cls(
            weight=float(data["weight"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            time_after_meal=float(data["time_after_meal"]),
            edited=data.get("edited", False),
        )

    @classmethod
    def get_time_after_meal_display(cls, value: float) -> str:
        """
        食後経過時間の数値を表示用文字列に変換

        Parameters
        ----------
        value : float
            食後経過時間の数値

        Returns
        -------
        str
            表示用文字列
        """
        for time_value, display_text in cls.TIME_AFTER_MEAL_OPTIONS:
            if time_value == value:
                return display_text
        return "不明"
