from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Literal, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats


class SortMode(Enum):
    IMPACT = "impact"
    P_VALUE = "p_value"


@dataclass
class SplitResult:
    feature: str
    feature_type: Literal["continuous", "discrete"]
    rule: str
    group_a_rate: float
    group_b_rate: float
    effect_size: float
    p_value: float
    is_significant: bool


class FeatureAnalyzer:
    def __init__(
        self,
        df: pd.DataFrame,
        target_col: str,
        significance_level: float = 0.05,
        sort_mode: SortMode = SortMode.IMPACT,
    ):
        self.df = df
        self.target_col = target_col
        self.significance_level = significance_level
        self.sort_mode = sort_mode
        self._classify_features()

    def _classify_features(self):
        """將特徵分類為離散型和連續型"""
        self.continuous_features = []
        self.discrete_features = []

        for col in self.df.columns:
            if col == self.target_col:
                continue

            if self.df[col].dtype in ["int64", "float64"]:
                if self.df[col].nunique() > 10:  # 如果唯一值超過10個，視為連續型
                    self.continuous_features.append(col)
                else:
                    self.discrete_features.append(col)
            else:
                self.discrete_features.append(col)

    def _calculate_split_statistics(
        self, feature: str, split_value: float, feature_type: str = "continuous"
    ) -> SplitResult:
        """計算給定分割點的統計指標"""
        if feature_type == "continuous":
            # 連續型特徵的分割
            group_a = self.df[self.df[feature] > split_value]
            group_b = self.df[self.df[feature] <= split_value]
            rule = f"{feature} > {split_value:.2f}"
        else:
            # 離散型特徵的分割（one-vs-rest）
            group_a = self.df[self.df[feature] == split_value]
            group_b = self.df[self.df[feature] != split_value]
            rule = f"{feature} = {split_value}"

        # 計算各組的目標變量比率
        group_a_rate = group_a[self.target_col].mean()
        group_b_rate = group_b[self.target_col].mean()

        # 計算效應大小（絕對差異）
        effect_size = abs(group_a_rate - group_b_rate)

        # 執行統計檢定
        if self.df[self.target_col].dtype in ["int64", "float64"]:
            # 對於數值型目標變量，使用 Mann-Whitney U 檢定
            stat, p_value = stats.mannwhitneyu(
                group_a[self.target_col],
                group_b[self.target_col],
                alternative="two-sided",
            )
        else:
            # 對於類別型目標變量，使用卡方檢定
            contingency = pd.crosstab(
                (
                    self.df[feature] == split_value
                    if feature_type == "discrete"
                    else self.df[feature] > split_value
                ),
                self.df[self.target_col],
            )
            chi2, p_value, _, _ = stats.chi2_contingency(contingency)

        return SplitResult(
            feature=feature,
            feature_type=feature_type,
            rule=rule,
            group_a_rate=group_a_rate * 100,
            group_b_rate=group_b_rate * 100,
            effect_size=effect_size * 100,
            p_value=p_value,
            is_significant=p_value < self.significance_level,
        )

    def _analyze_discrete_feature(self, feature: str) -> List[SplitResult]:
        """分析離散型特徵"""
        splits = []
        for category in self.df[feature].unique():
            split_result = self._calculate_split_statistics(
                feature, category, feature_type="discrete"
            )
            splits.append(split_result)
        return splits

    def find_best_splits(self, n_splits: int = 5) -> List[SplitResult]:
        """為所有特徵找到最佳分割點"""
        all_splits = []

        # 分析連續型特徵
        for feature in self.continuous_features:
            percentiles = np.linspace(0.1, 0.9, 9)
            split_points = np.percentile(self.df[feature], percentiles * 100)

            for split_point in split_points:
                split_result = self._calculate_split_statistics(feature, split_point)
                all_splits.append(split_result)

        # 分析離散型特徵
        for feature in self.discrete_features:
            splits = self._analyze_discrete_feature(feature)
            all_splits.extend(splits)

        # 按顯著性分組
        significant_splits = [s for s in all_splits if s.is_significant]
        non_significant_splits = [s for s in all_splits if not s.is_significant]

        # 根據排序模式排序顯著性結果
        if self.sort_mode == SortMode.IMPACT:
            significant_splits.sort(key=lambda x: x.effect_size, reverse=True)
        else:  # SortMode.P_VALUE
            significant_splits.sort(key=lambda x: x.p_value)

        # 非顯著性結果始終按效應大小排序
        non_significant_splits.sort(key=lambda x: x.effect_size, reverse=True)

        return significant_splits + non_significant_splits

    def get_top_splits_per_feature(self) -> Dict[str, SplitResult]:
        """獲取每個特徵的最佳分割"""
        all_splits = self.find_best_splits()
        best_splits = {}

        for split in all_splits:
            if split.feature not in best_splits:
                best_splits[split.feature] = split
            elif split.effect_size > best_splits[split.feature].effect_size:
                best_splits[split.feature] = split

        return best_splits
