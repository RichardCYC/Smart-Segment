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
    Tab,
    Tabs,
    TextField,
    ToggleButton,
    ToggleButtonGroup,
    Typography,
} from '@mui/material';
import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import React, { useState } from 'react';
import FeatureResults from './components/FeatureResults';
import FeedbackForm from './components/FeedbackForm';

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
  const [activeTab, setActiveTab] = useState(0);
  const [categoryResults, setCategoryResults] = useState(null);
  const [selectedFeature, setSelectedFeature] = useState('');
  const [discreteFeatures, setDiscreteFeatures] = useState([]);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Check file size (16MB limit)
      if (file.size > 16 * 1024 * 1024) {
        setError('File size cannot exceed 16MB');
        setFile(null);
        return;
      }

      // Check file type
      if (!file.name.toLowerCase().endsWith('.csv')) {
        setError('Only CSV files are allowed');
        setFile(null);
        return;
      }

      setFile(file);
      setError('');
      // Read CSV file header to get column names
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const text = e.target.result;
          const headers = text.split('\n')[0].split(',');
          setColumns(headers);
        } catch (err) {
          setError('Unable to read CSV file');
          setFile(null);
          setColumns([]);
        }
      };
      reader.onerror = () => {
        setError('File reading error');
        setFile(null);
        setColumns([]);
      };
      reader.readAsText(file);
    }
  };

  const handleTargetColumnChange = async (e) => {
    const newTargetColumn = e.target.value;
    setTargetColumn(newTargetColumn);

    if (file && newTargetColumn) {
      setLoading(true);
      setError('');

      const formData = new FormData();
      formData.append('file', file);
      formData.append('targetColumn', newTargetColumn);

      try {
        const response = await fetch('http://localhost:5000/api/discrete-features', {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();
        if (data.success) {
          setDiscreteFeatures(data.discrete_features);
        } else {
          setError(data.error || 'Failed to get discrete features list');
        }
      } catch (err) {
        setError('Unable to connect to server');
      } finally {
        setLoading(false);
      }
    }
  };

  const handleViewModeChange = (event, newMode) => {
    if (newMode !== null) {
      setViewMode(newMode);
      if (results) {
        handleAnalyze(); // Re-analyze to update view
      }
    }
  };

  const handleSortModeChange = (event, newMode) => {
    if (newMode !== null) {
      setSortMode(newMode);
      if (results) {
        handleAnalyze(); // Re-analyze to update view
      }
    }
  };

  const handleAnalyze = async () => {
    if (!file || !targetColumn) {
      setError('Please select a file and target variable column');
      return;
    }

    // Validate significance level
    const alpha = parseFloat(significanceLevel);
    if (isNaN(alpha) || alpha <= 0 || alpha >= 1) {
      setError('Significance level must be a number between 0 and 1');
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
        setError(data.error || 'Error occurred during analysis');
      }
    } catch (err) {
      setError('Unable to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryAnalyze = async () => {
    if (!file || !targetColumn || !selectedFeature) {
      setError('Please select a file, target variable column, and feature column');
      return;
    }

    // Validate significance level
    const alpha = parseFloat(significanceLevel);
    if (isNaN(alpha) || alpha <= 0 || alpha >= 1) {
      setError('Significance level must be a number between 0 and 1');
      return;
    }

    setLoading(true);
    setError('');
    setCategoryResults(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('targetColumn', targetColumn);
    formData.append('feature', selectedFeature);
    formData.append('significanceLevel', significanceLevel);

    try {
      const response = await fetch('http://localhost:5000/api/category-splits', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (data.success) {
        setCategoryResults(data.results);
      } else {
        setError(data.error || 'Error occurred during analysis');
      }
    } catch (err) {
      setError('Unable to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom align="center">
            Smart Segment
          </Typography>

          <Paper sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button
                variant="contained"
                component="label"
                startIcon={<CloudUploadIcon />}
              >
                Upload CSV file
                <input
                  type="file"
                  hidden
                  accept=".csv"
                  onChange={handleFileUpload}
                />
              </Button>

              {file && (
                <Typography variant="body2" color="text.secondary">
                  Selected file: {file.name}
                </Typography>
              )}

              {columns.length > 0 && (
                <FormControl fullWidth>
                  <InputLabel>Select target variable column</InputLabel>
                  <Select
                    value={targetColumn}
                    label="Select target variable column"
                    onChange={handleTargetColumnChange}
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
                label="Significance level (α)"
                type="number"
                value={significanceLevel}
                onChange={(e) => setSignificanceLevel(e.target.value)}
                inputProps={{ step: "0.01", min: "0.01", max: "0.99" }}
                helperText="Please enter a number between 0 and 1, e.g., 0.05"
                fullWidth
              />

              <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs value={activeTab} onChange={handleTabChange}>
                  <Tab label="General Analysis" />
                  <Tab label="Category Variable Analysis" />
                </Tabs>
              </Box>

              {activeTab === 0 ? (
                <>
                  <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                    <ToggleButtonGroup
                      value={viewMode}
                      exclusive
                      onChange={handleViewModeChange}
                      aria-label="View mode"
                    >
                      <ToggleButton value="best_per_feature" aria-label="Best split per feature">
                        Best split per feature
                      </ToggleButton>
                      <ToggleButton value="top_5_global" aria-label="Top 5 global best splits">
                        Top 5 global best splits
                      </ToggleButton>
                    </ToggleButtonGroup>
                  </Box>

                  <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                    <ToggleButtonGroup
                      value={sortMode}
                      exclusive
                      onChange={handleSortModeChange}
                      aria-label="Sort mode"
                    >
                      <ToggleButton value="impact" aria-label="Sort by effect size">
                        Sort by effect size
                      </ToggleButton>
                      <ToggleButton value="p_value" aria-label="Sort by p value">
                        Sort by p value
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
                    label="Show non-significant results"
                  />

                  <Button
                    variant="contained"
                    onClick={handleAnalyze}
                    disabled={loading || !file || !targetColumn}
                  >
                    {loading ? <CircularProgress size={24} /> : 'Analyze'}
                  </Button>
                </>
              ) : (
                <>
                  <FormControl fullWidth>
                    <InputLabel>Select category variable</InputLabel>
                    <Select
                      value={selectedFeature}
                      label="Select category variable"
                      onChange={(e) => setSelectedFeature(e.target.value)}
                    >
                      {discreteFeatures.map((feature) => (
                        <MenuItem key={feature} value={feature}>
                          {feature}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <Button
                    variant="contained"
                    onClick={handleCategoryAnalyze}
                    disabled={loading || !file || !targetColumn || !selectedFeature}
                  >
                    {loading ? <CircularProgress size={24} /> : 'Analyze category variable'}
                  </Button>
                </>
              )}
            </Box>
          </Paper>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {activeTab === 0 ? (
            results && <FeatureResults results={results} />
          ) : (
            categoryResults && <FeatureResults results={categoryResults} />
          )}

          <FeedbackForm />
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;