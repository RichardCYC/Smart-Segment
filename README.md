# CSV Binary Segmentation Helper

這是一個網頁工具，用於分析CSV檔案中的特徵如何區分二元目標變量。

## 功能特點

- 上傳CSV檔案並指定二元目標變量
- 自動檢測特徵類型（離散/連續）
- 計算特徵重要性分數
- 對連續特徵進行最佳分段
- 提供特徵排名和詳細分析報告

## 安裝說明

1. 安裝Python依賴：
```bash
pip install -r requirements.txt
```

2. 安裝前端依賴：
```bash
cd frontend
npm install
```

3. 啟動後端服務器：
```bash
python app.py
```

4. 啟動前端開發服務器：
```bash
cd frontend
npm start
```

## 使用說明

1. 打開瀏覽器訪問 http://localhost:3000
2. 上傳CSV檔案
3. 選擇目標變量列
4. 查看分析結果

## 技術棧

- 後端：Python Flask
- 前端：React
- 數據處理：Pandas, NumPy, scikit-learn