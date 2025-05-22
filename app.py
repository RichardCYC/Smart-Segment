import json
import logging
import os

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

from feature_analysis import FeatureAnalyzer, SortMode

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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

        # Create feature analyzer
        analyzer = FeatureAnalyzer(
            df,
            target_column,
            significance_level=significance_level,
            sort_mode=SortMode.IMPACT if sort_mode == "impact" else SortMode.P_VALUE,
        )

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
