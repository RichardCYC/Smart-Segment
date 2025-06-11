# Smart Segments

A web-based tool for analyzing and optimizing feature segmentation in CSV files for binary classification tasks.

## Features

- Upload CSV files and specify binary target variables
- Automatic feature type detection (discrete/continuous)
- Calculate feature importance scores
- Optimize segmentation for continuous features
- Provide feature rankings and detailed analysis reports

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install frontend dependencies:
```bash
cd frontend
npm install
```

3. Start the backend server:
```bash
python app.py
```

4. Start the frontend development server:
```bash
cd frontend
npm start
```

## Usage

1. Open your browser and visit http://localhost:3000
2. Upload your CSV file
3. Select the target variable column
4. View the analysis results

## Tech Stack

- Backend: Python Flask
- Frontend: React
- Data Processing: Pandas, NumPy, scikit-learn