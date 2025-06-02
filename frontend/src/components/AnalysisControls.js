import {
    Box,
    FormControl,
    FormControlLabel,
    InputLabel,
    MenuItem,
    Select,
    Switch,
    ToggleButton,
    ToggleButtonGroup,
} from '@mui/material';
import React from 'react';

export default function AnalysisControls({
  columns,
  targetColumn,
  onTargetColumnChange,
  viewMode,
  onViewModeChange,
  sortMode,
  onSortModeChange,
  significanceLevel,
  onSignificanceLevelChange,
  showNonSignificant,
  onShowNonSignificantChange,
}) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <FormControl fullWidth>
        <InputLabel>Target Variable</InputLabel>
        <Select
          value={targetColumn}
          label="Target Variable"
          onChange={onTargetColumnChange}
        >
          {columns.map((column) => (
            <MenuItem key={column} value={column}>
              {column}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl fullWidth>
        <InputLabel>Significance Level</InputLabel>
        <Select
          value={significanceLevel}
          label="Significance Level"
          onChange={onSignificanceLevelChange}
        >
          <MenuItem value="0.01">0.01 (99% confidence)</MenuItem>
          <MenuItem value="0.05">0.05 (95% confidence)</MenuItem>
          <MenuItem value="0.1">0.1 (90% confidence)</MenuItem>
        </Select>
      </FormControl>

      <ToggleButtonGroup
        value={viewMode}
        exclusive
        onChange={onViewModeChange}
        aria-label="view mode"
        fullWidth
      >
        <ToggleButton value="best_per_feature" aria-label="best per feature">
          Best Per Feature
        </ToggleButton>
        <ToggleButton value="all_splits" aria-label="all splits">
          All Splits
        </ToggleButton>
      </ToggleButtonGroup>

      <ToggleButtonGroup
        value={sortMode}
        exclusive
        onChange={onSortModeChange}
        aria-label="sort mode"
        fullWidth
      >
        <ToggleButton value="impact" aria-label="sort by impact">
          Sort by Impact
        </ToggleButton>
        <ToggleButton value="pvalue" aria-label="sort by p-value">
          Sort by P-value
        </ToggleButton>
      </ToggleButtonGroup>

      <FormControlLabel
        control={
          <Switch
            checked={showNonSignificant}
            onChange={(e) => onShowNonSignificantChange(e.target.checked)}
          />
        }
        label="Show Non-Significant Results"
      />
    </Box>
  );
}