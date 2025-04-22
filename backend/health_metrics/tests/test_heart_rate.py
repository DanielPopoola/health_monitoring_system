import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from datetime import timedelta


@pytest.mark.django_db
class TestHeartRateAPI:

    def test_create_heart_rate_authenticated(self, authenticated_client, heart_rate_data):
        """Test that authenitcated user can create heart rated data"""
        url = reverse('heartrate-list')
        response = authenticated_client.post(url, heart_rate_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['value'] == heart_rate_data['value']
        assert response.data['activity_level'] == heart_rate_data['activity_level']
        assert 'heart_rate_zone' in response.data
        assert 'is_tachycardia' in response.data
        assert 'is_bradycardia' in response.data

    def test_hrv_endpoint(self, authenticated_client, user):
        """Test the hrv custom action"""
        # Create multiple heart rate readings
        url = reverse('heartrate-list')

        for i in range(5):
            heart_rate = {
                "value": 65 + i * 5, 
                "activity_level": "active",
                "timestamp": (timezone.now() - timedelta(hours=i)).isoformat(),
                "source": "device"
            }
            authenticated_client.post(url, heart_rate, format='json')
            
        # Test the custom action
        hrv_url = reverse('heartrate-hrv')
        response = authenticated_client.get(f"{hrv_url}?time_window=5")

        assert response.status_code == status.HTTP_200_OK
        assert 'hrv' in response.data

    def test_baseline_comparison_endpoint(self, authenticated_client, user):
        """Test the baseline_comparison custom action"""
        # Create multiple heart rate readings
        url = reverse('heartrate-list')

        for i in range(5):
            heart_rate = {
                "value": 65 + i * 5, 
                "activity_level": "active",
                "timestamp": (timezone.now() - timedelta(hours=i)).isoformat(),
                "source": "device"
            }
            authenticated_client.post(url, heart_rate, format='json')

        # Test the custom action
        baseline_url = reverse('heartrate-baseline-comparison')
        response = authenticated_client.get(f"{baseline_url}?baseline_days=30")

        assert response.status_code == status.HTTP_200_OK
        assert 'baseline' in response.data
        assert 'is_elevated' in response.data
        assert 'percent_change' in response.data