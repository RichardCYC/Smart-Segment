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
  // 將結果分為顯著和不顯著兩組
  const significantResults = results.filter(result => result.is_significant);
  const nonSignificantResults = results.filter(result => !result.is_significant);

  // 依照顯著性優先排序 chartData，順序與上方表格一致
  const sortedResults = [
    ...results.filter(r => r.is_significant),
    ...results.filter(r => !r.is_significant)
  ];
  const chartData = sortedResults.map(result => ({
    name: result.feature,
    rule: result.rule,
    groupA: result.group_a_rate,
    groupB: result.group_b_rate,
    group_a_count: typeof result.group_a_count === 'number' ? result.group_a_count : '-',
    group_b_count: typeof result.group_b_count === 'number' ? result.group_b_count : '-',
    isSignificant: result.is_significant,
  }));

  // 統計檢定方法的說明
  const testMethodDescriptions = {
    "Welch's t-test": "適用於兩組獨立樣本的平均值比較，不假設兩組變異數相等",
    "Mann-Whitney U test (n < 30)": "適用於小樣本(n<30)的兩組獨立樣本比較，不假設常態分配",
    "Mann-Whitney U test (group size < 30)": "適用於任一組樣本數小於30的情況，不假設常態分配",
    "Mann-Whitney U test (skewed data)": "適用於資料分布嚴重偏斜的情況，不假設常態分配",
    "Chi-square test": "適用於類別變數的獨立性檢定，要求期望頻數大於5",
    "Fisher's exact test (expected freq < 5)": "適用於期望頻數小於5的類別變數獨立性檢定",
    "Fisher's exact test (n < 30)": "適用於小樣本(n<30)的類別變數獨立性檢定"
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        特徵分析結果
      </Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>特徵名稱</TableCell>
              <TableCell>特徵類型</TableCell>
              <TableCell>分割規則</TableCell>
              <TableCell>組別A (Y=True%)</TableCell>
              <TableCell>組別B (Y=True%)</TableCell>
              <TableCell>效應大小</TableCell>
              <TableCell>P值</TableCell>
              <TableCell>顯著性</TableCell>
              <TableCell>統計檢定方法</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {/* 顯著結果 */}
            {significantResults.map((result) => (
              <TableRow
                key={`${result.feature}-${result.rule}`}
                sx={{ backgroundColor: 'rgba(76, 175, 80, 0.1)' }}
              >
                <TableCell>{result.feature}</TableCell>
                <TableCell>{result.feature_type === 'continuous' ? '連續型' : '離散型'}</TableCell>
                <TableCell>{result.rule}</TableCell>
                <TableCell>{result.group_a_rate.toFixed(2)}%</TableCell>
                <TableCell>{result.group_b_rate.toFixed(2)}%</TableCell>
                <TableCell>{result.effect_size.toFixed(2)}%</TableCell>
                <TableCell>{result.p_value.toFixed(4)}</TableCell>
                <TableCell>
                  <Chip
                    label="顯著"
                    color="success"
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Typography variant="body2">
                      {result.test_method}
                    </Typography>
                    <Tooltip title={testMethodDescriptions[result.test_method] || "無說明"}>
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

            {/* 分隔線 */}
            {significantResults.length > 0 && nonSignificantResults.length > 0 && (
              <TableRow>
                <TableCell colSpan={9}>
                  <Divider />
                </TableCell>
              </TableRow>
            )}

            {/* 不顯著結果 */}
            {nonSignificantResults.map((result) => (
              <TableRow
                key={`${result.feature}-${result.rule}`}
                sx={{ backgroundColor: 'rgba(255, 152, 0, 0.1)' }}
              >
                <TableCell>{result.feature}</TableCell>
                <TableCell>{result.feature_type === 'continuous' ? '連續型' : '離散型'}</TableCell>
                <TableCell>{result.rule}</TableCell>
                <TableCell>{result.group_a_rate.toFixed(2)}%</TableCell>
                <TableCell>{result.group_b_rate.toFixed(2)}%</TableCell>
                <TableCell>{result.effect_size.toFixed(2)}%</TableCell>
                <TableCell>{result.p_value.toFixed(4)}</TableCell>
                <TableCell>
                  <Chip
                    label="不顯著"
                    color="warning"
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Typography variant="body2">
                      {result.test_method}
                    </Typography>
                    <Tooltip title={testMethodDescriptions[result.test_method] || "無說明"}>
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
          各特徵分割效果比較
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
                if (value === 'groupA') return '組別A（大於分割點/等於）';
                if (value === 'groupB') return '組別B（小於等於分割點/不等於）';
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
                      {`${value.toFixed(2)}% (n=${count})`}
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
                      {`${value.toFixed(2)}% (n=${count})`}
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