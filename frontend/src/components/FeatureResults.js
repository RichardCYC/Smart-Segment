import InfoIcon from '@mui/icons-material/Info';
import {
    Box,
    Chip,
    Divider,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Tooltip,
    Typography
} from '@mui/material';
import React from 'react';
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, XAxis, YAxis } from 'recharts';

const FeatureResults = ({ results }) => {
  // 依 effect size 由大到小排序
  const sortedResults = [...results].sort((a, b) => b.effect_size - a.effect_size);
  const significantResults = sortedResults.filter(result => result.is_significant);
  const nonSignificantResults = sortedResults.filter(result => !result.is_significant);

  // Sort chartData by significance priority, matching the table order above
  const chartData = sortedResults.map(result => ({
    name: result.feature,
    rule: result.rule,
    groupA: result.group_a_rate,
    groupB: result.group_b_rate,
    group_a_count: typeof result.group_a_count === 'number' ? result.group_a_count : '-',
    group_b_count: typeof result.group_b_count === 'number' ? result.group_b_count : '-',
    isSignificant: result.is_significant,
  }));

  // Statistical test method descriptions
  const testMethodDescriptions = {
    "Welch's t-test": "Used for comparing means of two independent samples, does not assume equal variances",
    "Mann-Whitney U test (n < 30)": "Used for small samples (n<30) of two independent groups, does not assume normal distribution",
    "Mann-Whitney U test (group size < 30)": "Used when either group size is less than 30, does not assume normal distribution",
    "Mann-Whitney U test (skewed data)": "Used for severely skewed data distributions, does not assume normal distribution",
    "Mann-Whitney U test (low variability)": "Used when one or both groups have very low variability (almost identical values)",
    "Mann-Whitney U test (skew calculation failed)": "Used when skewness calculation fails, fallback to non-parametric test",
    "Chi-square test": "Used for testing independence of categorical variables, requires expected frequencies > 5",
    "Fisher's exact test (expected freq < 5)": "Used for testing independence when expected frequencies < 5",
    "Fisher's exact test (n < 30)": "Used for small samples (n<30) of categorical variables",
    "Fisher's exact test (small sample or expected freq < 5)": "Used for small samples or when expected frequencies < 5",
    "Two-proportion z-test": "Used to compare proportions or means between two groups when sample size is sufficient. Assumes independent samples.",
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        Feature Analysis Results
      </Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Feature Name</TableCell>
              <TableCell>Split Rule</TableCell>
              <TableCell>
                {results[0]?.target_type === 'binary' ? 'Group A (Y=True%)' : 'Group A (Y Mean)'}
              </TableCell>
              <TableCell>
                {results[0]?.target_type === 'binary' ? 'Group B (Y=True%)' : 'Group B (Y Mean)'}
              </TableCell>
              <TableCell>
                {results[0]?.target_type === 'binary' ? 'Effect Size (%)' : 'Effect Size'}
              </TableCell>
              <TableCell>P-value</TableCell>
              <TableCell>Significance</TableCell>
              <TableCell>Statistical Test</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {/* Significant results */}
            {significantResults.map((result) => (
              <TableRow
                key={`${result.feature}-${result.rule}`}
                sx={{ backgroundColor: 'rgba(76, 175, 80, 0.1)' }}
              >
                <TableCell>{result.feature}</TableCell>
                <TableCell>{result.rule}</TableCell>
                <TableCell>
                  {result.target_type === 'binary'
                    ? `${result.group_a_rate.toFixed(2)}%`
                    : result.group_a_rate.toFixed(2)}
                </TableCell>
                <TableCell>
                  {result.target_type === 'binary'
                    ? `${result.group_b_rate.toFixed(2)}%`
                    : result.group_b_rate.toFixed(2)}
                </TableCell>
                <TableCell>
                  {result.target_type === 'binary'
                    ? `${result.effect_size.toFixed(2)}%`
                    : result.effect_size.toFixed(2)}
                </TableCell>
                <TableCell>{result.p_value.toFixed(4)}</TableCell>
                <TableCell>
                  <Chip
                    label="Significant"
                    color="success"
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Typography variant="body2">
                      {result.test_method}
                    </Typography>
                    <Tooltip title={testMethodDescriptions[result.test_method] || "No description"}>
                      <InfoIcon
                        sx={{
                          fontSize: '1rem',
                          color: 'text.secondary',
                          opacity: 0.7,
                          '&:hover': {
                            opacity: 1
                          }
                        }}
                      />
                    </Tooltip>
                  </Box>
                </TableCell>
              </TableRow>
            ))}

            {/* Divider */}
            {significantResults.length > 0 && nonSignificantResults.length > 0 && (
              <TableRow>
                <TableCell colSpan={8}>
                  <Divider />
                </TableCell>
              </TableRow>
            )}

            {/* Non-significant results */}
            {nonSignificantResults.map((result) => (
              <TableRow
                key={`${result.feature}-${result.rule}`}
                sx={{ backgroundColor: 'rgba(255, 152, 0, 0.1)' }}
              >
                <TableCell>{result.feature}</TableCell>
                <TableCell>{result.rule}</TableCell>
                <TableCell>
                  {result.target_type === 'binary'
                    ? `${result.group_a_rate.toFixed(2)}%`
                    : result.group_a_rate.toFixed(2)}
                </TableCell>
                <TableCell>
                  {result.target_type === 'binary'
                    ? `${result.group_b_rate.toFixed(2)}%`
                    : result.group_b_rate.toFixed(2)}
                </TableCell>
                <TableCell>
                  {result.target_type === 'binary'
                    ? `${result.effect_size.toFixed(2)}%`
                    : result.effect_size.toFixed(2)}
                </TableCell>
                <TableCell>{result.p_value.toFixed(4)}</TableCell>
                <TableCell>
                  <Chip
                    label="Non-significant"
                    color="warning"
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Typography variant="body2">
                      {result.test_method}
                    </Typography>
                    <Tooltip title={testMethodDescriptions[result.test_method] || "No description"}>
                      <InfoIcon
                        sx={{
                          fontSize: '1rem',
                          color: 'text.secondary',
                          opacity: 0.7,
                          '&:hover': {
                            opacity: 1
                          }
                        }}
                      />
                    </Tooltip>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Paper sx={{ mt: 3, p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Feature Split Effect Comparison
        </Typography>
        <Box sx={{ height: 420 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="rule"
                tick={{ fontSize: 13, wordBreak: 'break-all', whiteSpace: 'pre-line' }}
                interval={0}
                angle={-10}
                textAnchor="end"
                height={70}
              />
              <YAxis />
              <Legend formatter={(value) => {
                if (value === 'groupA') return 'Group A (Greater than/Equal to split point)';
                if (value === 'groupB') return 'Group B (Less than/Not equal to split point)';
                return value;
              }} />
              <Bar
                dataKey="groupA"
                fill="#8884d8"
                name="groupA"
                fillOpacity={0.8}
                label={({ x, y, width, value, index }) => {
                  const count = chartData[index].group_a_count;
                  return (
                    <text
                      x={x + width / 2}
                      y={y - 8}
                      fill="#8884d8"
                      textAnchor="middle"
                      fontSize="12"
                    >
                      {results[0]?.target_type === 'binary'
                        ? `${value.toFixed(2)}% (n=${count})`
                        : `${value.toFixed(2)} (n=${count})`}
                    </text>
                  );
                }}
              />
              <Bar
                dataKey="groupB"
                fill="#82ca9d"
                name="groupB"
                fillOpacity={0.8}
                label={({ x, y, width, value, index }) => {
                  const count = chartData[index].group_b_count;
                  return (
                    <text
                      x={x + width / 2}
                      y={y - 24}
                      fill="#82ca9d"
                      textAnchor="middle"
                      fontSize="12"
                    >
                      {results[0]?.target_type === 'binary'
                        ? `${value.toFixed(2)}% (n=${count})`
                        : `${value.toFixed(2)} (n=${count})`}
                    </text>
                  );
                }}
              />
            </BarChart>
          </ResponsiveContainer>
        </Box>
      </Paper>
    </Box>
  );
};

export default FeatureResults;