import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { getCurrentUser } from './services/authService';

// Layout components
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import { Box, Container } from '@mui/material';

// Pages
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import Dashboard from './components/dashboard/Dashboard';
import BloodPressurePage from './pages/BloodPressurePage';
import HeartRatePage from './pages/HeartRatePage';
import SpO2Page from './pages/SpO2Page';
import DailyStepsPage from './pages/DailyStepsPage';
import SleepDurationPage from './pages/SleepDurationPage';

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#f50057',
    },
  },
});

// Protected route component
const ProtectedRoute = ({ children }) => {
  const currentUser = getCurrentUser();
  return currentUser ? children : <Navigate to="/login" />;
};

function App() {
  const currentUser = getCurrentUser();
  
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        {currentUser ? (
          <Box sx={{ display: 'flex' }}>
            <Header />
            <Sidebar />
            <Box
              component="main"
              sx={{
                flexGrow: 1,
                height: '100vh',
                overflow: 'auto',
                pt: 10, // Adjust according to your header height
                px: 2
              }}
            >
              <Container maxWidth="lg">
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" />} />
                  <Route path="/dashboard" element={
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  } />
                  <Route path="/blood-pressure" element={
                    <ProtectedRoute>
                      <BloodPressurePage />
                    </ProtectedRoute>
                  } />
                  <Route path="/heart-rate" element={
                    <ProtectedRoute>
                      <HeartRatePage />
                    </ProtectedRoute>
                  } />
                  <Route path="/spo2" element={
                    <ProtectedRoute>
                      <SpO2Page />
                    </ProtectedRoute>
                  } />
                  <Route path="/daily-steps" element={
                    <ProtectedRoute>
                      <DailyStepsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/sleep-duration" element={
                    <ProtectedRoute>
                      <SleepDurationPage />
                    </ProtectedRoute>
                  } />
                  <Route path="*" element={<Navigate to="/dashboard" />} />
                </Routes>
              </Container>
            </Box>
          </Box>
        ) : (
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="*" element={<Navigate to="/login" />} />
          </Routes>
        )}
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;