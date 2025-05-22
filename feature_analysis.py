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
        """Classify features as discrete and continuous"""
        self.continuous_features = []
        self.discrete_features = []

        for col in self.df.columns:
            if col == self.target_col:
                continue

            if self.df[col].dtype in ["int64", "float64"]:
                if (
                    self.df[col].nunique() > 10
                ):  # If unique values exceed 10, treat as continuous
                    self.continuous_features.append(col)
                else:
                    self.discrete_features.append(col)
            else:
                self.discrete_features.append(col)

    def _calculate_split_statistics(
        self, feature: str, split_value: float, feature_type: str = "continuous"
    ) -> SplitResult:
        """Calculate statistical indicators for a given split point"""
        if feature_type == "continuous":
            # Split for continuous features
            group_a = self.df[self.df[feature] > split_value]
            group_b = self.df[self.df[feature] <= split_value]
            rule = f"{feature} > {split_value:.2f}"
            # Calculate target variable ratio for each group
            group_a_rate = group_a[self.target_col].mean()
            group_b_rate = group_b[self.target_col].mean()
            # Calculate effect size (absolute difference)
            effect_size = abs(group_a_rate - group_b_rate)

            # Dynamically determine test method based on dataset size
            n_a = len(group_a)
            n_b = len(group_b)
            total_n = len(self.df)

            # Check if target variable is binary variable
            is_binary_target = self.df[self.target_col].nunique() == 2
            target_type = "binary" if is_binary_target else "continuous"

            if is_binary_target:
                # Binary target variable processing logic
                if total_n < 30 or n_a < 30 or n_b < 30:
                    # Use Fisher's exact test
                    contingency = pd.crosstab(
                        self.df[feature] > split_value,
                        self.df[self.target_col],
                    )
                    oddsratio, p_value = stats.fisher_exact(contingency)
                    test_method = "Fisher's exact test (small sample)"
                else:
                    # Use two-proportion z-test
                    p_a = group_a[self.target_col].mean()
                    p_b = group_b[self.target_col].mean()
                    n_a = len(group_a)
                    n_b = len(group_b)

                    # Calculate merged proportion
                    p_pooled = (p_a * n_a + p_b * n_b) / (n_a + n_b)

                    # Calculate z statistic
                    z = (p_a - p_b) / np.sqrt(
                        p_pooled * (1 - p_pooled) * (1 / n_a + 1 / n_b)
                    )
                    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
                    test_method = "Two-proportion z-test"
            else:
                # Continuous target variable processing logic
                if total_n < 30 or n_a < 30 or n_b < 30:
                    # Use Mann-Whitney U test
                    stat, p_value = stats.mannwhitneyu(
                        group_a[self.target_col],
                        group_b[self.target_col],
                        alternative="two-sided",
                    )
                    test_method = "Mann-Whitney U test (small sample)"
                else:
                    # Check data variability
                    def check_variability(data):
                        if len(data) < 2:
                            return False
                        # Calculate coefficient of variation
                        cv = np.std(data) / np.mean(data) if np.mean(data) != 0 else 0
                        # If coefficient of variation is too small (less than 0.01), consider data variability insufficient
                        return cv >= 0.01

                    # Check data variability of two groups
                    a_variable = check_variability(group_a[self.target_col])
                    b_variable = check_variability(group_b[self.target_col])

                    if not (a_variable and b_variable):
                        # If one group data variability is insufficient, use Mann-Whitney U test
                        stat, p_value = stats.mannwhitneyu(
                            group_a[self.target_col],
                            group_b[self.target_col],
                            alternative="two-sided",
                        )
                        test_method = "Mann-Whitney U test (low variability)"
                    else:
                        try:
                            # Calculate skewness
                            skew_a = stats.skew(group_a[self.target_col])
                            skew_b = stats.skew(group_b[self.target_col])

                            if abs(skew_a) > 2 or abs(skew_b) > 2:
                                # Use Mann-Whitney U test to process skewed data
                                stat, p_value = stats.mannwhitneyu(
                                    group_a[self.target_col],
                                    group_b[self.target_col],
                                    alternative="two-sided",
                                )
                                test_method = "Mann-Whitney U test (skewed data)"
                            else:
                                # Use Welch's t-test
                                stat, p_value = stats.ttest_ind(
                                    group_a[self.target_col],
                                    group_b[self.target_col],
                                    equal_var=False,
                                )
                                test_method = "Welch's t-test"
                        except RuntimeWarning:
                            # If skewness calculation warning occurs, use Mann-Whitney U test
                            stat, p_value = stats.mannwhitneyu(
                                group_a[self.target_col],
                                group_b[self.target_col],
                                alternative="two-sided",
                            )
                            test_method = (
                                "Mann-Whitney U test (skew calculation failed)"
                            )
        else:
            # Split for discrete features (one-vs-rest)
            group_a = self.df[self.df[feature] == split_value]
            group_b = self.df[self.df[feature] != split_value]
            rule = f"{feature} = {split_value}"
            group_a_rate = group_a[self.target_col].mean()
            group_b_rate = group_b[self.target_col].mean()
            effect_size = abs(group_a_rate - group_b_rate)

            n_a = len(group_a)
            n_b = len(group_b)
            total_n = len(self.df)

            # Check if target variable is binary variable
            is_binary_target = self.df[self.target_col].nunique() == 2
            target_type = "binary" if is_binary_target else "continuous"

            if is_binary_target:
                # Binary target variable processing logic
                contingency = pd.crosstab(
                    self.df[feature] == split_value,
                    self.df[self.target_col],
                )
                expected = stats.contingency.expected_freq(contingency)

                if np.any(expected < 5) or total_n < 30 or n_a < 30 or n_b < 30:
                    # Use Fisher's exact test
                    oddsratio, p_value = stats.fisher_exact(contingency)
                    test_method = (
                        "Fisher's exact test (small sample or expected freq < 5)"
                    )
                else:
                    # Use two-proportion z-test
                    p_a = group_a[self.target_col].mean()
                    p_b = group_b[self.target_col].mean()
                    p_pooled = (p_a * n_a + p_b * n_b) / (n_a + n_b)
                    z = (p_a - p_b) / np.sqrt(
                        p_pooled * (1 - p_pooled) * (1 / n_a + 1 / n_b)
                    )
                    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
                    test_method = "Two-proportion z-test"
            else:
                # Continuous target variable processing logic
                if total_n < 30 or n_a < 30 or n_b < 30:
                    # Use Mann-Whitney U test
                    stat, p_value = stats.mannwhitneyu(
                        group_a[self.target_col],
                        group_b[self.target_col],
                        alternative="two-sided",
                    )
                    test_method = "Mann-Whitney U test (small sample)"
                else:
                    # Check data variability
                    def check_variability(data):
                        if len(data) < 2:
                            return False
                        # Calculate coefficient of variation
                        cv = np.std(data) / np.mean(data) if np.mean(data) != 0 else 0
                        # If coefficient of variation is too small (less than 0.01), consider data variability insufficient
                        return cv >= 0.01

                    # Check data variability of two groups
                    a_variable = check_variability(group_a[self.target_col])
                    b_variable = check_variability(group_b[self.target_col])

                    if not (a_variable and b_variable):
                        # If one group data variability is insufficient, use Mann-Whitney U test
                        stat, p_value = stats.mannwhitneyu(
                            group_a[self.target_col],
                            group_b[self.target_col],
                            alternative="two-sided",
                        )
                        test_method = "Mann-Whitney U test (low variability)"
                    else:
                        try:
                            # Calculate skewness
                            skew_a = stats.skew(group_a[self.target_col])
                            skew_b = stats.skew(group_b[self.target_col])

                            if abs(skew_a) > 2 or abs(skew_b) > 2:
                                # Use Mann-Whitney U test to process skewed data
                                stat, p_value = stats.mannwhitneyu(
                                    group_a[self.target_col],
                                    group_b[self.target_col],
                                    alternative="two-sided",
                                )
                                test_method = "Mann-Whitney U test (skewed data)"
                            else:
                                # Use Welch's t-test
                                stat, p_value = stats.ttest_ind(
                                    group_a[self.target_col],
                                    group_b[self.target_col],
                                    equal_var=False,
                                )
                                test_method = "Welch's t-test"
                        except RuntimeWarning:
                            # If skewness calculation warning occurs, use Mann-Whitney U test
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
        """Analyze discrete features"""
        splits = []
        for category in self.df[feature].unique():
            split_result = self._calculate_split_statistics(
                feature, category, feature_type="discrete"
            )
            splits.append(split_result)
        return splits

    def find_best_splits(self, n_splits: int = 5) -> List[SplitResult]:
        """Find the best split point for all features"""
        all_splits = []

        # Analyze continuous features
        for feature in self.continuous_features:
            percentiles = np.linspace(0.1, 0.9, 9)
            split_points = np.percentile(self.df[feature], percentiles * 100)

            for split_point in split_points:
                split_result = self._calculate_split_statistics(feature, split_point)
                all_splits.append(split_result)

        # Analyze discrete features
        for feature in self.discrete_features:
            splits = self._analyze_discrete_feature(feature)
            all_splits.extend(splits)

        # Group by significance
        significant_splits = [s for s in all_splits if s.is_significant]
        non_significant_splits = [s for s in all_splits if not s.is_significant]

        # Sort significant results based on sorting mode
        if self.sort_mode == SortMode.IMPACT:
            significant_splits.sort(key=lambda x: x.effect_size, reverse=True)
        else:  # SortMode.P_VALUE
            significant_splits.sort(key=lambda x: x.p_value)

        # Non-significant results are always sorted by effect size
        non_significant_splits.sort(key=lambda x: x.effect_size, reverse=True)

        return significant_splits + non_significant_splits

    def get_top_splits_per_feature(self) -> Dict[str, SplitResult]:
        """Get the best split for each feature"""
        all_splits = self.find_best_splits()
        best_splits = {}

        for split in all_splits:
            if split.feature not in best_splits:
                best_splits[split.feature] = split
            elif split.effect_size > best_splits[split.feature].effect_size:
                best_splits[split.feature] = split

        return best_splits

    def get_all_category_splits(self, feature: str) -> List[SplitResult]:
        """Get all possible grouping methods for specified category variable"""
        if feature not in self.discrete_features:
            raise ValueError(f"Feature {feature} is not a category variable")

        splits = self._analyze_discrete_feature(feature)

        # Sort by effect size
        splits.sort(key=lambda x: x.effect_size, reverse=True)

        return splits
