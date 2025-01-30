from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler

from models import WeightRecord


class WeightVisualizer:
    """
    体重データの可視化と予測を行うクラス

    Parameters
    ----------
    user1_records : List[WeightRecord]
        ユーザー1の記録リスト
    user2_records : List[WeightRecord]
        ユーザー2の記録リスト
    start_date : datetime
        表示開始日
    end_date : datetime
        表示終了日
    show_prediction : bool
        予測表示フラグ
    """

    def __init__(
        self,
        records1: List[WeightRecord],
        records2: List[WeightRecord],
        start_date: datetime,
        end_date: datetime,
        show_prediction: bool = False,
    ):
        self.records1 = records1
        self.records2 = records2
        self.start_date = start_date
        self.end_date = end_date
        self.show_prediction = show_prediction

        # 表示用のデータをフィルタリング
        self.display_record1 = [
            r for r in records1 if start_date <= r.timestamp <= end_date
        ]
        self.display_record2 = [
            r for r in records2 if start_date <= r.timestamp <= end_date
        ]

    def _prepare_data(
        self, records: List[WeightRecord]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        特徴量の生成と前処理

        Parameters
        ----------
        records : List[WeightRecord]
            体重記録リスト

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            X (特徴量) と y (体重) のデータ
        """

        if not records:
            return np.array([]), np.array([])

        # 特徴量の抽出
        features = []
        targets = []

        for i, record in enumerate(records):
            feature = [
                (record.timestamp - datetime.now()).days,  # 経過日数
                record.time_after_meal,  # 食後経過時間
                record.timestamp.hour,  # 時刻
                record.timestamp.weekday(),  # 曜日
                np.sin(2 * np.pi * record.timestamp.hour / 24),  # 時刻の周期性
                np.cos(2 * np.pi * record.timestamp.hour / 24),
            ]

            # 過去の体重変化率（可能な場合）
            if i > 0:
                prev_record = records[i - 1]  # 前回の記録を参照
                weight_change = record.weight - prev_record.weight
                days_diff = (record.timestamp - prev_record.timestamp).days
                if days_diff > 0:
                    feature.append(weight_change / days_diff)
                else:
                    feature.append(0)
            else:
                feature.append(0)

            features.append(feature)
            targets.append(record.weight)

        X = np.array(features)
        y = np.array(targets)

        # 特徴量の標準化
        self.scaler = StandardScaler()
        X = self.scaler.fit_transform(X)

        return X, y

    def _predict_future(
        self, X: np.ndarray, y: np.ndarray, days: int = 30
    ) -> Tuple[List[datetime], List[float]]:
        """
        勾配ブースティングを使用した高精度な予測

        Parameters
        ----------
        X : np.ndarray
            学習用の特徴量データ
        y : np.ndarray
            学習用の体重データ
        days : int, optional
            予測日数, by default 30

        Returns
        -------
        Tuple[List[datetime], List[float]]
            予測日付と予測体重のリスト
        """
        if len(X) < 5:  # 最低5点のデータポイントが必要
            return [], []

        model = GradientBoostingRegressor(
            n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42
        )
        model.fit(X, y)

        future_dates = []
        predictions = []

        last_weight = y[-1]
        last_change = 0

        for day in range(1, days + 1):
            future_date = datetime.now() + timedelta(days=day)
            feature = [
                day,  # 経過日数
                2.0,  # デフォルトの食後経過時間
                future_date.hour,
                future_date.weekday(),
                np.sin(2 * np.pi * future_date.hour / 24),
                np.cos(2 * np.pi * future_date.hour / 24),
                last_change,  # 過去の変化率
            ]

            feature_scaled = self.scaler.transform([feature])
            pred = model.predict(feature_scaled)[0]

            # 予測値の安定化
            last_change = (pred - last_weight) / 1
            last_weight = pred

            future_dates.append(future_date)
            predictions.append(pred)

        return future_dates, predictions

    def create_graph(self):
        user1_name, user2_name = st.secrets["app"]["user_type"]
        fig = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]])

        # ユーザー1のデータプロット
        if self.display_record1:
            dates1 = [r.timestamp for r in self.display_record1]
            weight1 = [r.weight for r in self.display_record1]

            fig.add_trace(
                go.Scatter(
                    x=dates1,
                    y=weight1,
                    name=user1_name,
                    mode="lines+markers",
                    line=dict(color="blue"),
                    hovertemplate="日時: %{x}<br>体重: %{y:.1f}kg<br>",
                ),
                secondary_y=False,
            )

            # 予測の追加
            if (
                self.show_prediction and self.records1
            ):  # 全データを使用して予測
                X1, y1 = self._prepare_data(self.records1)
                future_dates1, predictions1 = self._predict_future(X1, y1)

                if predictions1:
                    # 表示期間内の最新データから予測線を開始
                    last_record = self.display_record1[-1]
                    future_dates1.insert(0, last_record.timestamp)
                    predictions1.insert(0, last_record.weight)

                    fig.add_trace(
                        go.Scatter(
                            x=future_dates1,
                            y=predictions1,
                            name=f"{user1_name} (予測)",
                            line=dict(color="blue", dash="dot"),
                            hovertemplate="予測日: %{x}<br>予測体重: %{y:.1f}kg<br>",
                        ),
                        secondary_y=False,
                    )

        # ユーザー2のデータも同様にプロット
        if self.display_record2:
            dates2 = [r.timestamp for r in self.display_record2]
            weights2 = [r.weight for r in self.display_record2]

            fig.add_trace(
                go.Scatter(
                    x=dates2,
                    y=weights2,
                    name=user2_name,
                    mode="lines+markers",
                    line=dict(color="red"),
                    hovertemplate="日時: %{x}<br>体重: %{y:.1f}kg<br>",
                ),
                secondary_y=False,
            )

            # 予測の追加
            if (
                self.show_prediction and self.records2
            ):  # 全データを使用して予測
                X2, y2 = self._prepare_data(self.records2)
                future_dates2, predictions2 = self._predict_future(X2, y2)

                if predictions2:
                    # 表示期間内の最新データから予測線を開始
                    last_record = self.display_record2[-1]
                    future_dates2.insert(0, last_record.timestamp)
                    predictions2.insert(0, last_record.weight)

                    fig.add_trace(
                        go.Scatter(
                            x=future_dates2,
                            y=predictions2,
                            name=f"{user2_name} (予測)",
                            line=dict(color="red", dash="dot"),
                            hovertemplate="予測日: %{x}<br>予測体重: %{y:.1f}kg<br>",
                        ),
                        secondary_y=False,
                    )

        # グラフのレイアウト設定
        fig.update_layout(
            title="体重推移グラフ",
            xaxis_title="日付",
            yaxis_title="体重 (kg)",
            hovermode="x unified",
            showlegend=True,
        )

        return fig

    def render(self):
        """グラフを描画"""
        fig = self.create_graph()
        st.plotly_chart(fig, use_container_width=True)
