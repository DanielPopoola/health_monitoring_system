import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestSleepDurationAPI:

    def test_create_sleep_duration_authenticated(self, authenticated_client, sleep_duration_data):
        """Test that authenticated user can creat sleep_duration data"""
        # Create sleep session data
        url = reverse('sleepduration-list')
        response = authenticated_client.post(url, sleep_duration_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'duration' in response.data
        assert 'is_sufficient' in response.data

    def test_sufficiency_check(self, authenticated_client, sleep_duration_data):
        """Test the sufficiency_check custom action"""
        # First create sleep duration data
        create_url = reverse('sleepduration-list')
        authenticated_client.post(create_url, sleep_duration_data, format='json')

        # Test the custom action with the age parameter
        sufficiency_url = reverse('sleepduration-sufficiency-check')
        response = authenticated_client.get(f"{sufficiency_url}?age=35")
        
        assert response.status_code == status.HTTP_200_OK
        assert 'is_sufficient' in response.data
        assert 'recommended_range' in response.data