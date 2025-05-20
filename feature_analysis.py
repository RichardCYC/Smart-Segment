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
    test_method: str
    group_a_count: int
    group_b_count: int


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
            # 計算各組的目標變量比率
            group_a_rate = group_a[self.target_col].mean()
            group_b_rate = group_b[self.target_col].mean()
            # 計算效應大小（絕對差異）
            effect_size = abs(group_a_rate - group_b_rate)

            # 根據資料集大小動態決定檢定方法
            n_a = len(group_a)
            n_b = len(group_b)
            total_n = len(self.df)

            # 如果總樣本數小於30，使用Mann-Whitney U test
            if total_n < 30:
                stat, p_value = stats.mannwhitneyu(
                    group_a[self.target_col],
                    group_b[self.target_col],
                    alternative="two-sided",
                )
                test_method = "Mann-Whitney U test (n < 30)"
            # 如果任一組樣本數小於30，使用Mann-Whitney U test
            elif n_a < 30 or n_b < 30:
                stat, p_value = stats.mannwhitneyu(
                    group_a[self.target_col],
                    group_b[self.target_col],
                    alternative="two-sided",
                )
                test_method = "Mann-Whitney U test (group size < 30)"
            # 如果資料分布嚴重偏斜，使用Mann-Whitney U test
            elif (
                abs(stats.skew(group_a[self.target_col])) > 2
                or abs(stats.skew(group_b[self.target_col])) > 2
            ):
                stat, p_value = stats.mannwhitneyu(
                    group_a[self.target_col],
                    group_b[self.target_col],
                    alternative="two-sided",
                )
                test_method = "Mann-Whitney U test (skewed data)"
            # 其他情況使用Welch's t-test
            else:
                stat, p_value = stats.ttest_ind(
                    group_a[self.target_col],
                    group_b[self.target_col],
                    equal_var=False,
                )
                test_method = "Welch's t-test"
        else:
            # 離散型特徵的分割（one-vs-rest）
            group_a = self.df[self.df[feature] == split_value]
            group_b = self.df[self.df[feature] != split_value]
            rule = f"{feature} = {split_value}"
            group_a_rate = group_a[self.target_col].mean()
            group_b_rate = group_b[self.target_col].mean()
            effect_size = abs(group_a_rate - group_b_rate)

            # 根據資料集大小動態決定檢定方法
            n_a = len(group_a)
            n_b = len(group_b)
            total_n = len(self.df)

            # 如果任一組的期望頻數小於5，使用Fisher's exact test
            contingency = pd.crosstab(
                self.df[feature] == split_value,
                self.df[self.target_col],
            )
            expected = stats.contingency.expected_freq(contingency)
            if np.any(expected < 5):
                oddsratio, p_value = stats.fisher_exact(contingency)
                test_method = "Fisher's exact test (expected freq < 5)"
            # 如果總樣本數小於30，使用Fisher's exact test
            elif total_n < 30:
                oddsratio, p_value = stats.fisher_exact(contingency)
                test_method = "Fisher's exact test (n < 30)"
            # 其他情況使用Chi-square test
            else:
                chi2, p_value, _, _ = stats.chi2_contingency(contingency)
                test_method = "Chi-square test"

        return SplitResult(
            feature=feature,
            feature_type=feature_type,
            rule=rule,
            group_a_rate=group_a_rate * 100,
            group_b_rate=group_b_rate * 100,
            effect_size=effect_size * 100,
            p_value=p_value,
            is_significant=p_value < self.significance_level,
            test_method=test_method,
            group_a_count=n_a,
            group_b_count=n_b,
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

    def get_all_category_splits(self, feature: str) -> List[SplitResult]:
        """獲取指定類別型變數的所有可能分群方式"""
        if feature not in self.discrete_features:
            raise ValueError(f"特徵 {feature} 不是類別型變數")

        splits = self._analyze_discrete_feature(feature)

        # 根據效應大小排序
        splits.sort(key=lambda x: x.effect_size, reverse=True)

        return splits
