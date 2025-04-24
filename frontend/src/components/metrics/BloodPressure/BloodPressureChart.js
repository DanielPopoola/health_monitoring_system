import React, { useState, useEffect } from 'react';
import { fetchMetrics } from '../../../services/metricsService';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Paper, Typography, Box, CircularProgress, FormControl, InputLabel, Select, MenuItem } from '@mui/material';

const BloodPressureChart = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState([]);
  const [timeRange, setTimeRange] = useState('week');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Calculate date range based on selected time range
        const now = new Date();
        let startDate;
        
        switch (timeRange) {
          case 'day':
            startDate = new Date(now.setHours(0, 0, 0, 0));
            break;
          case 'week':
            startDate = new Date(now.setDate(now.getDate() - 7));
            break;
          case 'month':
            startDate = new Date(now.setMonth(now.getMonth() - 1));
            break;
          default:
            startDate = new Date(now.setDate(now.getDate() - 7));
        }
        
        // Format dates for API request
        const params = {
          timestamp_after: startDate.toISOString(),
          timestamp_before: new Date().toISOString(),
          ordering: 'timestamp'
        };
        
        const response = await fetchMetrics('blood-pressure', params);
        
        // Format data for chart
        const formattedData = response.results.map(item => ({
          timestamp: new Date(item.timestamp).toLocaleString(),
          systolic: item.systolic,
          diastolic: item.diastolic,
          category: item.bp_category
        }));
        
        setData(formattedData);
      } catch (error) {
        console.error('Error fetching blood pressure data:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [timeRange]);

  const handleTimeRangeChange = (event) => {
    setTimeRange(event.target.value);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Paper sx={{ p: 3, height: '400px' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">Blood Pressure Trend</Typography>
        <FormControl size="small" sx={{ width: 120 }}>
          <InputLabel>Time Range</InputLabel>
          <Select
            value={timeRange}
            label="Time Range"
            onChange={handleTimeRangeChange}
          >
            <MenuItem value="day">Day</MenuItem>
            <MenuItem value="week">Week</MenuItem>
            <MenuItem value="month">Month</MenuItem>
          </Select>
        </FormControl>
      </Box>
      
      {data.length === 0 ? (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mt: 10 }}>
          No blood pressure data available for this time range
        </Typography>
      ) : (
        <ResponsiveContainer width="100%" height="85%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="timestamp" 
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => {
                const date = new Date(value);
                return timeRange === 'day' 
                  ? date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                  : date.toLocaleDateString([], { month: 'short', day: 'numeric' });
              }}
            />
            <YAxis domain={[50, 180]} />
            <Tooltip 
              labelFormatter={(value) => `Time: ${value}`}
              formatter={(value, name) => [
                `${value} mmHg`, 
                name === 'systolic' ? 'Systolic' : 'Diastolic'
              ]}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="systolic" 
              stroke="#e53935" 
              activeDot={{ r: 8 }} 
              strokeWidth={2}
            />
            <Line 
              type="monotone" 
              dataKey="diastolic" 
              stroke="#3f51b5" 
              strokeWidth={2}
            />
            {/* Reference lines for normal ranges */}
            <Line 
              type="monotone" 
              dataKey={() => 120} 
              stroke="#e53935" 
              strokeDasharray="5 5" 
              strokeWidth={1}
              dot={false}
            />
            <Line 
              type="monotone" 
              dataKey={() => 80} 
              stroke="#3f51b5" 
              strokeDasharray="5 5" 
              strokeWidth={1}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </Paper>
  );
};

export default BloodPressureChart;