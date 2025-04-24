import axios from "axios";
import { authHeader } from "./authService";

const API_URL = "http://localhost:8000/api/"

// General fetcher for health metrics
export const fetchMetrics = async (metricType, params = {}) => {
    try {
      const response = await axios.get(`${API_URL}${metricType}/`, {
        headers: authHeader(),
        params
      });
      return response.data;
    } catch (error) {
      throw error;
    }
};

// Specific API functions for custom endpoints
export const fetchBloodPressureTimeOfDayAnalysis = async (days = 30) => {
    try {
      const response = await axios.get(`${API_URL}blood-pressure/time_of_day_analysis/`, {
        headers: authHeader(),
        params: { days }
      });
      return response.data;
    } catch (error) {
      throw error;
    }
};

// Specific API functions for custom endpoints
export const fetchBloodPressureElevationCheck = async (days = 7) => {
    try {
      const response = await axios.get(`${API_URL}blood-pressure/elevation_check/`, {
        headers: authHeader(),
        params: { days }
      });
      return response.data;
    } catch (error) {
      throw error;
    }
};

export const fetchBloodPressureAgeComparison = async (age) => {
    try {
      const response = await axios.get(`${API_URL}blood-pressure/age_comparsion/`, {
        headers: authHeader(),
        params: { age }
      });
      return response.data;
    } catch (error) {
      throw error;
    }
};

export const fetchDailyStepsWeeklyAverage = async () => {
    try {
      const response = await axios.get(`${API_URL}daily-steps/weekly_average/`, {
        headers: authHeader()
      });
      return response.data;
    } catch (error) {
      throw error;
    }
};

export const fetchHeartRateRestingAverage = async () => {
    try {
      const response = await axios.get(`${API_URL}heart-rate/hrv/`, {
        headers: authHeader()
      });
      return response.data;
    } catch (error) {
      throw error;
    }
};

export const fetchHeartRateHRV = async (timeWindow = 24) => {
    try {
      const response = await axios.get(`${API_URL}heart-rate/hrv/`, {
        headers: authHeader(),
        params: { time_window: timeWindow }
      });
      return response.data;
    } catch (error) {
      throw error;
    }
};

export const fetchHeartRateBaselineComparison = async (baselineDays = 30, baselineActivity) => {
    try {
      const response = await axios.get(`${API_URL}heart-rate/baseline_comparison/`, {
        headers: authHeader(),
        params: {baseline_days: baselineDays, baseline_activity: baselineActivity}
      });
      return response.data;
    } catch (error) {
      throw error;
    }
};

export const fetchSleepDurationSufficienyCheck = async (age) => {
    try {
      const response = await axios.get(`${API_URL}sleep-duration/sufficiency_check/`, {
        headers: authHeader(),
        params: { age }
      });
      return response.data;
    } catch (error) {
      throw error;
    }
};

export const fetchSleepDurationWeeklyAverage = async (days = 7) => {
    try {
      const response = await axios.get(`${API_URL}sleep-duration/sufficiency_check/`, {
        headers: authHeader(),
        params: { days }
      });
      return response.data;
    } catch (error) {
      throw error;
    }
};

export const fetchSpO2LowestReading = async (days = 7) => {
    try {
      const response = await axios.get(`${API_URL}spo2/lowest_reading/`, {
        headers: authHeader(),
        params: { days }
      });
      return response.data;
    } catch (error) {
      throw error;
    }
};

export const fetchSpO2AlertCheck = async () => {
    try {
      const response = await axios.get(`${API_URL}spo2/alert_check/`, {
        headers: authHeader()
      });
      return response.data;
    } catch (error) {
      throw error;
    }
};