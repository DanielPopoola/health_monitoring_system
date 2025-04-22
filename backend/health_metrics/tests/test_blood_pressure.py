import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from datetime import timedelta


@pytest.mark.django_db
class TestBloodPressureAPI:

    def test_create_blood_pressure_unauthenticated(self, api_client, blood_pressure_data):
        """Test that unauthenticated user cannot create blood pressure data"""
        url = reverse('bloodpressure-list')
        response = api_client.post(url, blood_pressure_data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_blood_pressure_authenticated(self, authenticated_client, blood_pressure_data):
        """Test that authenticated user can create blood pressure data"""
        url = reverse('bloodpressure-list')
        response = authenticated_client.post(url, blood_pressure_data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['systolic'] == blood_pressure_data['systolic']
        assert response.data['diastolic'] == blood_pressure_data['diastolic']
        assert 'bp_category' in response.data
        assert 'pulse_pressure' in response.data
        assert 'mean_arterial_pressure' in response.data

    def test_get_blood_pressure_list(self, authenticated_client, blood_pressure_data):
        """Test getting list of blood pressure readings"""
        # First create a blood pressure reading
        create_url = reverse('bloodpressure-list')
        authenticated_client.post(create_url, blood_pressure_data, format='json')

        # Get the list
        response = authenticated_client.get(create_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    def test_time_of_day_analysis(self, authenticated_client, user):
        """Test the time_of_day_analysis custom action"""
        # Create morning and evening blood pressure readings
        url = reverse('bloodpressure-list')

        # Create a morning reading
        morning_data = {
            "systolic": 125,
            "diastolic": 82,
            "pulse": 70,
            "timestamp":(timezone.now() - timedelta(days=1)).replace(hour=8).isoformat(),
            "source": "manual"
        }

        authenticated_client.post(url, morning_data, format='json')

        # Create evening reading
        evening_data = {
            "systolic": 135,
            "diastolic": 85,
            "pulse": 75,
            "timestamp": (timezone.now() - timedelta(days=1)).replace(hour=20).isoformat(),
            "source": "manual"
        }

        authenticated_client.post(url, evening_data, format='json')

        # Test the custom action
        analysis_url = reverse('bloodpressure-time-of-day-analysis')
        response = authenticated_client.get(analysis_url)

        assert response.status_code == status.HTTP_200_OK
        assert 'morning_averages' in response.data
        assert 'evening_averages' in response.data

    def test_elevation_check(self, authenticated_client, user):
        """Test the elevation_check custom action"""
        # Create elevated blood pressure readings
        url = reverse('bloodpressure-list')

        # Create multiple elevated readings
        for i in range(5):
            elevated_reading = {
                "systolic": 140 + i,
                "diastolic": 90 + i,
                "pulse": 75,
                "timestamp": (timezone.now() - timedelta(days=i)).isoformat(),
                "source":"manual"
            }

            authenticated_client.post(url, elevated_reading, format='json')

        # Test the custom action
        elevation_url = reverse('bloodpressure-elevation-check')
        response = authenticated_client.get(elevation_url)

        assert response.status_code == status.HTTP_200_OK
        assert 'is_consistently_elevated' in response.data
        assert response.data['is_consistently_elevated'] is True

    def test_age_comparison(self, authenticated_client, blood_pressure_data):
        """Test the elevation_check custom action"""
        # Create a blood pressure reading
        create_url = reverse('bloodpressure-list')
        authenticated_client.post(create_url, blood_pressure_data, format='json')

        # Test the custom action with the age parameter
        age_url = reverse('bloodpressure-age-comparison')
        response = authenticated_client.get(f"{age_url}?age=45")

        assert response.status_code == status.HTTP_200_OK
        assert 'latest_reading' in response.data
        assert 'age_specific_assessment' in response.data
        assert 'recommendation' in response.data