import React, { useState, useEffect } from 'react';
import { getCurrentUser } from '../../services/authService';
import { fetchMetrics } from '../../services/metricsService';
import { 
  Grid, Typography, Paper, Box, 
  CircularProgress, Container 
} from '@mui/material';
import MetricSummary from './MetricSummary';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState({
    bloodPressure: null,
    heartRate: null,
    spO2: null,
    dailySteps: null,
    sleepDuration: null
  });
  const [user, setUser] = useState(null);

  useEffect(() => {
    const currentUser = getCurrentUser();
    if (currentUser) {
      setUser(currentUser);
    }
    
    const fetchAllMetrics = async () => {
      try {
        const [bp, hr, spo2, steps, sleep] = await Promise.all([
          fetchMetrics('blood-pressure'),
          fetchMetrics('heart-rate'),
          fetchMetrics('spo2'),
          fetchMetrics('daily-steps'),
          fetchMetrics('sleep-duration')
        ]);
        
        setMetrics({
          bloodPressure: bp,
          heartRate: hr,
          spO2: spo2,
          dailySteps: steps,
          sleepDuration: sleep
        });
      } catch (error) {
        console.error('Error fetching metrics:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAllMetrics();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Welcome, {user?.first_name || 'User'}
      </Typography>
      
      <Typography variant="h6" gutterBottom>
        Your Health Summary
      </Typography>
      
      <Grid container spacing={3}>
        {/* Blood Pressure Summary */}
        <Grid item xs={12} md={6} lg={4}>
          <MetricSummary 
            title="Blood Pressure" 
            data={metrics.bloodPressure?.results?.[0]} 
            type="bloodPressure"
          />
        </Grid>
        
        {/* Heart Rate Summary */}
        <Grid item xs={12} md={6} lg={4}>
          <MetricSummary 
            title="Heart Rate" 
            data={metrics.heartRate?.results?.[0]} 
            type="heartRate"
          />
        </Grid>
        
        {/* SpO2 Summary */}
        <Grid item xs={12} md={6} lg={4}>
          <MetricSummary 
            title="Blood Oxygen" 
            data={metrics.spO2?.results?.[0]} 
            type="spO2"
          />
        </Grid>
        
        {/* Daily Steps Summary */}
        <Grid item xs={12} md={6}>
          <MetricSummary 
            title="Daily Steps" 
            data={metrics.dailySteps?.results?.[0]} 
            type="dailySteps"
          />
        </Grid>
        
        {/* Sleep Duration Summary */}
        <Grid item xs={12} md={6}>
          <MetricSummary 
            title="Sleep Duration" 
            data={metrics.sleepDuration?.results?.[0]} 
            type="sleepDuration"
          />
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;