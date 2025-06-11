import Layout from '@/components/Layout';
import SEO from '@/components/SEO';
import { Alert, Box, Button, CircularProgress, Container, Paper, Typography } from '@mui/material';
import { useState } from 'react';
import AnalysisControls from '../components/AnalysisControls';
import FeatureResults from '../components/FeatureResults';
import FeedbackForm from '../components/FeedbackForm';
import FileUpload from '../components/FileUpload';

export default function Home() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
  const SHOW_CATEGORY_ANALYSIS = process.env.NEXT_PUBLIC_SHOW_CATEGORY_ANALYSIS === 'true';
  const GA_ID = process.env.NEXT_PUBLIC_GA_ID;

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

  const handleFileSelect = (file, error, headers) => {
    setFile(file);
    setError(error);
    if (headers) {
      setColumns(headers);
    }
  };

  const handleTargetColumnChange = (e) => {
    setTargetColumn(e.target.value);
  };

  const handleViewModeChange = (event, newMode) => {
    if (newMode !== null) {
      setViewMode(newMode);
      if (results) {
        handleAnalyze();
      }
    }
  };

  const handleSortModeChange = (event, newMode) => {
    if (newMode !== null) {
      setSortMode(newMode);
      if (results) {
        handleAnalyze();
      }
    }
  };

  const handleAnalyze = async () => {
    if (!file || !targetColumn) {
      setError('Please select a file and target variable column');
      return;
    }

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
      const response = await fetch(`${API_URL}/api/analyze`, {
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

  return (
    <Layout>
      <SEO
        title="Smart Segment - AI-Powered Customer Segmentation Tool"
        description="Transform your customer data into actionable insights with Smart Segment's AI-powered segmentation tool. Get started for free today."
        canonical="/"
      />
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom align="center">
            Smart Segment
          </Typography>
          <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 3 }}>
            Smart Segment helps you analyze your CSV data and generate actionable insights and feature importance rankings.<br /><br />
            <b>Step 1:</b> Please upload your CSV file to get started.
          </Typography>

          <Paper sx={{ p: 3, mb: 3, boxShadow: 6, border: '1.5px solid #e0e0e0' }}>
            <FileUpload onFileSelect={handleFileSelect} error={error} />
            {file && (
              <Typography align="center" color="primary" sx={{ mt: 2 }}>
                Uploaded file: {file.name}
              </Typography>
            )}
          </Paper>

          {columns.length > 0 && (
            <Paper sx={{ p: 3, mb: 3, boxShadow: 6, border: '1.5px solid #e0e0e0' }}>
              <AnalysisControls
                columns={columns}
                targetColumn={targetColumn}
                onTargetColumnChange={handleTargetColumnChange}
                viewMode={viewMode}
                onViewModeChange={handleViewModeChange}
                sortMode={sortMode}
                onSortModeChange={handleSortModeChange}
                significanceLevel={significanceLevel}
                onSignificanceLevelChange={(e) => setSignificanceLevel(e.target.value)}
                showNonSignificant={showNonSignificant}
                onShowNonSignificantChange={setShowNonSignificant}
              />
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
                <Button
                  variant="contained"
                  onClick={handleAnalyze}
                  disabled={loading || !file || !targetColumn}
                >
                  Analyze
                </Button>
              </Box>
            </Paper>
          )}

          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
              <CircularProgress />
            </Box>
          )}

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {results && (
            <FeatureResults
              results={results}
              viewMode={viewMode}
              sortMode={sortMode}
              showNonSignificant={showNonSignificant}
            />
          )}

          <FeedbackForm />
        </Box>
      </Container>
    </Layout>
  );
}