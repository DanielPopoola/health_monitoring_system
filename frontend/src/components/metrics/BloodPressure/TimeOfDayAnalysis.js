import React, { useState, useEffect } from 'react';
import { fetchBloodPressureTimeOfDayAnalysis } from '../../../services/metricsService';
import { 
  Paper, Typography, Box, CircularProgress,
  Grid, FormControl, InputLabel, Select, MenuItem,
  Table, TableContainer, TableHead, TableBody, TableRow, TableCell
} from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const TimeOfDayAnalysis = () => {
  const [loading, setLoading] = useState(true);
  const [analysisData, setAnalysisData] = useState(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    const fetchAnalysis = async () => {
      setLoading(true);
      try {
        const data = await fetchBloodPressureTimeOfDayAnalysis(days);
        setAnalysisData(data);
      } catch (error) {
        console.error('Error fetching time of day analysis:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAnalysis();
  }, [days]);

  const handleDaysChange = (event) => {
    setDays(event.target.value);
  };

  // Format data for the chart
  const prepareChartData = () => {
    if (!analysisData?.morning_averages || !analysisData?.evening_averages) return [];
    
    return [
      {
        name: 'Morning',
        systolic: Math.round(analysisData.morning_averages.avg_systolic || 0),
        diastolic: Math.round(analysisData.morning_averages.avg_diastolic || 0)
      },
      {
        name: 'Evening',
        systolic: Math.round(analysisData.evening_averages.avg_systolic || 0),
        diastolic: Math.round(analysisData.evening_averages.avg_diastolic || 0)
      }
    ];
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">Blood Pressure: Time of Day Analysis</Typography>
        <FormControl size="small" sx={{ width: 150 }}>
          <InputLabel>Analysis Period</InputLabel>
          <Select
            value={days}
            label="Analysis Period"
            onChange={handleDaysChange}
          >
            <MenuItem value={7}>Last Week</MenuItem>
            <MenuItem value={30}>Last Month</MenuItem>
            <MenuItem value={90}>Last 3 Months</MenuItem>
          </Select>
        </FormControl>
      </Box>
      
      {!analysisData ? (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', my: 3 }}>
          Not enough data available for analysis
        </Typography>
      ) : (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={prepareChartData()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis domain={[60, 160]} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="systolic" name="Systolic" fill="#e53935" />
                  <Bar dataKey="diastolic" name="Diastolic" fill="#3f51b5" />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Time of Day</TableCell>
                    <TableCell align="right">Avg. Systolic</TableCell>
                    <TableCell align="right">Avg. Diastolic</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell component="th" scope="row">Morning</TableCell>
                    <TableCell align="right">
                      {Math.round(analysisData.morning_averages.avg_systolic || 0)} mmHg
                    </TableCell>
                    <TableCell align="right">
                      {Math.round(analysisData.morning_averages.avg_diastolic || 0)} mmHg
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th" scope="row">Evening</TableCell>
                    <TableCell align="right">
                      {Math.round(analysisData.evening_averages.avg_systolic || 0)} mmHg
                    </TableCell>
                    <TableCell align="right">
                      {Math.round(analysisData.evening_averages.avg_diastolic || 0)} mmHg
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
            
            {analysisData.pattern && (
              <Box sx={{ mt: 3, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
                <Typography variant="subtitle1">
                  Pattern: {analysisData.pattern.type}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {analysisData.pattern.description}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Systolic difference: {analysisData.pattern.systolic_difference} mmHg
                </Typography>
              </Box>
            )}
          </Grid>
        </Grid>
      )}
    </Paper>
  );
};

export default TimeOfDayAnalysis;