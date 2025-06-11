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
      <Button
        variant="contained"
        component="label"
        startIcon={<CloudUploadIcon />}
        sx={{ alignSelf: 'center' }}
      >
        Upload CSV File
        <input
          type="file"
          hidden
          accept=".csv"
          onChange={handleFileUpload}
        />
      </Button>
      {error && (
        <Typography color="error" align="center">
          {error}
        </Typography>
      )}
    </Box>
  );
}