import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { Box, Button, Typography } from '@mui/material';
import React from 'react';

export default function FileUpload({ onFileSelect, error }) {
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Check file type
      if (!file.name.toLowerCase().endsWith('.csv')) {
        onFileSelect(null, 'Only CSV files are allowed');
        return;
      }

      // Read CSV file header to get column names
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const text = e.target.result;
          const headers = text.split('\n')[0].split(',');
          onFileSelect(file, '', headers);
        } catch (err) {
          onFileSelect(null, 'Unable to read CSV file');
        }
      };
      reader.onerror = () => {
        onFileSelect(null, 'File reading error');
      };
      reader.readAsText(file);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Typography align="center" color="text.secondary">
        Please upload a CSV file with column headers.
      </Typography>
      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
        <label htmlFor="file-upload">
          <Button
            variant="contained"
            component="span"
            startIcon={<CloudUploadIcon />}
          >
            Upload CSV File
          </Button>
        </label>
        <input
          id="file-upload"
          type="file"
          hidden
          accept=".csv"
          onChange={handleFileUpload}
        />
      </Box>
      {error && (
        <Typography color="error" align="center">
          {error}
        </Typography>
      )}
    </Box>
  );
}