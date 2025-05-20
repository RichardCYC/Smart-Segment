import json
import logging
import os

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

from feature_analysis import FeatureAnalyzer, SortMode

# 配置日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# 自定義 JSON 編碼器
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
app.json_encoder = NumpyEncoder  # 使用自定義編碼器

# 配置
UPLOAD_FOLDER = "uploads"
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {"csv"}

# 確保上傳目錄存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/api/analyze", methods=["POST"])
def analyze_csv():
    try:
        # 檢查是否有文件
        if "file" not in request.files:
            return jsonify({"success": False, "error": "沒有上傳文件"}), 400

        file = request.files["file"]

        # 檢查文件名
        if file.filename == "":
            return jsonify({"success": False, "error": "沒有選擇文件"}), 400

        # 檢查文件類型
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "只允許上傳CSV文件"}), 400

        # 檢查目標列
        target_column = request.form.get("targetColumn")
        if not target_column:
            return jsonify({"success": False, "error": "未指定目標列"}), 400

        # 獲取其他參數
        view_mode = request.form.get("viewMode", "best_per_feature")
        significance_level = float(request.form.get("significanceLevel", "0.05"))
        sort_mode = request.form.get("sortMode", "impact")
        show_non_significant = (
            request.form.get("showNonSignificant", "true").lower() == "true"
        )

        # 讀取CSV
        try:
            df = pd.read_csv(file)
        except Exception as e:
            return (
                jsonify({"success": False, "error": f"CSV文件讀取錯誤: {str(e)}"}),
                400,
            )

        # 檢查目標列是否存在
        if target_column not in df.columns:
            return (
                jsonify(
                    {"success": False, "error": f"目標列 '{target_column}' 不存在"}
                ),
                400,
            )

        # 檢查數據量
        if len(df) > 100000:  # 限制最大行數
            return (
                jsonify({"success": False, "error": "數據量過大，請限制在10萬行以內"}),
                400,
            )

        # 確保目標變量是二元的
        try:
            df[target_column] = df[target_column].astype(bool)
        except Exception as e:
            return (
                jsonify(
                    {"success": False, "error": f"目標列轉換為布爾值失敗: {str(e)}"}
                ),
                400,
            )

        # 創建特徵分析器
        analyzer = FeatureAnalyzer(
            df,
            target_column,
            significance_level=significance_level,
            sort_mode=SortMode.IMPACT if sort_mode == "impact" else SortMode.P_VALUE,
        )

        if view_mode == "best_per_feature":
            # 獲取每個特徵的最佳分割
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
                    "summary": f"特徵 {split.feature} ({split.feature_type}) 的最佳分割點為 {split.rule}，"
                    f"效應大小為 {split.effect_size:.2f}%，"
                    f"p值為 {split.p_value:.4f}，"
                    f"使用 {split.test_method} 進行檢定",
                }
                for split in results.values()
                if show_non_significant or split.is_significant
            ]
        else:
            # 獲取全局最佳分割
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
                    "summary": f"特徵 {split.feature} ({split.feature_type}) 的分割點 {split.rule}，"
                    f"效應大小為 {split.effect_size:.2f}%，"
                    f"p值為 {split.p_value:.4f}，"
                    f"使用 {split.test_method} 進行檢定",
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
        logger.error(f"處理請求時發生錯誤: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/category-splits", methods=["POST"])
def get_category_splits():
    try:
        # 檢查是否有文件
        if "file" not in request.files:
            return jsonify({"success": False, "error": "沒有上傳文件"}), 400

        file = request.files["file"]

        # 檢查文件名
        if file.filename == "":
            return jsonify({"success": False, "error": "沒有選擇文件"}), 400

        # 檢查文件類型
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "只允許上傳CSV文件"}), 400

        # 檢查目標列
        target_column = request.form.get("targetColumn")
        if not target_column:
            return jsonify({"success": False, "error": "未指定目標列"}), 400

        # 檢查特徵列
        feature = request.form.get("feature")
        if not feature:
            return jsonify({"success": False, "error": "未指定特徵列"}), 400

        # 獲取顯著性水平
        significance_level = float(request.form.get("significanceLevel", "0.05"))

        # 讀取CSV
        try:
            df = pd.read_csv(file)
        except Exception as e:
            return (
                jsonify({"success": False, "error": f"CSV文件讀取錯誤: {str(e)}"}),
                400,
            )

        # 檢查目標列和特徵列是否存在
        if target_column not in df.columns:
            return (
                jsonify(
                    {"success": False, "error": f"目標列 '{target_column}' 不存在"}
                ),
                400,
            )
        if feature not in df.columns:
            return (
                jsonify({"success": False, "error": f"特徵列 '{feature}' 不存在"}),
                400,
            )

        # 確保目標變量是二元的
        try:
            df[target_column] = df[target_column].astype(bool)
        except Exception as e:
            return (
                jsonify(
                    {"success": False, "error": f"目標列轉換為布爾值失敗: {str(e)}"}
                ),
                400,
            )

        # 創建特徵分析器
        analyzer = FeatureAnalyzer(
            df,
            target_column,
            significance_level=significance_level,
            sort_mode=SortMode.IMPACT,
        )

        # 獲取所有分群方式
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
                    "summary": f"特徵 {split.feature} ({split.feature_type}) 的分割點 {split.rule}，"
                    f"效應大小為 {split.effect_size:.2f}%，"
                    f"p值為 {split.p_value:.4f}，"
                    f"使用 {split.test_method} 進行檢定",
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
        logger.error(f"處理請求時發生錯誤: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/discrete-features", methods=["POST"])
def get_discrete_features():
    try:
        # 檢查是否有文件
        if "file" not in request.files:
            return jsonify({"success": False, "error": "沒有上傳文件"}), 400

        file = request.files["file"]

        # 檢查文件名
        if file.filename == "":
            return jsonify({"success": False, "error": "沒有選擇文件"}), 400

        # 檢查文件類型
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "只允許上傳CSV文件"}), 400

        # 檢查目標列
        target_column = request.form.get("targetColumn")
        if not target_column:
            return jsonify({"success": False, "error": "未指定目標列"}), 400

        # 讀取CSV
        try:
            df = pd.read_csv(file)
        except Exception as e:
            return (
                jsonify({"success": False, "error": f"CSV文件讀取錯誤: {str(e)}"}),
                400,
            )

        # 檢查目標列是否存在
        if target_column not in df.columns:
            return (
                jsonify(
                    {"success": False, "error": f"目標列 '{target_column}' 不存在"}
                ),
                400,
            )

        # 創建特徵分析器
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
        logger.error(f"處理請求時發生錯誤: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 400


if __name__ == "__main__":
    logger.info("啟動 Flask 應用程序...")
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=True)  # 啟用自動重載
