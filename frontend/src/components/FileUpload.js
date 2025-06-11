import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { Box, Button, Typography } from '@mui/material';
import React, { useRef } from 'react';

export default function FileUpload({ onFileSelect, error }) {
  const fileInputRef = useRef(null);

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

  const handleButtonClick = (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Typography align="center" color="text.secondary">
        Please upload a CSV file with column headers.
      </Typography>
      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
        <Button
          variant="contained"
          startIcon={<CloudUploadIcon />}
          onClick={handleButtonClick}
        >
          Upload CSV File
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          style={{ display: 'none' }}
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