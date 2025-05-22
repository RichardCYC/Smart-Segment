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
    target_type: Literal["binary", "continuous"]


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

            # 檢查目標變量是否為二元變量
            is_binary_target = self.df[self.target_col].nunique() == 2
            target_type = "binary" if is_binary_target else "continuous"

            if is_binary_target:
                # 二元目標變量的處理邏輯
                if total_n < 30 or n_a < 30 or n_b < 30:
                    # 使用 Fisher's exact test
                    contingency = pd.crosstab(
                        self.df[feature] > split_value,
                        self.df[self.target_col],
                    )
                    oddsratio, p_value = stats.fisher_exact(contingency)
                    test_method = "Fisher's exact test (small sample)"
                else:
                    # 使用 two-proportion z-test
                    p_a = group_a[self.target_col].mean()
                    p_b = group_b[self.target_col].mean()
                    n_a = len(group_a)
                    n_b = len(group_b)

                    # 計算合併比例
                    p_pooled = (p_a * n_a + p_b * n_b) / (n_a + n_b)

                    # 計算 z 統計量
                    z = (p_a - p_b) / np.sqrt(
                        p_pooled * (1 - p_pooled) * (1 / n_a + 1 / n_b)
                    )
                    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
                    test_method = "Two-proportion z-test"
            else:
                # 連續目標變量的處理邏輯
                if total_n < 30 or n_a < 30 or n_b < 30:
                    # 使用 Mann-Whitney U test
                    stat, p_value = stats.mannwhitneyu(
                        group_a[self.target_col],
                        group_b[self.target_col],
                        alternative="two-sided",
                    )
                    test_method = "Mann-Whitney U test (small sample)"
                else:
                    # 檢查數據變異性
                    def check_variability(data):
                        if len(data) < 2:
                            return False
                        # 計算變異係數
                        cv = np.std(data) / np.mean(data) if np.mean(data) != 0 else 0
                        # 如果變異係數太小（小於0.01），認為數據變異性不足
                        return cv >= 0.01

                    # 檢查兩組數據的變異性
                    a_variable = check_variability(group_a[self.target_col])
                    b_variable = check_variability(group_b[self.target_col])

                    if not (a_variable and b_variable):
                        # 如果任一組數據變異性不足，使用 Mann-Whitney U test
                        stat, p_value = stats.mannwhitneyu(
                            group_a[self.target_col],
                            group_b[self.target_col],
                            alternative="two-sided",
                        )
                        test_method = "Mann-Whitney U test (low variability)"
                    else:
                        try:
                            # 計算偏度
                            skew_a = stats.skew(group_a[self.target_col])
                            skew_b = stats.skew(group_b[self.target_col])

                            if abs(skew_a) > 2 or abs(skew_b) > 2:
                                # 使用 Mann-Whitney U test 處理偏斜數據
                                stat, p_value = stats.mannwhitneyu(
                                    group_a[self.target_col],
                                    group_b[self.target_col],
                                    alternative="two-sided",
                                )
                                test_method = "Mann-Whitney U test (skewed data)"
                            else:
                                # 使用 Welch's t-test
                                stat, p_value = stats.ttest_ind(
                                    group_a[self.target_col],
                                    group_b[self.target_col],
                                    equal_var=False,
                                )
                                test_method = "Welch's t-test"
                        except RuntimeWarning:
                            # 如果計算偏度時出現警告，使用 Mann-Whitney U test
                            stat, p_value = stats.mannwhitneyu(
                                group_a[self.target_col],
                                group_b[self.target_col],
                                alternative="two-sided",
                            )
                            test_method = (
                                "Mann-Whitney U test (skew calculation failed)"
                            )
        else:
            # 離散型特徵的分割（one-vs-rest）
            group_a = self.df[self.df[feature] == split_value]
            group_b = self.df[self.df[feature] != split_value]
            rule = f"{feature} = {split_value}"
            group_a_rate = group_a[self.target_col].mean()
            group_b_rate = group_b[self.target_col].mean()
            effect_size = abs(group_a_rate - group_b_rate)

            n_a = len(group_a)
            n_b = len(group_b)
            total_n = len(self.df)

            # 檢查目標變量是否為二元變量
            is_binary_target = self.df[self.target_col].nunique() == 2
            target_type = "binary" if is_binary_target else "continuous"

            if is_binary_target:
                # 二元目標變量的處理邏輯
                contingency = pd.crosstab(
                    self.df[feature] == split_value,
                    self.df[self.target_col],
                )
                expected = stats.contingency.expected_freq(contingency)

                if np.any(expected < 5) or total_n < 30 or n_a < 30 or n_b < 30:
                    # 使用 Fisher's exact test
                    oddsratio, p_value = stats.fisher_exact(contingency)
                    test_method = (
                        "Fisher's exact test (small sample or expected freq < 5)"
                    )
                else:
                    # 使用 two-proportion z-test
                    p_a = group_a[self.target_col].mean()
                    p_b = group_b[self.target_col].mean()
                    p_pooled = (p_a * n_a + p_b * n_b) / (n_a + n_b)
                    z = (p_a - p_b) / np.sqrt(
                        p_pooled * (1 - p_pooled) * (1 / n_a + 1 / n_b)
                    )
                    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
                    test_method = "Two-proportion z-test"
            else:
                # 連續目標變量的處理邏輯
                if total_n < 30 or n_a < 30 or n_b < 30:
                    # 使用 Mann-Whitney U test
                    stat, p_value = stats.mannwhitneyu(
                        group_a[self.target_col],
                        group_b[self.target_col],
                        alternative="two-sided",
                    )
                    test_method = "Mann-Whitney U test (small sample)"
                else:
                    # 檢查數據變異性
                    def check_variability(data):
                        if len(data) < 2:
                            return False
                        # 計算變異係數
                        cv = np.std(data) / np.mean(data) if np.mean(data) != 0 else 0
                        # 如果變異係數太小（小於0.01），認為數據變異性不足
                        return cv >= 0.01

                    # 檢查兩組數據的變異性
                    a_variable = check_variability(group_a[self.target_col])
                    b_variable = check_variability(group_b[self.target_col])

                    if not (a_variable and b_variable):
                        # 如果任一組數據變異性不足，使用 Mann-Whitney U test
                        stat, p_value = stats.mannwhitneyu(
                            group_a[self.target_col],
                            group_b[self.target_col],
                            alternative="two-sided",
                        )
                        test_method = "Mann-Whitney U test (low variability)"
                    else:
                        try:
                            # 計算偏度
                            skew_a = stats.skew(group_a[self.target_col])
                            skew_b = stats.skew(group_b[self.target_col])

                            if abs(skew_a) > 2 or abs(skew_b) > 2:
                                # 使用 Mann-Whitney U test 處理偏斜數據
                                stat, p_value = stats.mannwhitneyu(
                                    group_a[self.target_col],
                                    group_b[self.target_col],
                                    alternative="two-sided",
                                )
                                test_method = "Mann-Whitney U test (skewed data)"
                            else:
                                # 使用 Welch's t-test
                                stat, p_value = stats.ttest_ind(
                                    group_a[self.target_col],
                                    group_b[self.target_col],
                                    equal_var=False,
                                )
                                test_method = "Welch's t-test"
                        except RuntimeWarning:
                            # 如果計算偏度時出現警告，使用 Mann-Whitney U test
                            stat, p_value = stats.mannwhitneyu(
                                group_a[self.target_col],
                                group_b[self.target_col],
                                alternative="two-sided",
                            )
                            test_method = (
                                "Mann-Whitney U test (skew calculation failed)"
                            )

        return SplitResult(
            feature=feature,
            feature_type=feature_type,
            rule=rule,
            group_a_rate=(
                group_a_rate * 100 if target_type == "binary" else group_a_rate
            ),
            group_b_rate=(
                group_b_rate * 100 if target_type == "binary" else group_b_rate
            ),
            effect_size=effect_size * 100 if target_type == "binary" else effect_size,
            p_value=p_value,
            is_significant=p_value < self.significance_level,
            test_method=test_method,
            group_a_count=n_a,
            group_b_count=n_b,
            target_type=target_type,
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
