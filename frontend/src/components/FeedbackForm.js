import FeedbackIcon from '@mui/icons-material/Feedback';
import {
  Box,
  Button,
} from '@mui/material';
import React from 'react';

const FeedbackForm = () => {
  const handleClick = () => {
    window.open('https://docs.google.com/forms/d/e/1FAIpQLSeo6DMd2b9lwzF6kUBCAE0Dg_8hNMkP57mI61vzm05I2rTOqA/viewform', '_blank');
  };

  return (
    <Box
      sx={{
        position: 'fixed',
        bottom: 20,
        right: 20,
        zIndex: 1000,
      }}
    >
      <Button
        variant="contained"
        color="primary"
        onClick={handleClick}
        startIcon={<FeedbackIcon />}
        sx={{
          borderRadius: '50px',
          padding: '8px 20px',
          boxShadow: 3,
          '&:hover': {
            transform: 'scale(1.05)',
            transition: 'transform 0.2s',
          },
        }}
      >
        Tell Us What You Think!
      </Button>
    </Box>
  );
};

export default FeedbackForm;