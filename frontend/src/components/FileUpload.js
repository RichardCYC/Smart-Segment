import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { Box, Button, Typography } from '@mui/material';
import React, { useEffect } from 'react';

export default function FileUpload({ onFileSelect, error }) {
  useEffect(() => {
    console.log('FileUpload component mounted');
  }, []);

  const handleFileUpload = (event) => {
    console.log('handleFileUpload triggered');
    console.log('event:', event);
    console.log('event.target:', event.target);
    console.log('event.target.files:', event.target.files);

    const file = event.target.files[0];
    if (file) {
      console.log('File selected:', {
        name: file.name,
        type: file.type,
        size: file.size
      });

      // Check file type
      if (!file.name.toLowerCase().endsWith('.csv')) {
        console.log('Invalid file type');
        onFileSelect(null, 'Only CSV files are allowed');
        return;
      }

      // Read CSV file header to get column names
      const reader = new FileReader();
      reader.onload = (e) => {
        console.log('FileReader onload triggered');
        try {
          const text = e.target.result;
          console.log('File content first line:', text.split('\n')[0]);
          const headers = text.split('\n')[0].split(',');
          console.log('Parsed headers:', headers);
          onFileSelect(file, '', headers);
        } catch (err) {
          console.error('Error in onload:', err);
          onFileSelect(null, 'Unable to read CSV file');
        }
      };
      reader.onerror = (err) => {
        console.error('FileReader error:', err);
        onFileSelect(null, 'File reading error');
      };
      console.log('Starting to read file');
      reader.readAsText(file);
    } else {
      console.log('No file selected');
    }
  };

  const handleButtonClick = () => {
    console.log('Button clicked');
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Typography align="center" color="text.secondary">
        Please upload a CSV file with column headers.
      </Typography>
      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
        <label htmlFor="file-upload" onClick={() => console.log('Label clicked')}>
          <Button
            variant="contained"
            component="span"
            startIcon={<CloudUploadIcon />}
            onClick={handleButtonClick}
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
          onClick={() => console.log('Input clicked')}
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