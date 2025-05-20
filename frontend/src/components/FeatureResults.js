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
    Typography,
} from '@mui/material';
import React from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const FeatureResults = ({ results }) => {
  // 將結果分為顯著和不顯著兩組
  const significantResults = results.filter(result => result.is_significant);
  const nonSignificantResults = results.filter(result => !result.is_significant);

  // 準備圖表數據
  const chartData = results.map(result => ({
    name: result.feature,
    groupA: result.group_a_rate,
    groupB: result.group_b_rate,
    isSignificant: result.is_significant,
  }));

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
              </TableRow>
            ))}

            {/* 分隔線 */}
            {significantResults.length > 0 && nonSignificantResults.length > 0 && (
              <TableRow>
                <TableCell colSpan={8}>
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
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Paper sx={{ mt: 3, p: 2 }}>
        <Typography variant="h6" gutterBottom>
          各特徵分割效果比較
        </Typography>
        <Box sx={{ height: 400 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar
                dataKey="groupA"
                fill="#8884d8"
                name="組別A (Y=True%)"
                fillOpacity={0.8}
              />
              <Bar
                dataKey="groupB"
                fill="#82ca9d"
                name="組別B (Y=True%)"
                fillOpacity={0.8}
              />
            </BarChart>
          </ResponsiveContainer>
        </Box>
      </Paper>
    </Box>
  );
};

export default FeatureResults;