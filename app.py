import json
import logging
import os
import time
import traceback
from datetime import datetime

import numpy as np
import pandas as pd
import psutil
from flask import Flask, jsonify, request
from flask_cors import CORS
from scipy import stats
from werkzeug.utils import secure_filename

from feature_analysis import FeatureAnalyzer, SortMode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def log_system_metrics():
    process = psutil.Process()
    memory_info = process.memory_info()
    return {
        "memory_usage_mb": memory_info.rss / 1024 / 1024,
        "cpu_percent": process.cpu_percent(),
        "thread_count": process.num_threads(),
    }


def log_request_info():
    return {
        "timestamp": datetime.now().isoformat(),
        "endpoint": request.endpoint,
        "method": request.method,
        "ip": request.remote_addr,
        "user_agent": request.user_agent.string,
    }


# Custom JSON encoder
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)


app = Flask(__name__)
CORS(app)
app.json_encoder = NumpyEncoder  # Use custom encoder

# Configuration
UPLOAD_FOLDER = "uploads"
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {"csv"}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class FeatureAnalyzer:
    def __init__(self, df, target_column, significance_level=0.05):
        self.df = df
        self.target_column = target_column
        self.significance_level = significance_level
        self.target_type = self._determine_target_type()
        self.feature_types = self._determine_feature_types()

    def _determine_target_type(self):
        # Determine if target is binary or continuous
        unique_values = self.df[self.target_column].nunique()
        if unique_values == 2:
            return "binary"
        return "continuous"

    def _determine_feature_types(self):
        # Determine feature types (discrete or continuous)
        feature_types = {}
        for column in self.df.columns:
            if column == self.target_column:
                continue
            unique_values = self.df[column].nunique()
            if unique_values <= 10:  # Consider as discrete if unique values <= 10
                feature_types[column] = "discrete"
            else:
                feature_types[column] = "continuous"
        return feature_types

    def _calculate_effect_size(self, group_a, group_b):
        if self.target_type == "binary":
            # For binary target, calculate percentage difference
            return abs(group_a.mean() - group_b.mean()) * 100
        else:
            # For continuous target, calculate Cohen's d
            n1, n2 = len(group_a), len(group_b)
            var1, var2 = group_a.var(), group_b.var()
            pooled_se = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
            return abs(group_a.mean() - group_b.mean()) / pooled_se

    def _perform_statistical_test(self, group_a, group_b):
        if self.target_type == "binary":
            # Chi-square test for binary target
            contingency = pd.crosstab(
                pd.concat(
                    [pd.Series(["A"] * len(group_a)), pd.Series(["B"] * len(group_b))]
                ),
                pd.concat([group_a, group_b]),
            )
            chi2, p_value = stats.chi2_contingency(contingency)[:2]
            return p_value, "chi-square"
        else:
            # T-test for continuous target
            t_stat, p_value = stats.ttest_ind(group_a, group_b)
            return p_value, "t-test"

    def find_best_split(self, feature):
        best_split = None
        best_effect_size = -1
        best_p_value = 1
        best_rule = None

        if self.feature_types[feature] == "discrete":
            # For discrete features, try each unique value as a split point
            unique_values = self.df[feature].unique()
            for value in unique_values:
                group_a = self.df[self.df[feature] == value][self.target_column]
                group_b = self.df[self.df[feature] != value][self.target_column]

                if len(group_a) == 0 or len(group_b) == 0:
                    continue

                effect_size = self._calculate_effect_size(group_a, group_b)
                p_value, test_method = self._perform_statistical_test(group_a, group_b)

                if effect_size > best_effect_size:
                    best_effect_size = effect_size
                    best_p_value = p_value
                    best_split = (group_a, group_b)
                    best_rule = f"{feature} = {value}"

        else:
            # For continuous features, try different percentiles as split points
            percentiles = [25, 50, 75]
            for p in percentiles:
                split_value = self.df[feature].quantile(p / 100)
                group_a = self.df[self.df[feature] >= split_value][self.target_column]
                group_b = self.df[self.df[feature] < split_value][self.target_column]

                if len(group_a) == 0 or len(group_b) == 0:
                    continue

                effect_size = self._calculate_effect_size(group_a, group_b)
                p_value, test_method = self._perform_statistical_test(group_a, group_b)

                if effect_size > best_effect_size:
                    best_effect_size = effect_size
                    best_p_value = p_value
                    best_split = (group_a, group_b)
                    best_rule = f"{feature} >= {split_value:.2f}"

        if best_split is None:
            return None

        group_a, group_b = best_split
        return {
            "feature": feature,
            "feature_type": self.feature_types[feature],
            "rule": best_rule,
            "group_a_rate": (
                group_a.mean() * 100 if self.target_type == "binary" else group_a.mean()
            ),
            "group_b_rate": (
                group_b.mean() * 100 if self.target_type == "binary" else group_b.mean()
            ),
            "effect_size": best_effect_size,
            "p_value": best_p_value,
            "is_significant": best_p_value < self.significance_level,
            "test_method": test_method,
            "group_a_count": len(group_a),
            "group_b_count": len(group_b),
        }

    def get_top_splits_per_feature(self):
        results = {}
        for feature in self.df.columns:
            if feature != self.target_column:
                split_result = self.find_best_split(feature)
                if split_result:
                    results[feature] = split_result
        return results

    def find_best_splits(self, n_splits=5):
        all_splits = []
        for feature in self.df.columns:
            if feature != self.target_column:
                split_result = self.find_best_split(feature)
                if split_result:
                    all_splits.append(split_result)

        # Sort by effect size
        all_splits.sort(key=lambda x: x["effect_size"], reverse=True)
        return all_splits[:n_splits]


@app.before_request
def before_request():
    request.start_time = time.time()
    metrics = log_system_metrics()
    request_info = log_request_info()
    logger.info(f"Request started - {request_info} - System metrics: {metrics}")


@app.after_request
def after_request(response):
    if hasattr(request, "start_time"):
        duration = time.time() - request.start_time
        metrics = log_system_metrics()
        logger.info(
            f"Request completed - Duration: {duration:.2f}s - System metrics: {metrics}"
        )
    return response


@app.errorhandler(Exception)
def handle_error(error):
    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
    }
    logger.error(f"Unhandled error: {error_info}")
    return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/analyze", methods=["POST"])
def analyze_csv():
    try:
        # Check if file exists
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400

        file = request.files["file"]

        # Check filename
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400

        # Check file type
        if not allowed_file(file.filename):
            return (
                jsonify({"success": False, "error": "Only CSV files are allowed"}),
                400,
            )

        # Check target column
        target_column = request.form.get("targetColumn")
        if not target_column:
            return (
                jsonify({"success": False, "error": "Target column not specified"}),
                400,
            )

        # Get other parameters
        view_mode = request.form.get("viewMode", "best_per_feature")
        significance_level = float(request.form.get("significanceLevel", "0.05"))
        sort_mode = request.form.get("sortMode", "impact")
        show_non_significant = (
            request.form.get("showNonSignificant", "true").lower() == "true"
        )

        # Read CSV
        try:
            df = pd.read_csv(file)
        except Exception as e:
            return (
                jsonify(
                    {"success": False, "error": f"Error reading CSV file: {str(e)}"}
                ),
                400,
            )

        # Check if target column exists
        if target_column not in df.columns:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Target column '{target_column}' does not exist",
                    }
                ),
                400,
            )

        # Check data size
        if len(df) > 100000:  # Limit maximum rows
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Data size too large, please limit to 100,000 rows",
                    }
                ),
                400,
            )

        # Convert to bool only when target variable is binary
        if df[target_column].nunique() == 2:
            try:
                df[target_column] = df[target_column].astype(bool)
            except Exception as e:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": f"Failed to convert target column to boolean: {str(e)}",
                        }
                    ),
                    400,
                )

        # Initialize analyzer
        analyzer = FeatureAnalyzer(df, target_column, significance_level)

        if view_mode == "best_per_feature":
            # Get best split for each feature
            results = analyzer.get_top_splits_per_feature()
            formatted_results = [
                {
                    "feature": split.feature,
                    "feature_type": split.feature_type,
                    "rule": split.rule,
                    "group_a_rate": round(split.group_a_rate, 2),
                    "group_b_rate": round(split.group_b_rate, 2),
                    "effect_size": round(split.effect_size, 2),
                    "p_value": round(split.p_value, 4),
                    "is_significant": bool(split.is_significant),
                    "test_method": split.test_method,
                    "group_a_count": split.group_a_count,
                    "group_b_count": split.group_b_count,
                    "summary": f"Best split for feature {split.feature} ({split.feature_type}) is at {split.rule},"
                    f"effect size is {split.effect_size:.2f}%, "
                    f"p-value is {split.p_value:.4f}, "
                    f"using {split.test_method} for testing",
                }
                for split in results.values()
                if show_non_significant or split.is_significant
            ]
        else:
            # Get global best split
            results = analyzer.find_best_splits(n_splits=5)
            formatted_results = [
                {
                    "feature": split.feature,
                    "feature_type": split.feature_type,
                    "rule": split.rule,
                    "group_a_rate": round(split.group_a_rate, 2),
                    "group_b_rate": round(split.group_b_rate, 2),
                    "effect_size": round(split.effect_size, 2),
                    "p_value": round(split.p_value, 4),
                    "is_significant": bool(split.is_significant),
                    "test_method": split.test_method,
                    "group_a_count": split.group_a_count,
                    "group_b_count": split.group_b_count,
                    "summary": f"Best split for feature {split.feature} ({split.feature_type}) is at {split.rule},"
                    f"effect size is {split.effect_size:.2f}%, "
                    f"p-value is {split.p_value:.4f}, "
                    f"using {split.test_method} for testing",
                }
                for split in results
                if show_non_significant or split.is_significant
            ][:5]

        return jsonify(
            {
                "success": True,
                "results": formatted_results,
                "view_mode": view_mode,
                "significance_level": significance_level,
                "sort_mode": sort_mode,
                "show_non_significant": show_non_significant,
            }
        )

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/category-splits", methods=["POST"])
def get_category_splits():
    try:
        # Check if file exists
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400

        file = request.files["file"]

        # Check filename
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400

        # Check file type
        if not allowed_file(file.filename):
            return (
                jsonify({"success": False, "error": "Only CSV files are allowed"}),
                400,
            )

        # Check target column
        target_column = request.form.get("targetColumn")
        if not target_column:
            return (
                jsonify({"success": False, "error": "Target column not specified"}),
                400,
            )

        # Check feature column
        feature = request.form.get("feature")
        if not feature:
            return (
                jsonify({"success": False, "error": "Feature column not specified"}),
                400,
            )

        # Get significance level
        significance_level = float(request.form.get("significanceLevel", "0.05"))

        # Read CSV
        try:
            df = pd.read_csv(file)
        except Exception as e:
            return (
                jsonify(
                    {"success": False, "error": f"Error reading CSV file: {str(e)}"}
                ),
                400,
            )

        # Check if target column and feature column exist
        if target_column not in df.columns:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Target column '{target_column}' does not exist",
                    }
                ),
                400,
            )
        if feature not in df.columns:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Feature column '{feature}' does not exist",
                    }
                ),
                400,
            )

        # Convert to bool only when target variable is binary
        if df[target_column].nunique() == 2:
            try:
                df[target_column] = df[target_column].astype(bool)
            except Exception as e:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": f"Failed to convert target column to boolean: {str(e)}",
                        }
                    ),
                    400,
                )

        # Create feature analyzer
        analyzer = FeatureAnalyzer(
            df,
            target_column,
            significance_level=significance_level,
            sort_mode=SortMode.IMPACT,
        )

        # Get all category splits
        try:
            splits = analyzer.get_all_category_splits(feature)
            formatted_results = [
                {
                    "feature": split.feature,
                    "feature_type": split.feature_type,
                    "rule": split.rule,
                    "group_a_rate": round(split.group_a_rate, 2),
                    "group_b_rate": round(split.group_b_rate, 2),
                    "effect_size": round(split.effect_size, 2),
                    "p_value": round(split.p_value, 4),
                    "is_significant": bool(split.is_significant),
                    "test_method": split.test_method,
                    "group_a_count": split.group_a_count,
                    "group_b_count": split.group_b_count,
                    "summary": f"Best split for feature {split.feature} ({split.feature_type}) is at {split.rule},"
                    f"effect size is {split.effect_size:.2f}%, "
                    f"p-value is {split.p_value:.4f}, "
                    f"using {split.test_method} for testing",
                }
                for split in splits
            ]
            return jsonify(
                {
                    "success": True,
                    "results": formatted_results,
                    "feature": feature,
                    "significance_level": significance_level,
                }
            )
        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 400

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/discrete-features", methods=["POST"])
def get_discrete_features():
    try:
        # Check if file exists
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400

        file = request.files["file"]

        # Check filename
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400

        # Check file type
        if not allowed_file(file.filename):
            return (
                jsonify({"success": False, "error": "Only CSV files are allowed"}),
                400,
            )

        # Check target column
        target_column = request.form.get("targetColumn")
        if not target_column:
            return (
                jsonify({"success": False, "error": "Target column not specified"}),
                400,
            )

        # Read CSV
        try:
            df = pd.read_csv(file)
        except Exception as e:
            return (
                jsonify(
                    {"success": False, "error": f"Error reading CSV file: {str(e)}"}
                ),
                400,
            )

        # Check if target column exists
        if target_column not in df.columns:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Target column '{target_column}' does not exist",
                    }
                ),
                400,
            )

        # Create feature analyzer
        analyzer = FeatureAnalyzer(
            df,
            target_column,
            significance_level=0.05,
            sort_mode=SortMode.IMPACT,
        )

        return jsonify(
            {
                "success": True,
                "discrete_features": analyzer.discrete_features,
            }
        )

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 400


if __name__ == "__main__":
    logger.info("Starting Flask application...")
    app.run(
        host="127.0.0.1", port=5000, debug=True, use_reloader=True
    )  # Use auto reload
