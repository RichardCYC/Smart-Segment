import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Container,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Switch,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import React, { useState } from 'react';
import FeatureResults from './components/FeatureResults';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  const [file, setFile] = useState(null);
  const [targetColumn, setTargetColumn] = useState('');
  const [columns, setColumns] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [viewMode, setViewMode] = useState('best_per_feature');
  const [significanceLevel, setSignificanceLevel] = useState('0.05');
  const [sortMode, setSortMode] = useState('impact');
  const [showNonSignificant, setShowNonSignificant] = useState(true);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      // 檢查文件大小（16MB限制）
      if (file.size > 16 * 1024 * 1024) {
        setError('文件大小不能超過16MB');
        setFile(null);
        return;
      }

      // 檢查文件類型
      if (!file.name.toLowerCase().endsWith('.csv')) {
        setError('只允許上傳CSV文件');
        setFile(null);
        return;
      }

      setFile(file);
      setError('');
      // 讀取CSV文件頭部來獲取列名
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const text = e.target.result;
          const headers = text.split('\n')[0].split(',');
          setColumns(headers);
        } catch (err) {
          setError('無法讀取CSV文件');
          setFile(null);
          setColumns([]);
        }
      };
      reader.onerror = () => {
        setError('文件讀取錯誤');
        setFile(null);
        setColumns([]);
      };
      reader.readAsText(file);
    }
  };

  const handleViewModeChange = (event, newMode) => {
    if (newMode !== null) {
      setViewMode(newMode);
      if (results) {
        handleAnalyze(); // 重新分析以更新視圖
      }
    }
  };

  const handleSortModeChange = (event, newMode) => {
    if (newMode !== null) {
      setSortMode(newMode);
      if (results) {
        handleAnalyze(); // 重新分析以更新視圖
      }
    }
  };

  const handleAnalyze = async () => {
    if (!file || !targetColumn) {
      setError('請選擇文件和目標變量列');
      return;
    }

    // 驗證顯著水準
    const alpha = parseFloat(significanceLevel);
    if (isNaN(alpha) || alpha <= 0 || alpha >= 1) {
      setError('顯著水準必須是0到1之間的數字');
      return;
    }

    setLoading(true);
    setError('');
    setResults(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('targetColumn', targetColumn);
    formData.append('viewMode', viewMode);
    formData.append('significanceLevel', significanceLevel);
    formData.append('sortMode', sortMode);
    formData.append('showNonSignificant', showNonSignificant.toString());

    try {
      const response = await fetch('http://localhost:5000/api/analyze', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (data.success) {
        setResults(data.results);
      } else {
        setError(data.error || '分析過程中發生錯誤');
      }
    } catch (err) {
      setError('無法連接到服務器');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom align="center">
            CSV二元分段分析工具
          </Typography>

          <Paper sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button
                variant="contained"
                component="label"
                startIcon={<CloudUploadIcon />}
              >
                上傳CSV文件
                <input
                  type="file"
                  hidden
                  accept=".csv"
                  onChange={handleFileUpload}
                />
              </Button>

              {file && (
                <Typography variant="body2" color="text.secondary">
                  已選擇文件: {file.name}
                </Typography>
              )}

              {columns.length > 0 && (
                <FormControl fullWidth>
                  <InputLabel>選擇目標變量列</InputLabel>
                  <Select
                    value={targetColumn}
                    label="選擇目標變量列"
                    onChange={(e) => setTargetColumn(e.target.value)}
                  >
                    {columns.map((column) => (
                      <MenuItem key={column} value={column}>
                        {column}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}

              <TextField
                label="顯著水準 (α)"
                type="number"
                value={significanceLevel}
                onChange={(e) => setSignificanceLevel(e.target.value)}
                inputProps={{ step: "0.01", min: "0.01", max: "0.99" }}
                helperText="請輸入0到1之間的數字，例如：0.05"
                fullWidth
              />

              <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                <ToggleButtonGroup
                  value={viewMode}
                  exclusive
                  onChange={handleViewModeChange}
                  aria-label="視圖模式"
                >
                  <ToggleButton value="best_per_feature" aria-label="每個特徵最佳分割">
                    每個特徵最佳分割
                  </ToggleButton>
                  <ToggleButton value="top_5_global" aria-label="全局前5最佳分割">
                    全局前5最佳分割
                  </ToggleButton>
                </ToggleButtonGroup>
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                <ToggleButtonGroup
                  value={sortMode}
                  exclusive
                  onChange={handleSortModeChange}
                  aria-label="排序模式"
                >
                  <ToggleButton value="impact" aria-label="按效應大小排序">
                    按效應大小排序
                  </ToggleButton>
                  <ToggleButton value="p_value" aria-label="按p值排序">
                    按p值排序
                  </ToggleButton>
                </ToggleButtonGroup>
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={showNonSignificant}
                    onChange={(e) => setShowNonSignificant(e.target.checked)}
                  />
                }
                label="顯示非顯著結果"
              />

              <Button
                variant="contained"
                color="primary"
                onClick={handleAnalyze}
                disabled={loading || !file || !targetColumn}
              >
                {loading ? <CircularProgress size={24} /> : '開始分析'}
              </Button>
            </Box>
          </Paper>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {results && <FeatureResults results={results} />}
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;