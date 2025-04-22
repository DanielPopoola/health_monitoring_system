import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from datetime import timedelta


@pytest.mark.django_db
class TestSpO2API:

    def test_create_spo2_authenticated(self, authenticated_client, spo2_data):
        """Test that authenitcated user can creat spo2 data"""
        # Create an SpO2 reading
        url = reverse('spo2-list')
        response = authenticated_client.post(url, spo2_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['value'] == spo2_data['value']
        assert 'is_normal' in response.data
        assert 'severity' in response.data

    def test_lowest_reading(self, authenticated_client, user):
        """Test the lowest_reading custom action"""
        # Create multiple SpO2 readings
        url = reverse('spo2-list')

        # Create a normal readiing
        normal_reading = {
            "value": 98,
            "measurement_method": "WEARABLE",
            "timestamp": timezone.now().isoformat(),
            "source": "device"
        }
        authenticated_client.post(url, normal_reading, format='json')

        # Create a low reading
        low_reading = {
            "value": 94,
            "measurement_method": "WEARABLE",
            "timestamp": (timezone.now() - timedelta(days=1)).isoformat(),
            "source": "device"
        }
        authenticated_client.post(url, low_reading, format='json')

        # Test the custom action
        lowest_url = reverse('spo2-lowest-reading')
        response = authenticated_client.get(f"{lowest_url}?days=1")

        assert response.status_code == status.HTTP_200_OK
        assert 'lowest_oxygen_level' in response.data
        assert "94%" in response.data['lowest_oxygen_level']

