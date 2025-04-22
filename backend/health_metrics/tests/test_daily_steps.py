import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestDailyStepsAPI:

    def test_create_daily_steps_authenticated(self, authenticated_client, daily_steps_data):
        """Test that authenticated user can create daily steps data"""
        url = reverse('dailysteps-list')
        response = authenticated_client.post(url, daily_steps_data, format='json')

        assert response.status_code ==  status.HTTP_201_CREATED
        assert response.data['count'] == daily_steps_data['count']
        assert 'goal_percentage' in response.data
        assert 'active_level' in response.data

    def test_get_daily_steps_data_list(self, authenticated_client, daily_steps_data):
        """Test getting list of daily steps"""
        # First create daily steps
        create_url = reverse('dailysteps-list')
        authenticated_client.post(create_url, daily_steps_data, format='json')

        # Get the list
        response = authenticated_client.get(create_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0